from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user
from schemas.eleves import EleveUpdate
from services.moyennes import calculer_moyenne_annuelle, calculer_moyennes_par_trimestre, calculer_notes_par_matiere

router = APIRouter(prefix="/api/eleves", tags=["Élèves"], dependencies=[Depends(get_current_user)])


def _resoudre_annee_inscription(db: Session, annee_scolaire_id: Optional[int]) -> int:
    """Année scolaire pour une inscription : celle fournie (validée) sinon l'active."""
    from models.annees_scolaires import AnneesScolaires

    if annee_scolaire_id is not None:
        annee = db.query(AnneesScolaires).filter(AnneesScolaires.id == annee_scolaire_id).first()
        if not annee:
            raise HTTPException(status_code=404, detail="Année scolaire introuvable")
        return annee.id
    annee_active = (
        db.query(AnneesScolaires)
        .filter(AnneesScolaires.active.is_(True))
        .order_by(AnneesScolaires.date_debut.desc())
        .first()
    )
    if not annee_active:
        raise HTTPException(status_code=400, detail="Aucune année scolaire active")
    return annee_active.id


def _inscrire_eleve(db: Session, matricule: str, id_classe: Optional[int], annee_scolaire_id: Optional[int]):
    """Crée l'inscription de l'année (avec échéancier) et synchronise la classe.

    Idempotent : si une inscription existe déjà pour (élève, année), son
    id_classe est simplement mis à jour pour éviter les doublons.
    """
    from routers.inscriptions import _appliquer_changement_classe, _generer_echeances, _synchroniser_classe_eleve

    annee_id = _resoudre_annee_inscription(db, annee_scolaire_id)
    existante = (
        db.query(models.Inscriptions)
        .filter(
            models.Inscriptions.matricule_eleve == matricule,
            models.Inscriptions.id_annee_scolaire == annee_id,
        )
        .first()
    )
    if existante:
        # Une inscription existante ne doit jamais être « écrasée » par un None :
        # la classe actuelle de l'élève (pré-inscription) ne vide pas l'inscription.
        if id_classe is not None and existante.id_classe != id_classe:
            existante.id_classe = id_classe
            _appliquer_changement_classe(db, existante)
        return existante

    inscription = models.Inscriptions(
        matricule_eleve=matricule,
        id_classe=id_classe,
        id_annee_scolaire=annee_id,
        statut="Inscrit",
    )
    db.add(inscription)
    db.flush()
    _generer_echeances(db, inscription)
    _synchroniser_classe_eleve(db, matricule, inscription.statut, inscription.id_classe)
    return inscription


@router.post("/", response_model=schemas.EleveResponse, status_code=status.HTTP_201_CREATED)
def create_eleve(eleve: schemas.EleveCreate, db: Session = Depends(get_db)):
    if not db.query(models.Tuteurs).filter(models.Tuteurs.id == eleve.tuteur_id).first():
        raise HTTPException(status_code=404, detail="Tuteur introuvable")
    if eleve.classe_id is not None:
        if not db.query(models.Classes).filter(models.Classes.id == eleve.classe_id).first():
            raise HTTPException(status_code=404, detail="Classe introuvable")
    donnees = eleve.model_dump()
    # Transitoire : utilisé par before_insert pour l'année du matricule, non persisté.
    annee_scolaire_id = donnees.pop("annee_scolaire_id", None)
    nouveau_eleve = models.Eleves(**donnees)
    nouveau_eleve.annee_scolaire_id = annee_scolaire_id
    db.add(nouveau_eleve)
    db.flush()  # before_insert génère le matricule

    # L'élève est toujours inscrit à sa création. Sans classe, la pré-inscription
    # est enregistrée avec id_classe=None (visible dans les listes de l'année,
    # affecté plus tard via Inscriptions ou l'édition).
    _inscrire_eleve(db, nouveau_eleve.matricule, donnees.get("classe_id"), annee_scolaire_id)

    db.commit()
    db.refresh(nouveau_eleve)
    return nouveau_eleve


def _attacher_contexte_annee(db: Session, eleves: list, id_annee_scolaire: int) -> None:
    """Attribue `classe_annee` / `statut_annee` (classe et statut de l'inscription
    de l'année consultée) à chaque élève, avant la sérialisation Pydantic.

    Ne touche jamais à `Eleves.classe_id` / `Eleves.statut` (état actuel) : ces
    champs transitoires ne servent qu'à l'affichage scopé à l'année."""
    if not eleves:
        return
    matricules = [e.matricule for e in eleves]
    inscriptions = (
        db.query(models.Inscriptions)
        .options(joinedload(models.Inscriptions.classe))
        .filter(
            models.Inscriptions.matricule_eleve.in_(matricules),
            models.Inscriptions.id_annee_scolaire == id_annee_scolaire,
        )
        .all()
    )
    classes = {ins.matricule_eleve: ins.classe for ins in inscriptions}
    statuts = {ins.matricule_eleve: ins.statut for ins in inscriptions}
    for eleve in eleves:
        eleve.classe_annee = classes.get(eleve.matricule)
        eleve.statut_annee = statuts.get(eleve.matricule)


