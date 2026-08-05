from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/eleves", tags=["Élèves"], dependencies=[Depends(get_current_user)])


class EleveUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    lieu_de_naissance: Optional[str] = None
    adresse: Optional[str] = None
    classe_id: Optional[int] = None
    statut: Optional[str] = None
    photo: Optional[str] = None
    acte_naissance: Optional[bool] = None
    carnet_sante: Optional[bool] = None
    jugement_tutelle: Optional[bool] = None
    photo_id: Optional[bool] = None


def _resoudre_annee_inscription(db: Session, annee_scolaire_id: Optional[int]) -> int:
    """Année scolaire pour une inscription : celle fournie (validée) sinon l'active."""
    from models.annees_scolaires import AnneesScolaires

    if annee_scolaire_id is not None:
        annee = db.query(AnneesScolaires).filter(AnneesScolaires.id == annee_scolaire_id).first()
        if not annee:
            raise HTTPException(status_code=404, detail="Année scolaire introuvable.")
        return annee.id
    annee_active = (
        db.query(AnneesScolaires)
        .filter(AnneesScolaires.active.is_(True))
        .order_by(AnneesScolaires.date_debut.desc())
        .first()
    )
    if not annee_active:
        raise HTTPException(status_code=400, detail="Aucune année scolaire active : impossible d'inscrire l'élève.")
    return annee_active.id


def _inscrire_eleve(db: Session, matricule: str, id_classe: int, annee_scolaire_id: Optional[int]):
    """Crée l'inscription de l'année (avec échéancier) et synchronise la classe.

    Idempotent : si une inscription existe déjà pour (élève, année), son
    id_classe est simplement mis à jour pour éviter les doublons.
    """
    from routers.inscriptions import _generer_echeances, _synchroniser_classe_eleve

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
        if existante.id_classe != id_classe:
            existante.id_classe = id_classe
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


