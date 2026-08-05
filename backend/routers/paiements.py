from datetime import date as date_type
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, cast, String as SqlString, func
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/paiements", tags=["Paiements"], dependencies=[Depends(get_current_user)])

def _mettre_a_jour_statut(echeance: models.Echeances):
    if echeance.montant_paye <= 0:
        echeance.statut = "EN_ATTENTE"
    elif echeance.montant_paye >= echeance.montant_du:
        echeance.statut = "SOLDE"
    else:
        echeance.statut = "PARTIEL"


def _generer_numero_recu(db, date_paiement) -> str:
    """Numéro de reçu séquentiel par année : REC-<année>-<compteur>."""
    annee = date_paiement.year
    compteur = (
        db.query(func.count(models.Paiements.id))
        .filter(func.extract("year", models.Paiements.date) == annee)
        .scalar()
        or 0
    )
    return f"REC-{annee}-{compteur + 1:04d}"


def _distribuer_paiement(db, inscription, montant_verse, date_paiement, mode, numero_recu, observation) -> dict:
    """Distribue le montant versé + le crédit disponible sur les échéances impayées.
    Le surplus éventuel est conservé comme crédit pour un paiement futur."""
    reste = montant_verse + (inscription.credit_disponible or 0.0)
    inscription.credit_disponible = 0.0

    echeances_impayees = (
        db.query(models.Echeances)
        .filter(models.Echeances.id_inscription == inscription.id, models.Echeances.statut.in_(["EN_ATTENTE", "PARTIEL"]))
        .order_by(models.Echeances.date_echeance.asc())
        .all()
    )

    paiements_crees, echeances_maj = [], []

    for ech in echeances_impayees:
        if reste <= 0:
            break
        a_payer = ech.reste_a_payer
        if a_payer <= 0:
            continue  # échéance déjà soldée en mémoire : pas de paiement à 0
        montant_sur_ech = min(reste, a_payer)

        paiement = models.Paiements(
            id_inscription=inscription.id, id_echeance=ech.id, date=date_paiement,
            montant=montant_sur_ech, mode=mode, numero_recu=numero_recu, observation=observation,
        )
        db.add(paiement)
        ech.montant_paye += montant_sur_ech
        _mettre_a_jour_statut(ech)

        reste -= montant_sur_ech
        paiements_crees.append(paiement)
        echeances_maj.append(ech)

    # Surplus après avoir soldé toutes les échéances connues -> crédit pour la suite
    if reste > 0:
        inscription.credit_disponible = reste

    db.flush()

    # Les échéances encore dues sont exactement celles qu'on vient de charger
    # (montant_paye mis à jour en mémoire) : pas besoin d'une 2e requête.
    reste_global = sum(e.reste_a_payer for e in echeances_impayees)

    return {"paiements_crees": paiements_crees, "echeances_mises_a_jour": echeances_maj, "reste_global": reste_global}


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "comptable"))])
def enregistrer_paiement(payload: schemas.PaiementEcheanceCreate, db: Session = Depends(get_db)):
    inscription = db.query(models.Inscriptions).filter(models.Inscriptions.id == payload.id_inscription).first()
    if not inscription:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    if inscription.annee_scolaire and inscription.annee_scolaire.cloturee:
        raise HTTPException(status_code=409, detail="Cette année scolaire est clôturée.")

    numero_recu = (payload.numero_recu or "").strip() or _generer_numero_recu(db, payload.date)
    result = _distribuer_paiement(db, inscription, payload.montant, payload.date, payload.mode, numero_recu, payload.observation)
    db.commit()

    for p in result["paiements_crees"]:
        db.refresh(p)
    for e in result["echeances_mises_a_jour"]:
        db.refresh(e)
    db.refresh(inscription)

    return {
        "nb_paiements_crees": len(result["paiements_crees"]),
        "numero_recu": numero_recu,
        "echeances_mises_a_jour": [schemas.EcheanceResponse.model_validate(e) for e in result["echeances_mises_a_jour"]],
        "reste_global": result["reste_global"],
        "credit_disponible": inscription.credit_disponible,
    }


def _appliquer_filtres_paiements(query, id_inscription, matricule_eleve, date_debut, date_fin, q):
    if id_inscription:
        query = query.filter(models.Paiements.id_inscription == id_inscription)
    if matricule_eleve:
        query = query.join(models.Inscriptions).filter(models.Inscriptions.matricule_eleve == matricule_eleve)
    if date_debut:
        query = query.filter(models.Paiements.date >= date_debut)
    if date_fin:
        query = query.filter(models.Paiements.date <= date_fin)
    if q:
        like = f"%{q}%"
        query = query.join(models.Inscriptions)
        query = query.filter(or_(
            models.Paiements.code_paiement.ilike(like),
            models.Paiements.numero_recu.ilike(like),
            models.Paiements.observation.ilike(like),
            models.Paiements.mode.ilike(like),
            models.Inscriptions.matricule_eleve.ilike(like),
            cast(models.Inscriptions.id_classe, SqlString).ilike(like),
        ))
    return query


