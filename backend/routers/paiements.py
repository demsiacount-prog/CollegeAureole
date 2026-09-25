from datetime import date as date_type
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from database import get_db
import models
import schemas
from security import get_current_user
from services import pdf as pdf_service

router = APIRouter(prefix="/api/paiements", tags=["Paiements"], dependencies=[Depends(get_current_user)])

def _filtre_echeances_payables():
    """Condition SQL des échéances réellement payables.

    Sont payables : celles en attente/partielles ET les échéances REPORTE
    portées (id_echeance_origine non NULL), issues d'un passage d'année. Les
    échéances REPORTE sources (id_echeance_origine NULL) sont exclues : leur
    impayé a été transféré vers une échéance portée, les compter serait un
    double comptage."""
    return or_(
        models.Echeances.statut.in_(["EN_ATTENTE", "PARTIEL"]),
        and_(
            models.Echeances.statut == "REPORTE",
            models.Echeances.id_echeance_origine.isnot(None),
        ),
    )


def _mettre_a_jour_statut(echeance: models.Echeances):
    if echeance.montant_du <= 0:
        # Échéance entièrement remisée (montant ramené à zéro) : plus rien dû.
        echeance.statut = "SOLDE"
    elif echeance.montant_paye <= 0:
        # Un impayé reporté non entamé conserve son statut REPORTE.
        if echeance.statut == "REPORTE" or echeance.id_echeance_origine is not None:
            echeance.statut = "REPORTE"
        else:
            echeance.statut = "EN_ATTENTE"
    elif echeance.montant_paye >= echeance.montant_du:
        echeance.statut = "SOLDE"
    else:
        echeance.statut = "PARTIEL"


def _distribuer_paiement(db, inscription, montant_verse, date_paiement, mode, observation, ids_echeances=None) -> dict:
    """Distribue le crédit disponible puis le montant versé sur les échéances
    payables. Le crédit est consommé en premier ; seuls les règlements en
    espèces affectés à une échéance donnent lieu à une ligne Paiements (évite
    le double comptage de total_encaisse). Le cash non affecté reste en crédit
    disponible et est tracé par une ligne Paiements sans échéance (trop-perçu),
    donc annulable/modifiable. Si ids_echeances est précisé, seules ces
    échéances/mois sont alimentés."""
    credit = inscription.credit_disponible or 0.0
    cash = montant_verse
    inscription.credit_disponible = 0.0

    query = (
        db.query(models.Echeances)
        .filter(models.Echeances.id_inscription == inscription.id, _filtre_echeances_payables())
    )
    if ids_echeances:
        query = query.filter(models.Echeances.id.in_(ids_echeances))
    echeances_impayees = query.order_by(models.Echeances.date_echeance.asc()).with_for_update().all()

    paiements_crees, echeances_maj = [], []

    for ech in echeances_impayees:
        if credit <= 0 and cash <= 0:
            break
        a_payer = ech.reste_a_payer
        if a_payer <= 0:
            continue  # échéance déjà soldée en mémoire : pas de paiement à 0

        # 1) Le crédit existant couvre d'abord l'échéance…
        part_credit = min(credit, a_payer)
        credit -= part_credit
        a_payer -= part_credit
        # 2) …le cash ne règle que la part restante.
        part_cash = min(cash, a_payer)
        cash -= part_cash

        if part_credit > 0:
            ech.montant_paye += part_credit
        if part_cash > 0:
            paiement = models.Paiements(
                id_inscription=inscription.id, id_echeance=ech.id, date=date_paiement,
                montant=part_cash, mode=mode, observation=observation,
            )
            db.add(paiement)
            paiements_crees.append(paiement)
            ech.montant_paye += part_cash
        _mettre_a_jour_statut(ech)
        echeances_maj.append(ech)

    # Cash non affecté : conservé en crédit et tracé (donc annulable/modifiable).
    if cash > 0:
        paiement = models.Paiements(
            id_inscription=inscription.id, id_echeance=None, date=date_paiement,
            montant=cash, mode=mode, observation=observation,
        )
        db.add(paiement)
        paiements_crees.append(paiement)

    inscription.credit_disponible = credit + cash

    db.flush()

    # Total des échéances encore dues sur l'inscription (toutes les payables,
    # y compris celles non ciblées par ids_echeances). Les montants mis à jour
    # sont déjà flushés.
    reste_global = (
        db.query(func.sum(models.Echeances.montant_du - models.Echeances.montant_paye))
        .filter(
            models.Echeances.id_inscription == inscription.id,
            _filtre_echeances_payables(),
        )
        .scalar()
    ) or 0.0

    return {"paiements_crees": paiements_crees, "echeances_mises_a_jour": echeances_maj, "reste_global": reste_global}


