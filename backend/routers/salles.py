from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from services.protections import verifier_salle

router = APIRouter(prefix="/api/salles", tags=["Salles"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=schemas.SalleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_salle(payload: schemas.SalleCreate, db: Session = Depends(get_db)):
    if db.query(models.Salles).filter(models.Salles.nom == payload.nom).first():
        raise HTTPException(status_code=400, detail="Salle déjà existante")
    salle = models.Salles(**payload.model_dump())
    db.add(salle)
    db.commit()
    db.refresh(salle)
    return salle


@router.get("/", response_model=List[schemas.SalleResponse])
def get_all_salles(db: Session = Depends(get_db)):
    return db.query(models.Salles).all()


@router.put("/{salle_id}", response_model=schemas.SalleResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_salle(salle_id: int, payload: schemas.SalleCreate, db: Session = Depends(get_db)):
    salle = db.query(models.Salles).filter(models.Salles.id == salle_id).first()
    if not salle:
        raise HTTPException(status_code=404, detail="Salle introuvable")
    for key, value in payload.model_dump().items():
        setattr(salle, key, value)
    db.commit()
    db.refresh(salle)
    return salle


@router.delete("/{salle_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_salle(salle_id: int, db: Session = Depends(get_db)):
    salle = db.query(models.Salles).filter(models.Salles.id == salle_id).first()
    if not salle:
        raise HTTPException(status_code=404, detail="Salle introuvable")
    verifier_salle(db, salle_id)
    db.delete(salle)
    db.commit()
    return None
