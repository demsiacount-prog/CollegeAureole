from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from periodes import generer_periodes_par_defaut
from services.protections import verifier_annee_scolaire

router = APIRouter(prefix="/api/anneesScolaires", tags=["Années Scolaires"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=schemas.AnneeScolaireResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin"))])
def create_annee_scolaire(payload: schemas.AnneeScolaireCreate, db: Session = Depends(get_db)):
    if db.query(models.AnneesScolaires).filter(models.AnneesScolaires.libelle == payload.libelle).first():
        raise HTTPException(status_code=400, detail="Année scolaire déjà existante")
    if payload.active:
        db.query(models.AnneesScolaires).update({models.AnneesScolaires.active: False})
    nouvelle_annee = models.AnneesScolaires(**payload.model_dump())
    db.add(nouvelle_annee)
    db.flush()
    generer_periodes_par_defaut(db, nouvelle_annee.id, nouvelle_annee.date_debut, nouvelle_annee.date_fin)
    db.commit()
    db.refresh(nouvelle_annee)
    return nouvelle_annee


@router.get("/", response_model=List[schemas.AnneeScolaireResponse])
def get_all_annees_scolaires(db: Session = Depends(get_db)):
    return db.query(models.AnneesScolaires).order_by(models.AnneesScolaires.date_debut.desc()).all()


@router.get("/active", response_model=schemas.AnneeScolaireDetailResponse)
def get_annee_scolaire_active(db: Session = Depends(get_db)):
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Aucune année scolaire active")
    return annee


@router.get("/{annee_id}", response_model=schemas.AnneeScolaireDetailResponse)
def get_annee_scolaire(annee_id: int, db: Session = Depends(get_db)):
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee_id).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    return annee


@router.put("/{annee_id}", response_model=schemas.AnneeScolaireResponse, dependencies=[Depends(require_role("admin"))])
def update_annee_scolaire(annee_id: int, payload: schemas.AnneeScolaireCreate, db: Session = Depends(get_db)):
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee_id).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    if annee.cloturee:
        raise HTTPException(status_code=409, detail="Année scolaire clôturée")

    doublon = db.query(models.AnneesScolaires).filter(
        models.AnneesScolaires.libelle == payload.libelle, models.AnneesScolaires.id != annee_id
    ).first()
    if doublon:
        raise HTTPException(status_code=400, detail="Année scolaire déjà existante")
    if payload.active and not annee.active:
        db.query(models.AnneesScolaires).update({models.AnneesScolaires.active: False})
    for key, value in payload.model_dump().items():
        setattr(annee, key, value)
    db.commit()
    db.refresh(annee)
    return annee


@router.put("/{annee_id}/activer", response_model=schemas.AnneeScolaireResponse, dependencies=[Depends(require_role("admin"))])
def activer_annee_scolaire(annee_id: int, db: Session = Depends(get_db)):
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee_id).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    if annee.cloturee:
        raise HTTPException(status_code=409, detail="Année scolaire clôturée")
    db.query(models.AnneesScolaires).update({models.AnneesScolaires.active: False})
    annee.active = True
    db.commit()
    db.refresh(annee)
    return annee


@router.put("/{annee_id}/cloturer", response_model=schemas.AnneeScolaireResponse, dependencies=[Depends(require_role("admin"))])
def cloturer_annee_scolaire(annee_id: int, db: Session = Depends(get_db)):
    """Verrouille définitivement l'année : plus aucune note, absence ou
    inscription ne pourra y être rattachée. À appeler après le passage de classe."""
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee_id).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    if annee.active:
        raise HTTPException(status_code=400, detail="Année active")
    annee.cloturee = True
    db.query(models.Trimestres).filter(models.Trimestres.annee_scolaire_id == annee_id).update({models.Trimestres.verrouille: True})
    db.commit()
    db.refresh(annee)
    return annee


@router.delete("/{annee_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_annee_scolaire(annee_id: int, db: Session = Depends(get_db)):
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee_id).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable")
    verifier_annee_scolaire(db, annee_id)
    db.delete(annee)
    db.commit()
    return None