@router.post("/", response_model=schemas.PaiementResultResponse, status_code=status.HTTP_201_CREATED)
def enregistrer_paiement(payload: schemas.PaiementEcheanceCreate, db: Session = Depends(get_db),
                         user=Depends(get_current_user)):
    inscription = (
        db.query(models.Inscriptions)
        .filter(models.Inscriptions.id == payload.id_inscription)
        .with_for_update()
        .first()
    )
    if not inscription:
        raise HTTPException(status_code=404, detail="Inscription introuvable")
    if inscription.annee_scolaire and inscription.annee_scolaire.cloturee:
        raise HTTPException(status_code=409, detail="Année scolaire clôturée")

    if payload.ids_echeances:
        echeances = (
            db.query(models.Echeances)
            .filter(models.Echeances.id.in_(payload.ids_echeances))
            .all()
        )
        if len(echeances) != len(set(payload.ids_echeances)):
            raise HTTPException(status_code=404, detail="Échéance introuvable")
        for ech in echeances:
            if ech.id_inscription != inscription.id:
                raise HTTPException(status_code=404, detail="Échéance introuvable")
            if ech.statut == "SOLDE":
                raise HTTPException(status_code=400, detail="Échéance déjà soldée")

    # Appliquer les remises AVANT la distribution du paiement
    echeances_map = {}
    if payload.ids_echeances:
        for ech in echeances:
            echeances_map[ech.id] = ech
    if payload.remises:
        for ech_id, remise_data in payload.remises.items():
            ech = echeances_map.get(ech_id)
            if not ech:
                ech = db.query(models.Echeances).filter(
                    models.Echeances.id == ech_id,
                    models.Echeances.id_inscription == inscription.id,
                ).first()
            if not ech:
                raise HTTPException(status_code=404, detail="Échéance introuvable")
            # FIX : cette même vérification existait déjà sur l'endpoint dédié
            # POST /echeances/{id}/remises mais pas ici — une remise supérieure
            # au reste dû pouvait passer sans erreur et fausser la comptabilité.
            if remise_data.montant > ech.reste_a_payer:
                raise HTTPException(status_code=400, detail="Remise supérieure au reste à payer")
            remise = models.Remises(
                id_echeance=ech.id,
                montant=remise_data.montant,
                motif=remise_data.motif,
                date=payload.date,
                utilisateur_id=user.id,
            )
            db.add(remise)
            db.flush()
            _appliquer_remise(db, ech, remise_data.montant)

    result = _distribuer_paiement(db, inscription, payload.montant, payload.date, payload.mode, payload.observation, payload.ids_echeances)
    db.commit()

    for p in result["paiements_crees"]:
        db.refresh(p)
    for e in result["echeances_mises_a_jour"]:
        db.refresh(e)
        db.refresh(e, attribute_names=["remises"])
    db.refresh(inscription)

    return {
        "nb_paiements_crees": len(result["paiements_crees"]),
        "echeances_mises_a_jour": [schemas.EcheanceResponse.model_validate(e) for e in result["echeances_mises_a_jour"]],
        "reste_global": result["reste_global"],
        "credit_disponible": inscription.credit_disponible,
    }