@router.get("/", response_model=List[schemas.PaiementResponse], dependencies=[Depends(require_role("admin", "comptable"))])
def lister_paiements(
    id_inscription: Optional[int] = None,
    matricule_eleve: Optional[str] = None,
    date_debut: Optional[date_type] = None,
    date_fin: Optional[date_type] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_paiements(
        db.query(models.Paiements).options(
            joinedload(models.Paiements.inscription).joinedload(models.Inscriptions.eleve)
        ),
        id_inscription, matricule_eleve, date_debut, date_fin, q
    )
    results = query.order_by(models.Paiements.date.desc()).offset(skip).limit(limit).all()
    for p in results:
        if p.inscription and p.inscription.eleve:
            p.matricule_eleve = p.inscription.eleve.matricule
            p.eleve_nom = p.inscription.eleve.nom
            p.eleve_prenom = p.inscription.eleve.prenom
    return results


@router.get("/compte", dependencies=[Depends(require_role("admin", "comptable"))])
def compter_paiements(
    id_inscription: Optional[int] = None,
    matricule_eleve: Optional[str] = None,
    date_debut: Optional[date_type] = None,
    date_fin: Optional[date_type] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_paiements(
        db.query(models.Paiements), id_inscription, matricule_eleve, date_debut, date_fin, q
    )
    return {"total": query.count()}


@router.get("/relances", response_model=List[schemas.RelanceResponse], dependencies=[Depends(require_role("admin", "comptable"))])
def get_echeances_en_retard(db: Session = Depends(get_db)):
    """Échéances impayées dont la date est dépassée — base pour les relances
    (email/SMS à brancher séparément). Chaque relance embarque l'élève, sa
    classe et le contact de son tuteur."""
    aujourdhui = date_type.today()
    echeances = (
        db.query(models.Echeances)
        .options(
            joinedload(models.Echeances.inscription).joinedload(models.Inscriptions.eleve).joinedload(models.Eleves.tuteur),
            joinedload(models.Echeances.inscription).joinedload(models.Inscriptions.classe),
        )
        .filter(models.Echeances.statut.in_(["EN_ATTENTE", "PARTIEL"]), models.Echeances.date_echeance < aujourdhui)
        .order_by(models.Echeances.date_echeance.asc())
        .all()
    )

    resultats = []
    for e in echeances:
        inscription = e.inscription
        eleve = inscription.eleve if inscription else None
        tuteur = eleve.tuteur if eleve else None
        classe = inscription.classe if inscription else None
        resultats.append(
            schemas.RelanceResponse(
                **schemas.EcheanceResponse.model_validate(e).model_dump(),
                matricule_eleve=inscription.matricule_eleve if inscription else None,
                eleve_nom=eleve.nom if eleve else None,
                eleve_prenom=eleve.prenom if eleve else None,
                classe_nom=classe.nom if classe else None,
                niveau_classe=classe.niveau if classe else None,
                code_tuteur=tuteur.code_tuteur if tuteur else None,
                tuteur_nom=tuteur.nom if tuteur else None,
                tuteur_prenom=tuteur.prenom if tuteur else None,
                telephone_tuteur=tuteur.telephone if tuteur else None,
                email_tuteur=tuteur.email if tuteur else None,
            )
        )
    return resultats


@router.get("/{paiement_id}", response_model=schemas.PaiementResponse, dependencies=[Depends(require_role("admin", "comptable"))])
def get_paiement(paiement_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Paiements).filter(models.Paiements.id == paiement_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    return p


@router.delete("/{paiement_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def supprimer_paiement(paiement_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Paiements).filter(models.Paiements.id == paiement_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    if p.id_echeance:
        ech = db.query(models.Echeances).filter(models.Echeances.id == p.id_echeance).first()
        if ech:
            ech.montant_paye = max(ech.montant_paye - p.montant, 0.0)
            _mettre_a_jour_statut(ech)
    db.delete(p)
    db.commit()
    return None


@router.get("/echeances/{id_inscription}", response_model=List[schemas.EcheanceResponse], dependencies=[Depends(require_role("admin", "comptable"))])
def get_echeances(id_inscription: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Echeances)
        .filter(models.Echeances.id_inscription == id_inscription)
        .order_by(models.Echeances.date_echeance.asc())
        .all()
    )
