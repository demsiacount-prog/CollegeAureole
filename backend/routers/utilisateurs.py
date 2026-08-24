from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
from hashing import hash_password
from security import require_role

# Gestion des comptes d'administration : réservée aux admins (création de
# comptes directeur/comptable, changement de rôle, désactivation...).
router = APIRouter(
    prefix="/api/utilisateurs",
    tags=["Utilisateurs"],
    dependencies=[Depends(require_role("admin"))],
)


@router.post(
    "/",
    response_model=schemas.UtilisateurResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte d'administration (admin, directeur ou comptable)",
)
def inscription(payload: schemas.UtilisateurInscription, db: Session = Depends(get_db)):
    email_existant = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.email == payload.email
    ).first()
    if email_existant:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    nouvel_utilisateur = models.Utilisateurs(
        nom=payload.nom,
        prenom=payload.prenom,
        email=payload.email,
        mot_de_passe=hash_password(payload.mot_de_passe),
        role=payload.role,
    )
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    return nouvel_utilisateur


@router.get("/", response_model=List[schemas.UtilisateurResponse])
def get_all_utilisateurs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Utilisateurs)
        .order_by(models.Utilisateurs.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{utilisateur_id}", response_model=schemas.UtilisateurResponse)
def get_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.id == utilisateur_id
    ).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return utilisateur


@router.put("/{utilisateur_id}", response_model=schemas.UtilisateurResponse)
def update_utilisateur(
    utilisateur_id: int,
    payload: schemas.UtilisateurUpdate,
    db: Session = Depends(get_db),
):
    utilisateur = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.id == utilisateur_id
    ).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    email_existant = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.email == payload.email,
        models.Utilisateurs.id != utilisateur_id,
    ).first()
    if email_existant:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # exclude_unset : un PUT partiel n'écrase plus silencieusement `actif`
    # (qui avait une valeur par défaut True côté schéma) sur les champs omis.
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(utilisateur, key, value)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


@router.delete("/{utilisateur_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.id == utilisateur_id
    ).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(utilisateur)
    db.commit()
    return None
