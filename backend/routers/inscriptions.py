from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from datetime import date as date_type
from database import get_db
import models
import schemas
from models.echeances import MOIS_ANNEE_SCOLAIRE
from security import get_current_user, require_role

router = APIRouter(prefix="/api/inscriptions", tags=["Inscriptions"], dependencies=[Depends(get_current_user)])

def _verifier_existence(db, matricule_eleve, id_annee_scolaire, id_classe):
    if not db.query(models.Eleves).filter(models.Eleves.matricule == matricule_eleve).first():
        raise HTTPException(status_code=404, detail="Élève introuvable.")
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == id_annee_scolaire).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable.")
    if annee.cloturee:
        raise HTTPException(status_code=409, detail="Cette année scolaire est clôturée.")
    if id_classe and not db.query(models.Classes).filter(models.Classes.id == id_classe).first():
        raise HTTPException(status_code=404, detail="Classe introuvable.")


def _synchroniser_classe_eleve(db, matricule_eleve, statut, id_classe):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule_eleve).first()
    if not eleve:
        return
    eleve.classe_id = id_classe if statut in ("Inscrit", "Redoublant") else None


def _generer_echeances(db: Session, inscription: models.Inscriptions):
    classe = db.query(models.Classes).filter(models.Classes.id == inscription.id_classe).first()
    frais_inscription = getattr(classe, "frais_inscription", 0.0) or 0.0
    mensualite = getattr(classe, "mensualite", 0.0) or 0.0

    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == inscription.id_annee_scolaire).first()
    annee_debut = annee.date_debut.year if annee else inscription.date_inscription.year

    db.add(models.Echeances(
        id_inscription=inscription.id, id_classe=inscription.id_classe,
        type_echeance="INSCRIPTION", mois=None, date_echeance=inscription.date_inscription,
        montant_du=frais_inscription, montant_paye=0.0,
        statut="EN_ATTENTE" if frais_inscription > 0 else "SOLDE",
    ))

    nb_mensualites = 0
    for i, mois in enumerate(MOIS_ANNEE_SCOLAIRE):
        if i < 3:
            annee_mois, num_mois = annee_debut, 10 + i
        else:
            annee_mois, num_mois = annee_debut + 1, i - 2
        date_echeance = date_type(annee_mois, num_mois, 5)
        # Prorata : pas d'échéance pour un mois antérieur à la date d'inscription
        # (un élève inscrit en cours d'année n'est pas facturé pour les mois passés).
        if date_echeance < inscription.date_inscription:
            continue
        nb_mensualites += 1
        db.add(models.Echeances(
            id_inscription=inscription.id, id_classe=inscription.id_classe,
            type_echeance="MENSUALITE", mois=mois, date_echeance=date_echeance,
            montant_du=mensualite, montant_paye=0.0,
            statut="EN_ATTENTE" if mensualite > 0 else "SOLDE",
        ))

    inscription.montant_total = frais_inscription + (mensualite * nb_mensualites)


def _reporter_impayes(db: Session, matricule_eleve: str, id_annee_origine: int, nouvelle_inscription: models.Inscriptions):
    ancienne = db.query(models.Inscriptions).filter(
        models.Inscriptions.matricule_eleve == matricule_eleve,
        models.Inscriptions.id_annee_scolaire == id_annee_origine,
    ).first()
    if not ancienne:
        return

    credit = ancienne.credit_disponible or 0.0

    impayes = db.query(models.Echeances).filter(
        models.Echeances.id_inscription == ancienne.id,
        models.Echeances.statut.in_(["EN_ATTENTE", "PARTIEL"]),
    ).all()

    for ech in impayes:
        reste = max(ech.montant_du - ech.montant_paye, 0.0)
        if reste <= 0:
            continue
        if credit > 0:
            couvert = min(credit, reste)
            reste -= couvert
            credit -= couvert
        if reste <= 0:
            ech.statut = "REPORTE"
            continue

        existing = db.query(models.Echeances).filter(
            models.Echeances.id_inscription == nouvelle_inscription.id,
            models.Echeances.type_echeance == ech.type_echeance,
            models.Echeances.mois == ech.mois,
        ).first()

        if existing:
            existing.montant_du += reste
            if existing.statut == "SOLDE":
                existing.statut = "EN_ATTENTE"
        else:
            db.add(models.Echeances(
                id_inscription=nouvelle_inscription.id, id_classe=nouvelle_inscription.id_classe,
                type_echeance=ech.type_echeance, mois=ech.mois, date_echeance=nouvelle_inscription.date_inscription,
                montant_du=reste, montant_paye=0.0, statut="REPORTE", id_echeance_origine=ech.id,
            ))

        ech.statut = "REPORTE"
        nouvelle_inscription.montant_total += reste

    ancienne.credit_disponible = credit