def _filtre_q_paiements(db, query, q: str):
    """Recherche plein texte multi-mots sur les paiements : code, mode,
    observation, élève (matricule, nom, prénom) et classe.

    Sémantique : chaque mot saisi doit correspondre à AU MOINS un champ
    (ET entre mots, OU entre champs). Une sous-requête identifie les
    inscriptions dont l'élève/classe correspondent — sans JOIN, donc sans
    risque de duplication de lignes ni de conflit avec les filtres déjà
    appliqués."""
    sous_requete_eleves = (
        db.query(models.Inscriptions.id)
        .join(models.Eleves, models.Eleves.matricule == models.Inscriptions.matricule_eleve)
        .outerjoin(models.Classes, models.Classes.id == models.Inscriptions.id_classe)
    )
    conditions = []
    for mot in q.split():
        like = f"%{mot}%"
        eleve_correspond = sous_requete_eleves.filter(or_(
            models.Inscriptions.matricule_eleve.ilike(like),
            models.Eleves.nom.ilike(like),
            models.Eleves.prenom.ilike(like),
            models.Classes.nom.ilike(like),
            models.Classes.niveau.ilike(like),
        ))
        conditions.append(or_(
            models.Paiements.code_paiement.ilike(like),
            models.Paiements.mode.ilike(like),
            models.Paiements.observation.ilike(like),
            models.Paiements.id_inscription.in_(eleve_correspond),
        ))
    return query.filter(and_(*conditions))


def _appliquer_filtres_paiements(db, query, id_inscription, matricule_eleve, date_debut, date_fin, q):
    if id_inscription:
        query = query.filter(models.Paiements.id_inscription == id_inscription)
    if matricule_eleve:
        query = query.join(models.Inscriptions).filter(models.Inscriptions.matricule_eleve == matricule_eleve)
    if date_debut:
        query = query.filter(models.Paiements.date >= date_debut)
    if date_fin:
        query = query.filter(models.Paiements.date <= date_fin)
    if q:
        query = _filtre_q_paiements(db, query, q)
    return query


@router.get("/", response_model=List[schemas.PaiementResponse])
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
        db,
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


