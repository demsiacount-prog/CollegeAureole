from datetime import date
from timeutils import now_utc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user

router = APIRouter(prefix="/api/absences", tags=["Absences"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=schemas.AbsenceResponse, status_code=status.HTTP_201_CREATED)
def creer_absence(payload: schemas.AbsenceCreate, db: Session = Depends(get_db)):
    if not db.query(models.Eleves).filter(models.Eleves.matricule == payload.matricule_eleve).first():
        raise HTTPException(status_code=404, detail="Élève introuvable")
    if payload.id_cours and not db.query(models.Cours).filter(models.Cours.id == payload.id_cours).first():
        raise HTTPException(status_code=404, detail="Cours introuvable")

    nouvelle_absence = models.Absences(**payload.model_dump())
    db.add(nouvelle_absence)
    db.commit()
    db.refresh(nouvelle_absence)
    return nouvelle_absence


def _appliquer_filtres_absences(query, classe_id, matricule_eleve, id_cours, date_debut, date_fin, justifiee, q, annee_id=None):
    if matricule_eleve:
        query = query.filter(models.Absences.matricule_eleve == matricule_eleve)
    if id_cours:
        query = query.filter(models.Absences.id_cours == id_cours)
    if classe_id:
        # FIX : si annee_id est fourni, on filtre directement par inscription
        # sur cette année (précis et rapide). Sinon, on retombe sur le filtre
        # par date (ancien comportement) pour rester rétrocompatible.
        if annee_id is not None:
            query = query.join(
                models.Inscriptions,
                and_(
                    models.Inscriptions.matricule_eleve == models.Absences.matricule_eleve,
                    models.Inscriptions.id_classe == classe_id,
                    models.Inscriptions.id_annee_scolaire == annee_id,
                ),
            )
        else:
            # Filtre « par classe » sur la classe de l'INSCRIPTION de l'année scolaire
            # qui couvre la date de l'absence — jamais Eleves.classe_id (classe
            # actuelle de l'élève : fausse, voire vide, pour les années antérieures).
            query = query.join(
                models.Inscriptions,
                and_(
                    models.Inscriptions.matricule_eleve == models.Absences.matricule_eleve,
                    models.Inscriptions.id_classe == classe_id,
                ),
            ).join(
                models.AnneesScolaires,
                models.AnneesScolaires.id == models.Inscriptions.id_annee_scolaire,
            ).filter(
                models.AnneesScolaires.date_debut <= models.Absences.date_absence,
                models.Absences.date_absence <= models.AnneesScolaires.date_fin,
            )
    if date_debut:
        query = query.filter(models.Absences.date_absence >= date_debut)
    if date_fin:
        query = query.filter(models.Absences.date_absence <= date_fin)
    if justifiee is not None:
        query = query.filter(models.Absences.justifiee.is_(justifiee))
    if q:
        like = f"%{q}%"
        query = query.join(models.Eleves, models.Eleves.matricule == models.Absences.matricule_eleve)
        query = query.outerjoin(models.Cours, models.Cours.id == models.Absences.id_cours)
        query = query.filter(or_(
            models.Eleves.nom.ilike(like),
            models.Eleves.prenom.ilike(like),
            models.Absences.matricule_eleve.ilike(like),
            models.Cours.nom.ilike(like),
        ))
    return query


@router.get("/", response_model=List[schemas.AbsenceResponse])
def get_all_absences(
    classe_id: Optional[int] = None,
    matricule_eleve: Optional[str] = None,
    id_cours: Optional[int] = None,
    annee_id: Optional[int] = Query(None, description="Filtre par année scolaire (recommandé avec classe_id)"),
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    justifiee: Optional[bool] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_absences(
        db.query(models.Absences).options(joinedload(models.Absences.eleve), joinedload(models.Absences.cours)),
        classe_id, matricule_eleve, id_cours, date_debut, date_fin, justifiee, q, annee_id=annee_id,
    )
    return query.order_by(models.Absences.date_absence.desc()).offset(skip).limit(limit).all()


@router.get("/compte")
def compter_absences(
    classe_id: Optional[int] = None,
    matricule_eleve: Optional[str] = None,
    id_cours: Optional[int] = None,
    annee_id: Optional[int] = Query(None, description="Filtre par année scolaire (recommandé avec classe_id)"),
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    justifiee: Optional[bool] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = _appliquer_filtres_absences(
        db.query(models.Absences), classe_id, matricule_eleve, id_cours, date_debut, date_fin, justifiee, q, annee_id=annee_id,
    )
    return {"total": query.count()}


@router.get("/alertes", response_model=List[schemas.AlerteAbsenceEleve])
def get_alertes_absences(seuil: int = 3, db: Session = Depends(get_db)):
    """Élèves ayant dépassé le seuil d'absences NON justifiées."""
    resultats = (
        db.query(
            models.Absences.matricule_eleve,
            models.Eleves.nom,
            models.Eleves.prenom,
            func.count(models.Absences.id).label("nb"),
        )
        .join(models.Eleves, models.Eleves.matricule == models.Absences.matricule_eleve)
        .filter(models.Absences.justifiee.is_(False))
        .group_by(models.Absences.matricule_eleve, models.Eleves.nom, models.Eleves.prenom)
        .having(func.count(models.Absences.id) >= seuil)
        .all()
    )
    return [
        schemas.AlerteAbsenceEleve(
            matricule_eleve=matricule, nom=nom, prenom=prenom, nb_absences_non_justifiees=nb
        )
        for matricule, nom, prenom, nb in resultats
    ]


@router.get("/{absence_id}", response_model=schemas.AbsenceResponse)
def get_absence(absence_id: int, db: Session = Depends(get_db)):
    absence = db.query(models.Absences).options(joinedload(models.Absences.eleve)).filter(models.Absences.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence introuvable")
    return absence


@router.put("/{absence_id}", response_model=schemas.AbsenceResponse)
def update_absence(absence_id: int, payload: schemas.AbsenceCreate, db: Session = Depends(get_db)):
    absence = db.query(models.Absences).filter(models.Absences.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence introuvable")
    for key, value in payload.model_dump().items():
        setattr(absence, key, value)
    db.commit()
    db.refresh(absence)
    return absence


@router.patch("/{absence_id}/justifier", response_model=schemas.AbsenceResponse)
def justifier_absence(absence_id: int, payload: schemas.AbsenceJustifierRequest, db: Session = Depends(get_db)):
    """Workflow dédié et tracé de justification (qui, quand), séparé de la
    modification générique pour garder un historique fiable."""
    absence = db.query(models.Absences).filter(models.Absences.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence introuvable")

    absence.justifiee = payload.justifiee
    absence.motif = payload.motif
    absence.justifiee_par_id = payload.utilisateur_id
    absence.date_justification = now_utc()

    db.commit()
    db.refresh(absence)
    return absence


@router.delete("/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_absence(absence_id: int, db: Session = Depends(get_db)):
    absence = db.query(models.Absences).filter(models.Absences.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence introuvable")
    db.delete(absence)
    db.commit()
    return None