@router.get("/", response_model=List[schemas.EleveResponse])
def get_all_eleves(
    skip: int = 0,
    limit: int = Query(default=100, le=5000),
    q: Optional[str] = None,
    classe_id: Optional[int] = None,
    statut: Optional[str] = None,
    id_annee_scolaire: Optional[int] = None,
    db: Session = Depends(get_db),
):
    # joinedload évite le N+1 : sans lui, sérialiser N élèves déclenche
    # N requêtes supplémentaires (tuteur + classe) car EleveResponse imbrique ces relations.
    query = db.query(models.Eleves).options(
        joinedload(models.Eleves.tuteur),
        joinedload(models.Eleves.classe_relation),
    )
    if q and q.strip():
        motif = f"%{q.strip().lower()}%"
        query = query.filter(or_(
            func.lower(models.Eleves.nom).like(motif),
            func.lower(models.Eleves.prenom).like(motif),
            func.lower(models.Eleves.matricule).like(motif),
        ))
    scope_annee = id_annee_scolaire is not None
    if scope_annee:
        # Liste scopée à une année scolaire précise (ex : effectif d'une année
        # antérieure) → s'appuyer sur les INSCRIPTIONS de cette année. Le statut
        # et la classe d'un élève sont ceux de son inscription : Eleves.statut /
        # Eleves.classe_id reflètent l'état ACTUEL et fausseraient la lecture.
        # Le DISTINCT évite les doublons en cas de double inscription (élève, année).
        query = query.join(
            models.Inscriptions,
            and_(
                models.Inscriptions.matricule_eleve == models.Eleves.matricule,
                models.Inscriptions.id_annee_scolaire == id_annee_scolaire,
            ),
        ).distinct(models.Eleves.matricule)
        if classe_id is not None:
            query = query.filter(models.Inscriptions.id_classe == classe_id)
        if statut and statut.strip():
            motif = f"%{statut.strip().lower()}%"
            query = query.filter(func.lower(models.Inscriptions.statut).like(motif))
    else:
        if classe_id is not None:
            query = query.filter(models.Eleves.classe_id == classe_id)
        if statut and statut.strip():
            motif = f"%{statut.strip().lower()}%"
            query = query.filter(func.lower(models.Eleves.statut).like(motif))

    eleves = (
        query
        .order_by(models.Eleves.matricule)
        .offset(skip)
        .limit(limit)
        .all()
    )
    if scope_annee:
        _attacher_contexte_annee(db, eleves, id_annee_scolaire)
    return eleves