@router.get("/compte")
def compter_paiements(
    id_inscription: Optional[int] = None,
    matricule_eleve: Optional[str] = None,
    date_debut: Optional[date_type] = None,
    date_fin: Optional[date_type] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_paiements(
        db, db.query(models.Paiements), id_inscription, matricule_eleve, date_debut, date_fin, q
    )
    return {"total": query.count()}


@router.get("/relances", response_model=List[schemas.RelanceResponse])
def get_echeances_en_retard(db: Session = Depends(get_db)):
    """Échéances impayées et dépassées de l'ANNÉE ACTIVE — base des relances
    (email/SMS à brancher séparément). Toutes les échéances payables sont
    concernées (en attente/partielles et REPORTE portées) ; chaque relance
    embarque l'élève, sa classe et le contact de son tuteur."""
    aujourdhui = date_type.today()
    inscriptions_annee_active = (
        db.query(models.Inscriptions.id)
        .join(models.AnneesScolaires, models.AnneesScolaires.id == models.Inscriptions.id_annee_scolaire)
        .filter(models.AnneesScolaires.active.is_(True))
    )
    echeances = (
        db.query(models.Echeances)
        .options(
            joinedload(models.Echeances.remises),
            joinedload(models.Echeances.inscription).joinedload(models.Inscriptions.eleve).joinedload(models.Eleves.tuteur),
            joinedload(models.Echeances.inscription).joinedload(models.Inscriptions.classe),
        )
        .filter(
            models.Echeances.date_echeance < aujourdhui,
            _filtre_echeances_payables(),
            models.Echeances.id_inscription.in_(inscriptions_annee_active),
        )
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


@router.get("/stats", response_model=schemas.PaiementStatsResponse)
def get_paiement_stats(db: Session = Depends(get_db)):
    """Synthèse 'payé / impayé' sur tout l'historique, pour les cartes de la
    page Paiements :
      - total_encaisse : somme des règlements réellement encaissés ;
      - montant_impaye : reste à devoir (montant_du - montant_paye) sur les
        échéances non soldées. Les échéances REPORTE sources d'un report
        (id_echeance_origine NULL) sont exclues : leur impayé a été transféré
        dans une nouvelle échéance REPORTE portée (id_echeance_origine non
        NULL), incluse, pour éviter de compter deux fois le même impayé."""
    total_encaisse = (
        db.query(func.coalesce(func.sum(models.Paiements.montant), 0.0)).scalar() or 0.0
    )

    impayees = (
        db.query(models.Echeances)
        .filter(
            models.Echeances.statut.in_(["EN_ATTENTE", "PARTIEL"])
            | (
                (models.Echeances.statut == "REPORTE")
                & (models.Echeances.id_echeance_origine.isnot(None))
            )
        )
        .all()
    )
    montant_impaye = round(
        sum(max(ech.montant_du - ech.montant_paye, 0.0) for ech in impayees), 2
    )

    nb_echeances_soldees = (
        db.query(func.count(models.Echeances.id))
        .filter(models.Echeances.statut == "SOLDE")
        .scalar()
        or 0
    )

    return {
        "total_encaisse": round(float(total_encaisse), 2),
        "montant_impaye": montant_impaye,
        "nb_echeances_soldees": nb_echeances_soldees,
        "nb_echeances_impayees": len(impayees),
    }


@router.get("/{paiement_id}/recu")
def telecharger_recu(paiement_id: int, db: Session = Depends(get_db)):
    """PDF officiel d'un reçu de paiement (bouton « Reçu » du front).

    Route déclarée AVANT `/{paiement_id}` : le segment `recu` est littéral,
    donc sans ambiguïté avec le paramètre entier, mais l'ordre reste explicite
    pour éviter toute capture par la route générique."""
    paiement = (
        db.query(models.Paiements)
        .options(
            joinedload(models.Paiements.inscription).joinedload(models.Inscriptions.eleve),
            joinedload(models.Paiements.inscription).joinedload(models.Inscriptions.classe),
            joinedload(models.Paiements.inscription).joinedload(models.Inscriptions.annee_scolaire),
            joinedload(models.Paiements.echeance),
        )
        .filter(models.Paiements.id == paiement_id)
        .first()
    )
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement introuvable")

    inscription = paiement.inscription
    etab = db.query(models.Etablissement).first()
    annee_label = inscription.annee_scolaire.libelle if inscription and inscription.annee_scolaire else None

    reste_global = 0.0
    if inscription:
        reste_global = (
            db.query(func.sum(models.Echeances.montant_du - models.Echeances.montant_paye))
            .filter(
                models.Echeances.id_inscription == inscription.id,
                _filtre_echeances_payables(),
            )
            .scalar()
        ) or 0.0

    contenu = pdf_service.recu_paiement_pdf(
        paiement,
        etab,
        annee_label=annee_label,
        montant_total=float(inscription.montant_total or 0.0) if inscription else 0.0,
        reste_global=float(reste_global),
    )
    fichier = f"recu-{paiement.code_paiement or paiement.id}.pdf"
    return StreamingResponse(
        content=iter([contenu]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{fichier}"'},
    )


@router.get("/{paiement_id}", response_model=schemas.PaiementResponse)
def get_paiement(paiement_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Paiements).filter(models.Paiements.id == paiement_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paiement introuvable")
    return p


@router.put("/{paiement_id}", response_model=schemas.PaiementResponse)
def modifier_paiement(paiement_id: int, payload: schemas.PaiementUpdate, db: Session = Depends(get_db)):
    p = db.query(models.Paiements).filter(models.Paiements.id == paiement_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paiement introuvable")
    inscription = db.query(models.Inscriptions).filter(models.Inscriptions.id == p.id_inscription).first()
    if inscription and inscription.annee_scolaire and inscription.annee_scolaire.cloturee:
        raise HTTPException(status_code=409, detail="Année scolaire clôturée")

    donnees = payload.model_dump(exclude_unset=True)
    delta = (donnees.get("montant") if donnees.get("montant") is not None else p.montant) - p.montant

    if p.id_echeance:
        ech = db.query(models.Echeances).filter(models.Echeances.id == p.id_echeance).first()
        if ech:
            nouveau_paye = ech.montant_paye + delta
            if nouveau_paye > ech.montant_du:
                raise HTTPException(
                    status_code=400,
                    detail="Le montant dépasse le montant dû de l'échéance : enregistrez l'excédent comme un versement sans échéance (crédit).",
                )
            if nouveau_paye < 0:
                raise HTTPException(
                    status_code=400,
                    detail="La réduction dépasse le montant déjà appliqué à l'échéance.",
                )
            ech.montant_paye = nouveau_paye
            _mettre_a_jour_statut(ech)
    elif delta != 0 and inscription:
        credit_cible = (inscription.credit_disponible or 0.0) + delta
        if credit_cible < 0:
            raise HTTPException(
                status_code=400,
                detail="Impossible de réduire le trop-perçu : le crédit a déjà été consommé.",
            )
        inscription.credit_disponible = credit_cible

    for k, v in donnees.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{paiement_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_paiement(paiement_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Paiements).filter(models.Paiements.id == paiement_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paiement introuvable")
    # FIX : la suppression était le seul endpoint de /paiements à ne pas
    # vérifier la clôture d'année (création et modification le font déjà) ;
    # on pouvait donc altérer l'historique financier d'une année archivée.
    inscription_verif = db.query(models.Inscriptions).filter(models.Inscriptions.id == p.id_inscription).first()
    if inscription_verif and inscription_verif.annee_scolaire and inscription_verif.annee_scolaire.cloturee:
        raise HTTPException(status_code=409, detail="Année scolaire clôturée : suppression du paiement impossible.")
    if p.id_echeance:
        ech = db.query(models.Echeances).filter(models.Echeances.id == p.id_echeance).first()
        if ech:
            avant = ech.montant_paye
            ech.montant_paye = max(avant - p.montant, 0.0)
            # Anciens paiements plafonnés (comportement remplacé) : le surplus
            # d'un paiement supérieur au payé de l'échéance avait été versé au
            # crédit ; on le retire à la suppression pour ne rien laisser en
            # l'air.
            if avant < p.montant and inscription_verif:
                surplus = p.montant - avant
                inscription_verif.credit_disponible = max((inscription_verif.credit_disponible or 0.0) - surplus, 0.0)
            _mettre_a_jour_statut(ech)
    else:
        # Paiement sans échéance = surplus stocké en crédit : le supprimer
        # retire ce crédit (symétrique de modifier_paiement).
        if inscription_verif:
            credit_cible = (inscription_verif.credit_disponible or 0.0) - p.montant
            if credit_cible < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Impossible de supprimer le trop-perçu : le crédit a déjà été consommé.",
                )
            inscription_verif.credit_disponible = credit_cible
    db.delete(p)
    db.commit()
    return None


@router.get("/echeances/{id_inscription}", response_model=List[schemas.EcheanceResponse])
def get_echeances(id_inscription: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Echeances)
        .options(joinedload(models.Echeances.remises))
        .filter(models.Echeances.id_inscription == id_inscription)
        .order_by(models.Echeances.date_echeance.asc())
        .all()
    )


# ─── Remises ────────────────────────────────────────────────────────────────

def _appliquer_remise(db: Session, echeance: models.Echeances, montant_remise: float) -> None:
    """Réduit montant_du d'une échéance. Si montant_paye > nouveau montant_du,
    l'excédent est transféré en crédit sur l'inscription."""
    echeance.montant_du = max(echeance.montant_du - montant_remise, 0.0)
    if echeance.montant_paye > echeance.montant_du:
        excédent = echeance.montant_paye - echeance.montant_du
        inscription = echeance.inscription
        if inscription:
            inscription.credit_disponible = (inscription.credit_disponible or 0.0) + excédent
        echeance.montant_paye = echeance.montant_du
    _mettre_a_jour_statut(echeance)


def _supprimer_remise(db: Session, echeance: models.Echeances, montant_remise: float) -> None:
    """Restaure montant_du après suppression d'une remise."""
    echeance.montant_du += montant_remise
    _mettre_a_jour_statut(echeance)


@router.post("/echeances/{id_echeance}/remises", status_code=status.HTTP_201_CREATED)
def appliquer_remise(id_echeance: int, payload: schemas.RemiseCreate,
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    ech = db.query(models.Echeances).filter(models.Echeances.id == id_echeance).first()
    if not ech:
        raise HTTPException(404, "Échéance introuvable")
    inscription = db.query(models.Inscriptions).filter(models.Inscriptions.id == ech.id_inscription).first()
    if inscription and inscription.annee_scolaire and inscription.annee_scolaire.cloturee:
        raise HTTPException(409, "Cette année scolaire est clôturée.")
    if payload.montant > ech.reste_a_payer:
        raise HTTPException(400, "Remise supérieure au reste à payer")

    remise = models.Remises(
        id_echeance=id_echeance, montant=payload.montant, motif=payload.motif,
        utilisateur_id=user.id, date=payload.date,
    )
    db.add(remise)
    _appliquer_remise(db, ech, payload.montant)
    db.commit()
    db.refresh(remise)
    db.refresh(ech)
    data = schemas.RemiseResponse.model_validate(remise).model_dump()
    data["utilisateur_nom"] = user.nom if user else None
    data["utilisateur_prenom"] = user.prenom if user else None
    return schemas.RemiseResponse(**data)


@router.get("/echeances/{id_echeance}/remises", response_model=List[schemas.RemiseResponse])
def lister_remises(id_echeance: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Remises)
        .options(joinedload(models.Remises.utilisateur))
        .filter(models.Remises.id_echeance == id_echeance)
        .order_by(models.Remises.date.desc())
        .all()
    )


@router.delete("/remises/{remise_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_remise(remise_id: int, db: Session = Depends(get_db)):
    remise = db.query(models.Remises).filter(models.Remises.id == remise_id).first()
    if not remise:
        raise HTTPException(404, "Remise introuvable")
    ech = db.query(models.Echeances).filter(models.Echeances.id == remise.id_echeance).first()
    if ech:
        inscription = db.query(models.Inscriptions).filter(models.Inscriptions.id == ech.id_inscription).first()
        if inscription and inscription.annee_scolaire and inscription.annee_scolaire.cloturee:
            raise HTTPException(409, "Année scolaire clôturée")
        _supprimer_remise(db, ech, remise.montant)
    db.delete(remise)
    db.commit()
    return None


# ─── Paiement groupé par tuteur ─────────────────────────────────────────────

@router.post("/groupes", status_code=status.HTTP_201_CREATED)
def enregistrer_paiement_groupe(payload: schemas.PaiementGroupeCreate,
                                db: Session = Depends(get_db)):
    """Enregistre un paiement unique réparti équitablement entre les enfants
    d'un tuteur. Pour chaque enfant, le montant est distribué sur les
    échéances les plus anciennes d'abord."""
    tuteur = db.query(models.Tuteurs).filter(models.Tuteurs.id == payload.id_tuteur).first()
    if not tuteur:
        raise HTTPException(404, "Tuteur introuvable")

    annee_active = (
        db.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.active == True)  # noqa: E712
        .first()
    )
    if not annee_active:
        raise HTTPException(404, "Aucune année scolaire active")

    eleves = db.query(models.Eleves).filter(models.Eleves.tuteur_id == tuteur.id).all()
    if not eleves:
        raise HTTPException(400, "Aucun élève rattaché")

    inscriptions = []
    for eleve in eleves:
        insc = (
            db.query(models.Inscriptions)
            .filter(
                models.Inscriptions.matricule_eleve == eleve.matricule,
                models.Inscriptions.id_annee_scolaire == annee_active.id,
            )
            .first()
        )
        if insc:
            reste_ins = (
                db.query(func.sum(models.Echeances.montant_du - models.Echeances.montant_paye))
                .filter(
                    models.Echeances.id_inscription == insc.id,
                    _filtre_echeances_payables(),
                )
                .scalar()
            ) or 0.0
            if reste_ins > 0:
                if (annee := insc.annee_scolaire) and annee.cloturee:
                    continue  # année clôturée : aucune écriture autorisée
                inscriptions.append(insc)

    if not inscriptions:
        raise HTTPException(400, "Aucune échéance impayée")

    montant_par_enfant = payload.montant_total / len(inscriptions)

    all_paiements, all_echeances = [], []
    for insc in inscriptions:
        result = _distribuer_paiement(
            db, insc, montant_par_enfant, payload.date,
            payload.mode, payload.observation,
        )
        all_paiements.extend(result["paiements_crees"])
        all_echeances.extend(result["echeances_mises_a_jour"])

    reste_total = sum(
        (db.query(func.sum(models.Echeances.montant_du - models.Echeances.montant_paye))
         .filter(
             models.Echeances.id_inscription == insc.id,
             _filtre_echeances_payables(),
         ).scalar() or 0.0)
        for insc in inscriptions
    )

    db.commit()

    return {
        "nb_enfants": len(inscriptions),
        "nb_paiements_crees": len(all_paiements),
        "reste_total": reste_total,
    }