@router.post("/", response_model=schemas.InscriptionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def creer_inscription(payload: schemas.InscriptionCreate, db: Session = Depends(get_db)):
    _verifier_existence(db, payload.matricule_eleve, payload.id_annee_scolaire, payload.id_classe)

    inscription = models.Inscriptions(**payload.model_dump())
    db.add(inscription)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Cet élève a déjà une inscription pour cette année scolaire.")

    _generer_echeances(db, inscription)
    _synchroniser_classe_eleve(db, payload.matricule_eleve, payload.statut, payload.id_classe)
    db.commit()
    db.refresh(inscription)
    return inscription


def _appliquer_filtres_inscriptions(query, matricule_eleve, id_classe, id_annee_scolaire, statut, q):
    if matricule_eleve:
        query = query.filter(models.Inscriptions.matricule_eleve == matricule_eleve)
    if id_classe:
        query = query.filter(models.Inscriptions.id_classe == id_classe)
    if id_annee_scolaire:
        query = query.filter(models.Inscriptions.id_annee_scolaire == id_annee_scolaire)
    if statut:
        query = query.filter(models.Inscriptions.statut == statut)
    if q:
        like = f"%{q}%"
        query = query.join(models.Eleves)
        query = query.filter(or_(
            models.Inscriptions.matricule_eleve.ilike(like),
            models.Inscriptions.code_inscription.ilike(like),
            models.Inscriptions.observation.ilike(like),
            models.Eleves.nom.ilike(like),
            models.Eleves.prenom.ilike(like),
        ))
    return query


@router.get("/", response_model=List[schemas.InscriptionResponse])
def lister_inscriptions(
    matricule_eleve: Optional[str] = None,
    id_classe: Optional[int] = None,
    id_annee_scolaire: Optional[int] = None,
    statut: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_inscriptions(
        db.query(models.Inscriptions).options(joinedload(models.Inscriptions.eleve)),
        matricule_eleve, id_classe, id_annee_scolaire, statut, q,
    )
    results = query.order_by(models.Inscriptions.id_annee_scolaire.desc()).offset(skip).limit(limit).all()
    for insc in results:
        if insc.eleve:
            insc.eleve_nom = insc.eleve.nom
            insc.eleve_prenom = insc.eleve.prenom
    return results


@router.get("/compte")
def compter_inscriptions(
    matricule_eleve: Optional[str] = None,
    id_classe: Optional[int] = None,
    id_annee_scolaire: Optional[int] = None,
    statut: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_inscriptions(
        db.query(models.Inscriptions), matricule_eleve, id_classe, id_annee_scolaire, statut, q
    )
    return {"total": query.count()}


@router.get("/eleve/{matricule_eleve}/historique", response_model=List[schemas.InscriptionDetailResponse])
def historique_eleve(matricule_eleve: str, db: Session = Depends(get_db)):
    if not db.query(models.Eleves).filter(models.Eleves.matricule == matricule_eleve).first():
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    # Import différé pour éviter tout risque de dépendance circulaire entre routeurs :
    # réutilise la même logique d'enrichissement que le dossier élève (finances,
    # moyennes) plutôt que de renvoyer InscriptionDetailResponse avec ses champs
    # calculés silencieusement à leurs valeurs par défaut (0 / None / []).
    from routers.eleves import _construire_inscription_enrichie

    inscriptions = (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.classe),
            joinedload(models.Inscriptions.annee_scolaire),
            joinedload(models.Inscriptions.paiements),
            joinedload(models.Inscriptions.echeances),
        )
        .filter(models.Inscriptions.matricule_eleve == matricule_eleve)
        .join(models.AnneesScolaires)
        .order_by(models.AnneesScolaires.date_debut.desc())
        .all()
    )
    return [_construire_inscription_enrichie(db, insc) for insc in inscriptions]


@router.get("/{inscription_id}", response_model=schemas.InscriptionDetailResponse)
def get_inscription(inscription_id: int, db: Session = Depends(get_db)):
    from routers.eleves import _construire_inscription_enrichie

    insc = (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.classe),
            joinedload(models.Inscriptions.annee_scolaire),
            joinedload(models.Inscriptions.paiements),
            joinedload(models.Inscriptions.echeances),
        )
        .filter(models.Inscriptions.id == inscription_id)
        .first()
    )
    if not insc:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    return _construire_inscription_enrichie(db, insc)