@router.get("/compte")
def compter_eleves(
    q: Optional[str] = None,
    classe_id: Optional[int] = None,
    statut: Optional[str] = None,
    id_annee_scolaire: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Total d'élèves (après filtre q) pour la pagination de la liste."""
    query = db.query(func.count(func.distinct(models.Eleves.matricule)))
    if q and q.strip():
        motif = f"%{q.strip().lower()}%"
        query = query.filter(or_(
            func.lower(models.Eleves.nom).like(motif),
            func.lower(models.Eleves.prenom).like(motif),
            func.lower(models.Eleves.matricule).like(motif),
        ))
    if id_annee_scolaire is not None:
        query = query.join(
            models.Inscriptions,
            and_(
                models.Inscriptions.matricule_eleve == models.Eleves.matricule,
                models.Inscriptions.id_annee_scolaire == id_annee_scolaire,
            ),
        )
        if classe_id is not None:
            query = query.filter(models.Inscriptions.id_classe == classe_id)
        if statut and statut.strip():
            motif = f"%{statut.strip().lower()}%"
            query = query.filter(func.lower(models.Inscriptions.statut).like(motif))
    else:
        if classe_id is not None:
            query = query.filter(models.Eleves.classe_id == classe_id)
        if statut and statut.strip():
            motif = f"%{statut.strip().lower()}%"
            query = query.filter(func.lower(models.Eleves.statut).like(motif))
    return {"total": query.scalar() or 0}


@router.put("/{matricule}", response_model=schemas.EleveResponse)
def update_eleve(matricule: str, payload: EleveUpdate, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")

    donnees = payload.model_dump(exclude_unset=True)
    for key, value in donnees.items():
        setattr(eleve, key, value)

    # Une classe affectée à l'édition vaut inscription : on synchronise
    # l'inscription de l'année active (idempotent). Année absente → on ne
    # bloque pas la modification, le module Inscriptions reste disponible.
    if donnees.get("classe_id") is not None:
        try:
            _inscrire_eleve(db, eleve.matricule, donnees["classe_id"], None)
        except HTTPException:
            # Année scolaire absente : la résolution échoue avant toute écriture,
            # on ne bloque pas la modification (module Inscriptions disponible).
            pass

    db.commit()
    db.refresh(eleve)
    return eleve


@router.get("/{matricule}", response_model=schemas.EleveResponse)
def get_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = (
        db.query(models.Eleves)
        .options(joinedload(models.Eleves.tuteur), joinedload(models.Eleves.classe_relation))
        .filter(models.Eleves.matricule == matricule)
        .first()
    )
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")
    return eleve


@router.patch("/{matricule}/desactiver", response_model=schemas.EleveResponse)
def desactiver_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")
    eleve.statut = "inactif"
    db.commit()
    db.refresh(eleve)
    return eleve


@router.patch("/{matricule}/activer", response_model=schemas.EleveResponse)
def activer_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")
    eleve.statut = "actif"
    db.commit()
    db.refresh(eleve)
    return eleve


# ─── Dossier complet (fiche élève) ─────────────────────────────────────────────
# Reconstruit à partir des schémas existants (DossierEleveResponse,
# InscriptionDetailResponse, MoyenneTrimestre, NoteParMatiere), qui étaient déjà
# définis et importés mais que rien n'exposait : il manquait ce endpoint.

def _construire_inscription_enrichie(db: Session, inscription: models.Inscriptions) -> "schemas.InscriptionDetailResponse":
    annee = inscription.annee_scolaire
    nb_absences = 0
    if annee:
        nb_absences = (
            db.query(func.count(models.Absences.id))
            .filter(
                models.Absences.matricule_eleve == inscription.matricule_eleve,
                models.Absences.date_absence >= annee.date_debut,
                models.Absences.date_absence <= annee.date_fin,
            )
            .scalar()
            or 0
        )

    montant_paye = sum((e.montant_paye or 0.0) for e in inscription.echeances)
    # Le reste dû ne compte que les échéances payables. Les échéances REPORTE
    # sources (id_echeance_origine NULL) ont vu leur impayé transféré vers les
    # échéances REPORTE portées : les compter serait un double comptage.
    reste_a_payer = sum(
        e.reste_a_payer
        for e in inscription.echeances
        if e.statut in ("EN_ATTENTE", "PARTIEL") or (e.statut == "REPORTE" and e.id_echeance_origine is not None)
    )

    base = schemas.InscriptionResponse.model_validate(inscription).model_dump()
    return schemas.InscriptionDetailResponse(
        **base,
        classe=inscription.classe,
        annee_scolaire=annee,
        eleve=inscription.eleve,
        nb_absences=nb_absences,
        moyenne_annuelle=calculer_moyenne_annuelle(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else None,
        moyennes_par_trimestre=calculer_moyennes_par_trimestre(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else [],
        paiements=inscription.paiements,
        montant_paye=montant_paye,
        reste_a_payer=reste_a_payer,
        notes_par_matiere=calculer_notes_par_matiere(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else [],
    )


@router.get("/{matricule}/dossier", response_model=schemas.DossierEleveResponse)
def get_dossier_eleve(
    matricule: str,
    id_annee_scolaire: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Fiche d'un élève restreinte à l'année de consultation
    (`id_annee_scolaire`, défaut : l'année active).

    Toutes les données dépendantes de l'année — inscriptions, notes, absences,
    bulletins et donc paiements — sont celles de l'année consultée. Le profil
    (identité) et les documents restent intacts.
    """
    eleve = (
        db.query(models.Eleves)
        .options(joinedload(models.Eleves.tuteur), joinedload(models.Eleves.classe_relation))
        .filter(models.Eleves.matricule == matricule)
        .first()
    )
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")

    annee_active = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()  # noqa: E712
    if id_annee_scolaire is not None:
        annee_consultation = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == id_annee_scolaire).first()
        if not annee_consultation:
            raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    else:
        annee_consultation = annee_active

    # Trimestres de l'année : pivot de rattachement des notes et bulletins à une
    # année (une note/bulletin appartient à l'année de son trimestre).
    if annee_consultation is not None:
        trimestres_consultation = (
            db.query(models.Trimestres)
            .filter(models.Trimestres.annee_scolaire_id == annee_consultation.id)
            .all()
        )
        trimestre_ids = [t.id for t in trimestres_consultation]
    else:
        trimestre_ids = []

    inscriptions_query = (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.classe),
            joinedload(models.Inscriptions.annee_scolaire),
            joinedload(models.Inscriptions.paiements),
            joinedload(models.Inscriptions.echeances),
        )
        .filter(models.Inscriptions.matricule_eleve == matricule)
    )
    if annee_consultation is not None:
        inscriptions_query = inscriptions_query.filter(
            models.Inscriptions.id_annee_scolaire == annee_consultation.id
        )
    inscriptions = inscriptions_query.all()
    inscriptions_enrichies = [_construire_inscription_enrichie(db, insc) for insc in inscriptions]

    conditions_notes = []
    if trimestre_ids:
        conditions_notes.append(models.Notes.id_trimestre.in_(trimestre_ids))
    if annee_consultation is not None and annee_consultation.date_debut and annee_consultation.date_fin:
        # Notes saisies sans trimestre : rattachées à l'année par leur date.
        conditions_notes.append(and_(
            models.Notes.id_trimestre.is_(None),
            models.Notes.date >= annee_consultation.date_debut,
            models.Notes.date <= annee_consultation.date_fin,
        ))
    notes_query = (
        db.query(models.Notes)
        .options(
            joinedload(models.Notes.cours),
            joinedload(models.Notes.classe),
            joinedload(models.Notes.enseignant),
            joinedload(models.Notes.trimestre),
        )
        .filter(models.Notes.matricule_eleve == matricule)
    )
    if conditions_notes:
        notes_query = notes_query.filter(or_(*conditions_notes))
    notes = notes_query.order_by(models.Notes.date.desc()).all()

    absences_query = (
        db.query(models.Absences)
        .options(joinedload(models.Absences.cours))
        .filter(models.Absences.matricule_eleve == matricule)
    )
    if annee_consultation is not None and annee_consultation.date_debut and annee_consultation.date_fin:
        absences_query = absences_query.filter(
            models.Absences.date_absence >= annee_consultation.date_debut,
            models.Absences.date_absence <= annee_consultation.date_fin,
        )
    absences = absences_query.order_by(models.Absences.date_absence.desc()).all()

    bulletins_query = (
        db.query(models.Bulletins)
        .options(joinedload(models.Bulletins.details))
        .filter(models.Bulletins.matricule_eleve == matricule)
    )
    if trimestre_ids:
        bulletins_query = bulletins_query.filter(models.Bulletins.id_trimestre.in_(trimestre_ids))
    bulletins = bulletins_query.order_by(models.Bulletins.generated_at.desc()).all()

    documents = (
        db.query(models.Documents)
        .options(joinedload(models.Documents.eleve))
        .filter(models.Documents.matricule_eleve == matricule)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    )

    inscription_annee = inscriptions[0] if inscriptions else None
    classe_annee = inscription_annee.classe if inscription_annee is not None else None
    statut_annee = inscription_annee.statut if inscription_annee is not None else None

    # Construit la réponse explicitement plutôt que via model_validate(eleve)
    # qui déclencherait des lazy loads sur toutes les relations (notes, bulletins,
    # absences…) et ferait échouer toute la requête si UNE seule donnée associée
    # est invalide ou incomplète.
    return schemas.DossierEleveResponse(
        matricule=eleve.matricule,
        nom=eleve.nom,
        prenom=eleve.prenom,
        photo=eleve.photo,
        date_de_naissance=eleve.date_de_naissance,
        lieu_de_naissance=eleve.lieu_de_naissance,
        sexe=eleve.sexe,
        adresse=eleve.adresse,
        statut=eleve.statut,
        acte_naissance=eleve.acte_naissance,
        carnet_sante=eleve.carnet_sante,
        numero_acte=eleve.numero_acte,
        jugement_suppletif=eleve.jugement_suppletif,
        date_acte=eleve.date_acte,
        delivre_par=eleve.delivre_par,
        nom_pere=eleve.nom_pere,
        prenom_pere=eleve.prenom_pere,
        fonction_pere=eleve.fonction_pere,
        nom_mere=eleve.nom_mere,
        prenom_mere=eleve.prenom_mere,
        fonction_mere=eleve.fonction_mere,
        created_at=eleve.created_at,
        updated_at=eleve.updated_at,
        tuteur=schemas.TuteurResponse.model_validate(eleve.tuteur),
        classe_relation=schemas.ClasseResponse.model_validate(eleve.classe_relation) if eleve.classe_relation else None,
        classe_annee=schemas.ClasseResponse.model_validate(classe_annee) if classe_annee else None,
        statut_annee=statut_annee,
        inscriptions=inscriptions_enrichies,
        notes=[schemas.NoteResponse.model_validate(n) for n in notes],
        absences=[schemas.AbsenceResponse.model_validate(a) for a in absences],
        bulletins=[schemas.BulletinResponse.model_validate(b) for b in bulletins],
        documents=[schemas.DocumentResponse.model_validate(d) for d in documents],
        annee_scolaire=schemas.AnneeScolaireResponse.model_validate(annee_consultation) if annee_consultation else None,
    )
