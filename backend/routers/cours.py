from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from bareme import bareme_niveau

router = APIRouter(prefix="/api/cours", tags=["Cours"], dependencies=[Depends(get_current_user)])

# CoursResponse imbrique enseignant + classes/coefficients (via classes_affectations) :
# sans eager loading, chaque cours sérialisé déclenche des requêtes supplémentaires.
_EAGER = (
    joinedload(models.Cours.enseignant),
    joinedload(models.Cours.classes_affectations).joinedload(models.AffectationCoursClasse.classe),
)


def _appliquer_affectations(db: Session, cours: models.Cours, affectations: list[schemas.AffectationCoursClasseInput]):
    ids_classes = [a.id_classe for a in affectations]
    classes_existantes = db.query(models.Classes).filter(models.Classes.id.in_(ids_classes)).all()
    if len(classes_existantes) != len(ids_classes):
        raise HTTPException(status_code=404, detail="Classe introuvable")

    # Règle métier : les coefficients ne s'appliquent qu'au second cycle.
    # En EF1 (notes /10, moyenne simple) le coefficient doit rester à 1.
    for a in affectations:
        classe = next(c for c in classes_existantes if c.id == a.id_classe)
        if bareme_niveau(classe.niveau) == 10 and float(a.coefficient) != 1.0:
            raise HTTPException(
                status_code=422,
                detail=f"Le coefficient ne s'applique pas aux classes du premier cycle (EF1) : {classe.niveau} {classe.nom} est notée sur 10 avec une moyenne simple.",
            )

    db.query(models.AffectationCoursClasse).filter(models.AffectationCoursClasse.id_cours == cours.id).delete()
    db.flush()
    for a in affectations:
        db.add(models.AffectationCoursClasse(id_classe=a.id_classe, id_cours=cours.id, coefficient=a.coefficient))


@router.post("/", response_model=schemas.CoursResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_cours(cours: schemas.CoursCreate, db: Session = Depends(get_db)):
    if cours.matricule_enseignant:
        if not db.query(models.Enseignants).filter(models.Enseignants.matricule == cours.matricule_enseignant).first():
            raise HTTPException(status_code=404, detail="Enseignant introuvable")

    nouveau_cours = models.Cours(**cours.model_dump(exclude={"affectations"}))
    db.add(nouveau_cours)
    db.flush()

    _appliquer_affectations(db, nouveau_cours, cours.affectations)

    db.commit()
    db.refresh(nouveau_cours)
    return nouveau_cours


@router.get("/", response_model=List[schemas.CoursResponse])
def get_all_cours(skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return db.query(models.Cours).options(*_EAGER).order_by(models.Cours.id).offset(skip).limit(limit).all()


@router.get("/{cours_id}", response_model=schemas.CoursResponse)
def get_cours(cours_id: int, db: Session = Depends(get_db)):
    db_cours = db.query(models.Cours).options(*_EAGER).filter(models.Cours.id == cours_id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    return db_cours


@router.put("/{cours_id}", response_model=schemas.CoursResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_cours(cours_id: int, cours_update: schemas.CoursCreate, db: Session = Depends(get_db)):
    db_cours = db.query(models.Cours).filter(models.Cours.id == cours_id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours introuvable")

    if cours_update.matricule_enseignant:
        if not db.query(models.Enseignants).filter(models.Enseignants.matricule == cours_update.matricule_enseignant).first():
            raise HTTPException(status_code=404, detail="Enseignant introuvable")

    for key, value in cours_update.model_dump(exclude={"affectations"}).items():
        setattr(db_cours, key, value)

    _appliquer_affectations(db, db_cours, cours_update.affectations)

    db.commit()
    db.refresh(db_cours)
    return db_cours


@router.delete("/{cours_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_cours(cours_id: int, db: Session = Depends(get_db)):
    db_cours = db.query(models.Cours).filter(models.Cours.id == cours_id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    db.delete(db_cours)
    db.commit()
    return None