@router.put("/{inscription_id}", response_model=schemas.InscriptionResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def modifier_inscription(inscription_id: int, payload: schemas.InscriptionUpdate, db: Session = Depends(get_db)):
    inscription = db.query(models.Inscriptions).filter(models.Inscriptions.id == inscription_id).first()
    if not inscription:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    if inscription.annee_scolaire and inscription.annee_scolaire.cloturee:
        raise HTTPException(status_code=409, detail="Cette année scolaire est clôturée.")

    donnees = payload.model_dump(exclude_unset=True)
    changement_classe = (
        "id_classe" in donnees and donnees["id_classe"] is not None and donnees["id_classe"] != inscription.id_classe
    )
    if "id_classe" in donnees and donnees["id_classe"] is not None:
        if not db.query(models.Classes).filter(models.Classes.id == donnees["id_classe"]).first():
            raise HTTPException(status_code=404, detail="Classe introuvable.")

    for champ, valeur in donnees.items():
        setattr(inscription, champ, valeur)

    if changement_classe:
        nouvelle_classe = db.query(models.Classes).filter(models.Classes.id == inscription.id_classe).first()
        if nouvelle_classe:
            nb_mensualites = 0
            for echeance in inscription.echeances:
                if echeance.type_echeance == "MENSUALITE":
                    nb_mensualites += 1
                if echeance.statut != "SOLDE":
                    echeance.montant_du = (
                        nouvelle_classe.frais_inscription
                        if echeance.type_echeance == "INSCRIPTION"
                        else nouvelle_classe.mensualite
                    )
            inscription.montant_total = nouvelle_classe.frais_inscription + (nouvelle_classe.mensualite * nb_mensualites)

    _synchroniser_classe_eleve(db, inscription.matricule_eleve, inscription.statut, inscription.id_classe)
    db.commit()
    db.refresh(inscription)
    return inscription


@router.delete("/{inscription_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def supprimer_inscription(inscription_id: int, db: Session = Depends(get_db)):
    insc = db.query(models.Inscriptions).filter(models.Inscriptions.id == inscription_id).first()
    if not insc:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    db.delete(insc)
    db.commit()
    return None


@router.post("/passage-annee", response_model=schemas.PassageAnneeResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin"))])
def passage_annee(payload: schemas.PassageAnneeRequest, db: Session = Depends(get_db)):
    if not db.query(models.Classes).filter(models.Classes.id == payload.id_classe_origine).first():
        raise HTTPException(status_code=404, detail="Classe d'origine introuvable.")
    annee_dest = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == payload.id_annee_scolaire_destination).first()
    if not annee_dest:
        raise HTTPException(status_code=404, detail="Année de destination introuvable.")
    if annee_dest.cloturee:
        raise HTTPException(status_code=409, detail="L'année de destination est déjà clôturée.")

    eleves = db.query(models.Eleves).filter(models.Eleves.classe_id == payload.id_classe_origine).all()
    nb_creees, nb_redoublants, erreurs = 0, 0, []

    for eleve in eleves:
        if eleve.matricule in payload.matricules_exclus:
            continue
        est_redoublant = eleve.matricule in payload.matricules_redoublants
        statut = "Redoublant" if est_redoublant else "Inscrit"
        id_classe_cible = payload.id_classe_origine if est_redoublant else payload.id_classe_destination

        nouvelle_inscription = models.Inscriptions(
            matricule_eleve=eleve.matricule, id_classe=id_classe_cible,
            id_annee_scolaire=payload.id_annee_scolaire_destination, statut=statut,
        )
        db.add(nouvelle_inscription)
        try:
            with db.begin_nested():
                db.flush()
        except IntegrityError:
            erreurs.append(f"{eleve.matricule} : inscription déjà existante.")
            continue

        _generer_echeances(db, nouvelle_inscription)
        db.flush()
        _reporter_impayes(db, eleve.matricule, payload.id_annee_scolaire_origine, nouvelle_inscription)
        _synchroniser_classe_eleve(db, eleve.matricule, statut, id_classe_cible)
        nb_creees += 1
        if est_redoublant:
            nb_redoublants += 1

    db.commit()
    return {"nb_inscriptions_creees": nb_creees, "nb_redoublants": nb_redoublants, "erreurs": erreurs}
