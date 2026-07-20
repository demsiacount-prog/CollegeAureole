# routers/depenses.py
from datetime import date as date_type
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/depenses", tags=["Dépenses"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=schemas.DepenseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur", "comptable"))])
def creer_depense(payload: schemas.DepenseCreate, db: Session = Depends(get_db)):
    depense = models.Depenses(**payload.model_dump())
    db.add(depense)
    db.commit()
    db.refresh(depense)
    return depense


@router.get("/", response_model=List[schemas.DepenseResponse])
def lister_depenses(
    date_debut: Optional[date_type] = None,
    date_fin:   Optional[date_type] = None,
    categorie:  Optional[str]       = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.Depenses)
    if date_debut:
        query = query.filter(models.Depenses.date >= date_debut)
    if date_fin:
        query = query.filter(models.Depenses.date <= date_fin)
    if categorie:
        query = query.filter(models.Depenses.categorie == categorie)
    return query.order_by(models.Depenses.date.desc()).offset(skip).limit(limit).all()


@router.get("/{depense_id}", response_model=schemas.DepenseResponse)
def get_depense(depense_id: int, db: Session = Depends(get_db)):
    dep = db.query(models.Depenses).filter(models.Depenses.id == depense_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dépense introuvable.")
    return dep


@router.put("/{depense_id}", response_model=schemas.DepenseResponse, dependencies=[Depends(require_role("admin", "directeur", "comptable"))])
def modifier_depense(depense_id: int, payload: schemas.DepenseUpdate, db: Session = Depends(get_db)):
    dep = db.query(models.Depenses).filter(models.Depenses.id == depense_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dépense introuvable.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(dep, k, v)
    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/{depense_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def supprimer_depense(depense_id: int, db: Session = Depends(get_db)):
    dep = db.query(models.Depenses).filter(models.Depenses.id == depense_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dépense introuvable.")
    db.delete(dep)
    db.commit()
    return None