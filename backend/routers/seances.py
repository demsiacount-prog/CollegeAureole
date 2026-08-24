from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/seances", tags=["Séances"], dependencies=[Depends(get_current_user)])


def _chevauchement(deb1, fin1, deb2, fin2) -> bool:
    return deb1 < fin2 and deb2 < fin1


def _verifier_conflits(db: Session, payload, id_seance_exclue: Optional[int] = None):
    cours = db.query(models.Cours).filter(models.Cours.id == payload.id_cours).first()
    if not cours:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    classe = db.query(models.Classes).filter(models.Classes.id == payload.id_classe).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    if payload.id_salle:
        salle = db.query(models.Salles).filter(models.Salles.id == payload.id_salle).first()
        if not salle:
            raise HTTPException(status_code=404, detail="Salle introuvable")
        if salle.capacite is not None:
            effectif = db.query(models.Eleves).filter(
                models.Eleves.classe_id == payload.id_classe,
                models.Eleves.statut == "actif",
            ).count()
            if effectif > salle.capacite:
                raise HTTPException(
                    status_code=400,
                    detail="Capacité insuffisante",
                )

    seances_du_jour = db.query(models.Seances).filter(
        models.Seances.id_annee_scolaire == payload.id_annee_scolaire,
        models.Seances.jour_semaine == payload.jour_semaine,
        models.Seances.id != (id_seance_exclue or -1),
    ).all()

    conflits = []
    for s in seances_du_jour:
        if not _chevauchement(payload.heure_debut, payload.heure_fin, s.heure_debut, s.heure_fin):
            continue
        if s.id_classe == payload.id_classe:
            conflits.append("Conflit de classe")
        if cours.matricule_enseignant and s.cours and s.cours.matricule_enseignant == cours.matricule_enseignant:
            conflits.append("Conflit d'enseignant")
        if payload.id_salle and s.id_salle == payload.id_salle:
            conflits.append("Conflit de salle")

    if conflits:
        raise HTTPException(status_code=409, detail=" | ".join(sorted(set(conflits))))


@router.post("/", response_model=schemas.SeanceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_seance(payload: schemas.SeanceCreate, db: Session = Depends(get_db)):
    _verifier_conflits(db, payload)
    seance = models.Seances(**payload.model_dump())
    db.add(seance)
    db.commit()
    db.refresh(seance)
    return seance


@router.get("/", response_model=List[schemas.SeanceDetailResponse])
def get_all_seances(
    id_annee_scolaire: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=300, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.Seances).options(
        joinedload(models.Seances.cours), joinedload(models.Seances.classe), joinedload(models.Seances.salle)
    )
    if id_annee_scolaire:
        query = query.filter(models.Seances.id_annee_scolaire == id_annee_scolaire)
    return query.order_by(models.Seances.id).offset(skip).limit(limit).all()


@router.get("/classe/{id_classe}", response_model=List[schemas.SeanceDetailResponse])
def get_seances_classe(id_classe: int, id_annee_scolaire: int, db: Session = Depends(get_db)):
    return db.query(models.Seances).options(
        joinedload(models.Seances.cours), joinedload(models.Seances.classe), joinedload(models.Seances.salle)
    ).filter(
        models.Seances.id_classe == id_classe,
        models.Seances.id_annee_scolaire == id_annee_scolaire,
    ).all()


@router.get("/enseignant/{matricule}", response_model=List[schemas.SeanceDetailResponse])
def get_seances_enseignant(matricule: str, id_annee_scolaire: int, db: Session = Depends(get_db)):
    return db.query(models.Seances).join(models.Cours).options(
        joinedload(models.Seances.cours), joinedload(models.Seances.classe), joinedload(models.Seances.salle)
    ).filter(
        models.Cours.matricule_enseignant == matricule,
        models.Seances.id_annee_scolaire == id_annee_scolaire,
    ).all()


@router.put("/{seance_id}", response_model=schemas.SeanceResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_seance(seance_id: int, payload: schemas.SeanceUpdate, db: Session = Depends(get_db)):
    seance = db.query(models.Seances).filter(models.Seances.id == seance_id).first()
    if not seance:
        raise HTTPException(status_code=404, detail="Séance introuvable")
    _verifier_conflits(db, payload, id_seance_exclue=seance_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(seance, key, value)
    db.commit()
    db.refresh(seance)
    return seance


@router.delete("/{seance_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_seance(seance_id: int, db: Session = Depends(get_db)):
    seance = db.query(models.Seances).filter(models.Seances.id == seance_id).first()
    if not seance:
        raise HTTPException(status_code=404, detail="Séance introuvable")
    db.delete(seance)
    db.commit()
    return None
