from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from periodes import generer_periodes_par_defaut

router = APIRouter(prefix="/api/trimestres", tags=["Trimestres"], dependencies=[Depends(get_current_user)])


@router.post("/generer", response_model=schemas.TrimestresGenererResponse, dependencies=[Depends(require_role("admin"))])
def generer_periodes_par_defaut_pour_annee(payload: schemas.TrimestresGenererRequest, db: Session = Depends(get_db)):
    """Crée le jeu de périodes par défaut (trimestres + compositions) d'une année.

    Idempotent : un type déjà présent dans l'année n'est pas dupliqué.
    """
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == payload.annee_scolaire_id).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    if annee.cloturee:
        raise HTTPException(status_code=409, detail="Année scolaire clôturée")
    cree = generer_periodes_par_defaut(db, annee.id, annee.date_debut, annee.date_fin)
    db.commit()
    return {"cree": cree, "annee_scolaire_id": annee.id}


@router.post("/", response_model=schemas.TrimestreResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin"))])
def create_trimestre(payload: schemas.TrimestreCreate, db: Session = Depends(get_db)):
    if not db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == payload.annee_scolaire_id).first():
        raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    trimestre = models.Trimestres(**payload.model_dump())
    db.add(trimestre)
    db.commit()
    db.refresh(trimestre)
    return trimestre


@router.get("/", response_model=List[schemas.TrimestreResponse])
def get_all_trimestres(annee_scolaire_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Trimestres)
    if annee_scolaire_id:
        query = query.filter(models.Trimestres.annee_scolaire_id == annee_scolaire_id)
    return query.order_by(models.Trimestres.date_debut.asc()).all()


@router.get("/{trimestre_id}", response_model=schemas.TrimestreDetailResponse)
def get_trimestre(trimestre_id: int, db: Session = Depends(get_db)):
    trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == trimestre_id).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")
    return trimestre


@router.put("/{trimestre_id}/verrouiller", response_model=schemas.TrimestreResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def verrouiller_trimestre(trimestre_id: int, db: Session = Depends(get_db)):
    """Bloque toute nouvelle saisie/modification de notes pour ce trimestre
    (typiquement une fois les bulletins publiés)."""
    trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == trimestre_id).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")
    trimestre.verrouille = True
    db.commit()
    db.refresh(trimestre)
    return trimestre


@router.put("/{trimestre_id}/deverrouiller", response_model=schemas.TrimestreResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def deverrouiller_trimestre(trimestre_id: int, db: Session = Depends(get_db)):
    trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == trimestre_id).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")
    trimestre.verrouille = False
    db.commit()
    db.refresh(trimestre)
    return trimestre


@router.delete("/{trimestre_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_trimestre(trimestre_id: int, db: Session = Depends(get_db)):
    trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == trimestre_id).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")
    db.delete(trimestre)
    db.commit()
    return None
