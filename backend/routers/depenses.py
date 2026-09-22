# routers/depenses.py
from datetime import date as date_type
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from database import get_db
import models
import schemas
from security import get_current_user

router = APIRouter(prefix="/api/depenses", tags=["Dépenses"], dependencies=[Depends(get_current_user)])


def _dans_annee_cloturee(db: Session, date_depense: date_type) -> bool:
    """Une dépense n'est pas liée directement à une année scolaire : on déduit
    l'année concernée de sa date pour savoir si elle tombe dans une année
    clôturée (dans ce cas, elle est figée)."""
    if not date_depense:
        return False
    return (
        db.query(models.AnneesScolaires)
        .filter(
            models.AnneesScolaires.cloturee.is_(True),
            models.AnneesScolaires.date_debut <= date_depense,
            models.AnneesScolaires.date_fin >= date_depense,
        )
        .first()
    ) is not None


@router.post("/", response_model=schemas.DepenseResponse, status_code=status.HTTP_201_CREATED)
def creer_depense(payload: schemas.DepenseCreate, db: Session = Depends(get_db)):
    # La création reste permise (saisie d'une dépense historique), seule la
    # modification/suppression est bloquée sur une année clôturée.
    depense = models.Depenses(**payload.model_dump())
    db.add(depense)
    db.commit()
    db.refresh(depense)
    return depense


def _appliquer_filtres_depenses(query, date_debut, date_fin, categorie, q):
    if date_debut:
        query = query.filter(models.Depenses.date >= date_debut)
    if date_fin:
        query = query.filter(models.Depenses.date <= date_fin)
    if categorie:
        query = query.filter(models.Depenses.categorie == categorie)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.Depenses.code_depense.ilike(like),
            models.Depenses.libelle.ilike(like),
            models.Depenses.description.ilike(like),
            models.Depenses.categorie.ilike(like),
        ))
    return query


@router.get("/")
def lister_depenses(
    date_debut: Optional[date_type] = None,
    date_fin:   Optional[date_type] = None,
    categorie:  Optional[str]       = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_depenses(db.query(models.Depenses), date_debut, date_fin, categorie, q)
    return query.order_by(models.Depenses.date.desc()).offset(skip).limit(limit).all()


@router.get("/compte")
def compter_depenses(
    date_debut: Optional[date_type] = None,
    date_fin:   Optional[date_type] = None,
    categorie:  Optional[str]       = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_depenses(db.query(models.Depenses), date_debut, date_fin, categorie, q)
    total_montant = query.with_entities(func.coalesce(func.sum(models.Depenses.montant), 0.0)).scalar()
    return {"total": query.count(), "total_montant": total_montant}


@router.get("/{depense_id}", response_model=schemas.DepenseResponse)
def get_depense(depense_id: int, db: Session = Depends(get_db)):
    dep = db.query(models.Depenses).filter(models.Depenses.id == depense_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    return dep


@router.put("/{depense_id}", response_model=schemas.DepenseResponse)
def modifier_depense(depense_id: int, payload: schemas.DepenseUpdate, db: Session = Depends(get_db)):
    dep = db.query(models.Depenses).filter(models.Depenses.id == depense_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    donnees = payload.model_dump(exclude_unset=True)
    nouveau_date = donnees.get("date")
    if _dans_annee_cloturee(db, dep.date) or (nouveau_date and _dans_annee_cloturee(db, nouveau_date)):
        raise HTTPException(status_code=409, detail="Année scolaire clôturée : modification de la dépense impossible.")
    for k, v in donnees.items():
        setattr(dep, k, v)
    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/{depense_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_depense(depense_id: int, db: Session = Depends(get_db)):
    dep = db.query(models.Depenses).filter(models.Depenses.id == depense_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    if _dans_annee_cloturee(db, dep.date):
        raise HTTPException(status_code=409, detail="Année scolaire clôturée : suppression de la dépense impossible.")
    db.delete(dep)
    db.commit()
    return None