@router.post("/", response_model=schemas.EleveResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_eleve(eleve: schemas.EleveCreate, db: Session = Depends(get_db)):
    if not db.query(models.Tuteurs).filter(models.Tuteurs.id == eleve.tuteur_id).first():
        raise HTTPException(status_code=404, detail="Le tuteur spécifié n'existe pas.")
    donnees = eleve.model_dump()
    # Transitoire : utilisé par before_insert pour l'année du matricule, non persisté.
    annee_scolaire_id = donnees.pop("annee_scolaire_id", None)
    nouveau_eleve = models.Eleves(**donnees)
    nouveau_eleve.annee_scolaire_id = annee_scolaire_id
    db.add(nouveau_eleve)
    db.flush()  # before_insert génère le matricule

    # Affecter une classe à la création équivaut à inscrire l'élève.
    if donnees.get("classe_id") is not None:
        _inscrire_eleve(db, nouveau_eleve.matricule, donnees["classe_id"], annee_scolaire_id)

    db.commit()
    db.refresh(nouveau_eleve)
    return nouveau_eleve


@router.get("/", response_model=List[schemas.EleveResponse])
def get_all_eleves(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    q: Optional[str] = None,
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
    return (
        query
        .order_by(models.Eleves.matricule)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/compte")
def compter_eleves(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Total d'élèves (après filtre q) pour la pagination de la liste."""
    query = db.query(func.count(models.Eleves.matricule))
    if q and q.strip():
        motif = f"%{q.strip().lower()}%"
        query = query.filter(or_(
            func.lower(models.Eleves.nom).like(motif),
            func.lower(models.Eleves.prenom).like(motif),
            func.lower(models.Eleves.matricule).like(motif),
        ))
    return {"total": query.scalar() or 0}


@router.put("/{matricule}", response_model=schemas.EleveResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_eleve(matricule: str, payload: EleveUpdate, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

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
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    return eleve


@router.patch("/{matricule}/desactiver", response_model=schemas.EleveResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def desactiver_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    eleve.statut = "inactif"
    db.commit()
    db.refresh(eleve)
    return eleve


@router.patch("/{matricule}/activer", response_model=schemas.EleveResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def activer_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    eleve.statut = "actif"
    db.commit()
    db.refresh(eleve)
    return eleve


# ─── Dossier complet (fiche élève) ─────────────────────────────────────────────
# Reconstruit à partir des schémas existants (DossierEleveResponse,
# InscriptionDetailResponse, MoyenneTrimestre, NoteParMatiere), qui étaient déjà
# définis et importés mais que rien n'exposait : il manquait ce endpoint.

def _moyenne_annuelle(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> Optional[float]:
    bulletins = (
        db.query(models.Bulletins)
        .join(models.Trimestres, models.Bulletins.id_trimestre == models.Trimestres.id)
        .filter(
            models.Bulletins.matricule_eleve == matricule_eleve,
            models.Trimestres.annee_scolaire_id == id_annee_scolaire,
        )
        .all()
    )
    if not bulletins:
        return None
    return round(sum(b.moyenne_generale for b in bulletins) / len(bulletins), 2)


def _moyennes_par_trimestre(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> List["schemas.MoyenneTrimestre"]:
    trimestres = (
        db.query(models.Trimestres)
        .filter(models.Trimestres.annee_scolaire_id == id_annee_scolaire)
        .order_by(models.Trimestres.date_debut.asc())
        .all()
    )
    resultats = []
    for numero, trimestre in enumerate(trimestres, start=1):
        bulletin = (
            db.query(models.Bulletins)
            .filter(
                models.Bulletins.matricule_eleve == matricule_eleve,
                models.Bulletins.id_trimestre == trimestre.id,
            )
            .first()
        )
        resultats.append(schemas.MoyenneTrimestre(
            numero=numero,
            periode=trimestre.nom,
            moyenne=bulletin.moyenne_generale if bulletin else None,
        ))
    return resultats


def _notes_par_matiere(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> List["schemas.NoteParMatiere"]:
    resultats = (
        db.query(models.Cours.nom, func.count(models.Notes.id), func.avg(models.Notes.note))
        .join(models.Notes, models.Notes.id_cours == models.Cours.id)
        .join(models.Trimestres, models.Notes.id_trimestre == models.Trimestres.id)
        .filter(
            models.Notes.matricule_eleve == matricule_eleve,
            models.Trimestres.annee_scolaire_id == id_annee_scolaire,
        )
        .group_by(models.Cours.nom)
        .all()
    )
    return [
        schemas.NoteParMatiere(matiere=nom, nb_notes=nb, moyenne=round(float(moy), 2) if moy is not None else None)
        for nom, nb, moy in resultats
    ]


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
    reste_a_payer = sum(e.reste_a_payer for e in inscription.echeances)

    base = schemas.InscriptionResponse.model_validate(inscription).model_dump()
    return schemas.InscriptionDetailResponse(
        **base,
        classe=inscription.classe,
        annee_scolaire=annee,
        eleve=inscription.eleve,
        nb_absences=nb_absences,
        moyenne_annuelle=_moyenne_annuelle(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else None,
        moyennes_par_trimestre=_moyennes_par_trimestre(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else [],
        paiements=inscription.paiements,
        montant_paye=montant_paye,
        reste_a_payer=reste_a_payer,
        notes_par_matiere=_notes_par_matiere(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else [],
    )


@router.get("/{matricule}/dossier", response_model=schemas.DossierEleveResponse)
def get_dossier_eleve(matricule: str, db: Session = Depends(get_db)):
    """Fiche complète d'un élève : profil, historique d'inscriptions (avec
    finances et moyennes), notes, absences et bulletins."""
    eleve = (
        db.query(models.Eleves)
        .options(joinedload(models.Eleves.tuteur), joinedload(models.Eleves.classe_relation))
        .filter(models.Eleves.matricule == matricule)
        .first()
    )
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

    inscriptions = (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.classe),
            joinedload(models.Inscriptions.annee_scolaire),
            joinedload(models.Inscriptions.paiements),
            joinedload(models.Inscriptions.echeances),
        )
        .filter(models.Inscriptions.matricule_eleve == matricule)
        .join(models.AnneesScolaires)
        .order_by(models.AnneesScolaires.date_debut.desc())
        .all()
    )
    inscriptions_enrichies = [_construire_inscription_enrichie(db, insc) for insc in inscriptions]

    notes = (
        db.query(models.Notes)
        .options(
            joinedload(models.Notes.cours),
            joinedload(models.Notes.classe),
            joinedload(models.Notes.enseignant),
            joinedload(models.Notes.trimestre),
        )
        .filter(models.Notes.matricule_eleve == matricule)
        .order_by(models.Notes.date.desc())
        .all()
    )
    absences = (
        db.query(models.Absences)
        .options(joinedload(models.Absences.cours))
        .filter(models.Absences.matricule_eleve == matricule)
        .order_by(models.Absences.date_absence.desc())
        .all()
    )
    bulletins = (
        db.query(models.Bulletins)
        .options(joinedload(models.Bulletins.details))
        .filter(models.Bulletins.matricule_eleve == matricule)
        .order_by(models.Bulletins.generated_at.desc())
        .all()
    )
    annee_active = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()  # noqa: E712

    documents = (
        db.query(models.Documents)
        .options(joinedload(models.Documents.eleve))
        .filter(models.Documents.matricule_eleve == matricule)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    )

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
        jugement_tutelle=eleve.jugement_tutelle,
        photo_id=eleve.photo_id,
        created_at=eleve.created_at,
        updated_at=eleve.updated_at,
        tuteur=schemas.TuteurResponse.model_validate(eleve.tuteur),
        classe_relation=schemas.ClasseResponse.model_validate(eleve.classe_relation) if eleve.classe_relation else None,
        inscriptions=inscriptions_enrichies,
        notes=[schemas.NoteResponse.model_validate(n) for n in notes],
        absences=[schemas.AbsenceResponse.model_validate(a) for a in absences],
        bulletins=[schemas.BulletinResponse.model_validate(b) for b in bulletins],
        documents=[schemas.DocumentResponse.model_validate(d) for d in documents],
        annee_scolaire=schemas.AnneeScolaireResponse.model_validate(annee_active) if annee_active else None,
    )
