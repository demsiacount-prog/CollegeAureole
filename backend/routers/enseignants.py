from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/enseignants", tags=["Enseignants"], dependencies=[Depends(get_current_user)])


# ─── CRUD de base ─────────────────────────────────────────────────────────────
@router.post("/", response_model=schemas.EnseignantResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_enseignant(enseignant: schemas.EnseignantCreate, db: Session = Depends(get_db)):
    if db.query(models.Enseignants).filter(models.Enseignants.email == enseignant.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
    nouveau_prof = models.Enseignants(**enseignant.model_dump())
    db.add(nouveau_prof)
    db.commit()
    db.refresh(nouveau_prof)
    return nouveau_prof


@router.get("/", response_model=List[schemas.EnseignantResponse])
def get_all_enseignants(q: Optional[str] = None, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    query = db.query(models.Enseignants)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.Enseignants.matricule.ilike(like),
            models.Enseignants.nom.ilike(like),
            models.Enseignants.prenom.ilike(like),
            models.Enseignants.specialite.ilike(like),
            models.Enseignants.email.ilike(like),
        ))
    return query.order_by(models.Enseignants.matricule).offset(skip).limit(limit).all()


@router.get("/compte")
def compter_enseignants(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Enseignants)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.Enseignants.matricule.ilike(like),
            models.Enseignants.nom.ilike(like),
            models.Enseignants.prenom.ilike(like),
            models.Enseignants.specialite.ilike(like),
            models.Enseignants.email.ilike(like),
        ))
    return {"total": query.count()}


@router.get("/{matricule}", response_model=schemas.EnseignantResponse)
def get_enseignant(matricule: str, db: Session = Depends(get_db)):
    db_ens = db.query(models.Enseignants).filter(models.Enseignants.matricule == matricule).first()
    if not db_ens:
        raise HTTPException(status_code=404, detail="Enseignant introuvable")
    return db_ens


@router.put("/{matricule}", response_model=schemas.EnseignantResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_enseignant(matricule: str, enseignant_update: schemas.EnseignantCreate, db: Session = Depends(get_db)):
    db_ens = db.query(models.Enseignants).filter(models.Enseignants.matricule == matricule).first()
    if not db_ens:
        raise HTTPException(status_code=404, detail="Enseignant introuvable")
    email_existant = db.query(models.Enseignants).filter(
        models.Enseignants.email == enseignant_update.email,
        models.Enseignants.matricule != matricule
    ).first()
    if email_existant:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé par un autre enseignant.")
    for key, value in enseignant_update.model_dump().items():
        setattr(db_ens, key, value)
    db.commit()
    db.refresh(db_ens)
    return db_ens


@router.delete("/{matricule}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_enseignant(matricule: str, db: Session = Depends(get_db)):
    db_ens = db.query(models.Enseignants).filter(models.Enseignants.matricule == matricule).first()
    if not db_ens:
        raise HTTPException(status_code=404, detail="Enseignant introuvable")
    db.delete(db_ens)
    db.commit()
    return None


# ─── Helpers internes ─────────────────────────────────────────────────────────

def _construire_historique(db: Session, matricule: str):
    """
    Historique par année scolaire via Seances.
    On charge les objets liés manuellement via leurs ids pour éviter
    les problèmes de lazy loading SQLAlchemy.
    """
    # 1. Tous les cours de cet enseignant (dict id → objet)
    cours_list = (
        db.query(models.Cours)
        .filter(models.Cours.matricule_enseignant == matricule)
        .all()
    )
    if not cours_list:
        return []
    cours_map = {c.id: c for c in cours_list}
    cours_ids = list(cours_map.keys())

    # 2. Toutes les séances (on lit uniquement les ids, pas les relations)
    seances = (
        db.query(models.Seances)
        .filter(models.Seances.id_cours.in_(cours_ids))
        .all()
    )
    if not seances:
        return []

    # 3. Charger toutes les années et classes concernées en une seule requête
    annee_ids  = list({s.id_annee_scolaire for s in seances if s.id_annee_scolaire})
    classe_ids = list({s.id_classe for s in seances if s.id_classe})

    annees_map  = {
        a.id: a for a in db.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.id.in_(annee_ids)).all()
    }
    classes_map = {
        c.id: c for c in db.query(models.Classes)
        .filter(models.Classes.id.in_(classe_ids)).all()
    }

    # 4. Regrouper par année, dédoublonner par (cours, classe)
    affectations_map: dict = {}  # id_annee → list[AffectationResponse]

    for s in seances:
        if not s.id_annee_scolaire or s.id_annee_scolaire not in annees_map:
            continue
        annee_id = s.id_annee_scolaire
        if annee_id not in affectations_map:
            affectations_map[annee_id] = []

        # Déduplication : une seule affectation par (cours, classe) par année
        deja_presente = any(
            aff.cours.id == s.id_cours and aff.classe and aff.classe.id == s.id_classe
            for aff in affectations_map[annee_id]
        )
        if not deja_presente:
            affectations_map[annee_id].append(
                schemas.AffectationResponse(
                    classe=classes_map.get(s.id_classe),
                    cours=cours_map[s.id_cours],
                )
            )

    # 5. Tri : année la plus récente en premier
    annee_ids_tries = sorted(
        affectations_map.keys(),
        key=lambda aid: annees_map[aid].date_debut,
        reverse=True,
    )

    return [
        schemas.HistoriqueAnneeResponse(
            annee_scolaire=annees_map[aid],
            affectations=affectations_map[aid],
        )
        for aid in annee_ids_tries
    ]


def _construire_stats(historique: list) -> schemas.StatsEnseignantResponse:
    classes_distinctes = set()
    matieres_distinctes = set()

    for bloc in historique:
        for aff in bloc.affectations:
            if aff.classe:
                classes_distinctes.add(aff.classe.id)
            if aff.cours:
                nom = getattr(aff.cours, "nom", None)
                if nom:
                    matieres_distinctes.add(nom)

    return schemas.StatsEnseignantResponse(
        nb_annees=len(historique),
        nb_classes_distinctes=len(classes_distinctes),
        nb_matieres_distinctes=len(matieres_distinctes),
    )


# ─── Dossier complet ──────────────────────────────────────────────────────────
@router.get("/{matricule}/dossier", response_model=schemas.DossierEnseignantResponse)
def get_dossier_enseignant(matricule: str, db: Session = Depends(get_db)):
    enseignant = (
        db.query(models.Enseignants)
        .filter(models.Enseignants.matricule == matricule)
        .first()
    )
    if not enseignant and hasattr(models.Enseignants, "id"):
        enseignant = (
            db.query(models.Enseignants)
            .filter(models.Enseignants.id == matricule)
            .first()
        )
    if not enseignant:
        raise HTTPException(status_code=404, detail="Enseignant non trouvé")

    historique = _construire_historique(db, enseignant.matricule)
    stats      = _construire_stats(historique)

    return schemas.DossierEnseignantResponse(
        enseignant=enseignant,
        stats=stats,
        historique=historique,
    )