from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/tuteurs", tags=["Tuteurs"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=schemas.TuteurResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_tuteur(tuteur: schemas.TuteurCreate, db: Session = Depends(get_db)):
    nouveau_tuteur = models.Tuteurs(**tuteur.model_dump())
    db.add(nouveau_tuteur)
    db.commit()
    db.refresh(nouveau_tuteur)
    return nouveau_tuteur

@router.get("/", response_model=List[schemas.TuteurResponse])
def get_all_tuteurs(q: Optional[str] = None, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    query = db.query(models.Tuteurs)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.Tuteurs.nom.ilike(like),
            models.Tuteurs.prenom.ilike(like),
            models.Tuteurs.telephone.ilike(like),
            models.Tuteurs.profession.ilike(like),
            models.Tuteurs.email.ilike(like),
            models.Tuteurs.code_tuteur.ilike(like),
        ))
    return query.order_by(models.Tuteurs.id).offset(skip).limit(limit).all()

@router.get("/compte")
def compter_tuteurs(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Tuteurs)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.Tuteurs.nom.ilike(like),
            models.Tuteurs.prenom.ilike(like),
            models.Tuteurs.telephone.ilike(like),
            models.Tuteurs.profession.ilike(like),
            models.Tuteurs.email.ilike(like),
            models.Tuteurs.code_tuteur.ilike(like),
        ))
    return {"total": query.count()}

@router.get("/{tuteur_id}", response_model=schemas.TuteurDetailResponse)
def get_tuteur(tuteur_id: int, db: Session = Depends(get_db)):
    db_tuteur = db.query(models.Tuteurs).filter(models.Tuteurs.id == tuteur_id).first()
    if not db_tuteur:
        raise HTTPException(status_code=404, detail="Tuteur introuvable")
    return db_tuteur

@router.put("/{tuteur_id}", response_model=schemas.TuteurResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_tuteur(tuteur_id: int, tuteur_update: schemas.TuteurCreate, db: Session = Depends(get_db)):
    db_tuteur = db.query(models.Tuteurs).filter(models.Tuteurs.id == tuteur_id).first()
    if not db_tuteur:
        raise HTTPException(status_code=404, detail="Tuteur introuvable")
    for key, value in tuteur_update.model_dump().items():
        setattr(db_tuteur, key, value)
    db.commit()
    db.refresh(db_tuteur)
    return db_tuteur

@router.delete("/{tuteur_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_tuteur(tuteur_id: int, db: Session = Depends(get_db)):
    db_tuteur = db.query(models.Tuteurs).filter(models.Tuteurs.id == tuteur_id).first()
    if not db_tuteur:
        raise HTTPException(status_code=404, detail="Tuteur introuvable")
    try:
        db.delete(db_tuteur)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de supprimer ce tuteur : il possède encore des élèves rattachés.")
    return None
