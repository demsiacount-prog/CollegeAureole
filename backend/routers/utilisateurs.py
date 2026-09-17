"""Gestion des comptes utilisateurs (création, statut, mot de passe, suppression).

Historiquement seul le compte créé à l'initialisation existe. Ce router permet
d'ajouter de nouveaux utilisateurs depuis les Paramètres, de les activer /
désactiver, de réinitialiser leur mot de passe et de les supprimer.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from hashing import hash_password
from security import get_current_user
from exceptions import (
    ForbiddenError,
    ValidationError,
)
from validators import assert_found, assert_unique
import models
import schemas


router = APIRouter(prefix="/api/utilisateurs", tags=["Utilisateurs"], dependencies=[Depends(get_current_user)])

ROLES_VALUES = {"ADMIN", "DIRECTEUR", "SECRETAIRE", "ENSEIGNANT", "COMPTABLE"}


def _valider_mot_de_passe(mot_de_passe: str) -> None:
    if not mot_de_passe or len(mot_de_passe) < 8:
        raise ValidationError("mot_de_passe", "Le mot de passe doit contenir au moins 8 caractères")


def _valider_role(role: str) -> str:
    role_normalise = role.strip().upper()
    if role_normalise not in ROLES_VALUES:
        raise ValidationError(
            "role",
            "Rôle invalide. Valeurs acceptées : " + ", ".join(sorted(ROLES_VALUES)),
        )
    return role_normalise


@router.get("/", response_model=List[schemas.UtilisateurResponse])
def lister_utilisateurs(db: Session = Depends(get_db)):
    return (
        db.query(models.Utilisateurs)
        .order_by(models.Utilisateurs.created_at, models.Utilisateurs.id)
        .all()
    )


@router.post("/", response_model=schemas.UtilisateurResponse, status_code=status.HTTP_201_CREATED)
def creer_utilisateur(payload: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    _valider_mot_de_passe(payload.mot_de_passe)
    role = _valider_role(payload.role)
    assert_unique(
        db,
        db.query(models.Utilisateurs).filter(models.Utilisateurs.email == payload.email).first(),
        "Utilisateur",
        "email",
        payload.email,
    )
    utilisateur = models.Utilisateurs(
        nom=payload.nom,
        prenom=payload.prenom,
        email=payload.email,
        mot_de_passe=hash_password(payload.mot_de_passe),
        role=role,
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


@router.patch("/{utilisateur_id}/statut", response_model=schemas.UtilisateurResponse)
def modifier_statut_utilisateur(
    utilisateur_id: int,
    payload: schemas.UtilisateurStatutUpdate,
    db: Session = Depends(get_db),
    utilisateur_courant: models.Utilisateurs = Depends(get_current_user),
):
    if utilisateur_courant.id == utilisateur_id:
        raise ForbiddenError("Vous ne pouvez pas désactiver votre propre compte")
    utilisateur = assert_found(
        db.query(models.Utilisateurs).filter(models.Utilisateurs.id == utilisateur_id).first(),
        "Utilisateur",
        str(utilisateur_id),
    )
    utilisateur.actif = payload.actif
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


@router.put("/{utilisateur_id}/mot-de-passe", status_code=status.HTTP_204_NO_CONTENT)
def reinitialiser_mot_de_passe(
    utilisateur_id: int,
    payload: schemas.UtilisateurReinitialiserMotDePasse,
    db: Session = Depends(get_db),
):
    _valider_mot_de_passe(payload.nouveau_mot_de_passe)
    utilisateur = assert_found(
        db.query(models.Utilisateurs).filter(models.Utilisateurs.id == utilisateur_id).first(),
        "Utilisateur",
        str(utilisateur_id),
    )
    utilisateur.mot_de_passe = hash_password(payload.nouveau_mot_de_passe)
    db.commit()
    return None


@router.delete("/{utilisateur_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_utilisateur(
    utilisateur_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: models.Utilisateurs = Depends(get_current_user),
):
    if utilisateur_courant.id == utilisateur_id:
        raise ForbiddenError("Vous ne pouvez pas supprimer votre propre compte")
    utilisateur = assert_found(
        db.query(models.Utilisateurs).filter(models.Utilisateurs.id == utilisateur_id).first(),
        "Utilisateur",
        str(utilisateur_id),
    )
    db.delete(utilisateur)
    db.commit()
    return None