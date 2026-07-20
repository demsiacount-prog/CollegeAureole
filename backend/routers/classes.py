from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/classes", tags=["Classes"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=schemas.ClasseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_classe(classe: schemas.ClasseCreate, db: Session = Depends(get_db)):
    nouveau_classe = models.Classes(**classe.model_dump())
    db.add(nouveau_classe)
    db.commit()
    db.refresh(nouveau_classe)
    return nouveau_classe

@router.get("/", response_model=List[schemas.ClasseResponse])
def get_all_classes(skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return db.query(models.Classes).order_by(models.Classes.id).offset(skip).limit(limit).all()

@router.get("/{classe_id}", response_model=schemas.ClasseDetailResponse)
def get_classe_detail(classe_id: int, db: Session = Depends(get_db)):
    classe = db.query(models.Classes).filter(models.Classes.id == classe_id).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    return classe

@router.put("/{classe_id}", response_model=schemas.ClasseResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_classe(classe_id: int, classe_update: schemas.ClasseCreate, db: Session = Depends(get_db)):
    db_classe = db.query(models.Classes).filter(models.Classes.id == classe_id).first()
    if not db_classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    for key, value in classe_update.model_dump().items():
        setattr(db_classe, key, value)
    db.commit()
    db.refresh(db_classe)
    return db_classe

@router.delete("/{classe_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_classe(classe_id: int, db: Session = Depends(get_db)):
    db_classe = db.query(models.Classes).filter(models.Classes.id == classe_id).first()
    if not db_classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    db.delete(db_classe)
    db.commit()
    return None