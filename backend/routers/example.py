"""
Exemple de gestion des erreurs dans un router Aureole.
Ce fichier démontre les bonnes pratiques pour gérer les erreurs.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from security import get_current_user
from exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    ForbiddenError,
    InvalidStateError,
    BusinessLogicError,
)
from validators import (
    assert_found,
    assert_unique,
    assert_valid_email,
    assert_user_can_write,
    assert_active_school_year,
)
from db_errors import handle_db_error
import models
import schemas


router = APIRouter(prefix="/api/example", tags=["Exemple"])


@router.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateurs = Depends(get_current_user),
):
    """
    Exemple de création d'utilisateur avec gestion complète des erreurs.
    """
    # 1. Vérifier les permissions
    assert_user_can_write(current_user, ["admin"])
    
    # 2. Valider les données
    assert_valid_email(payload.email)
    if len(payload.nom) < 2:
        raise ValidationError("nom", "Le nom doit contenir au moins 2 caractères")
    
    # 3. Vérifier les doublons
    existing = db.query(models.Utilisateurs).filter_by(email=payload.email).first()
    assert_unique(db, existing, "Utilisateur", "email", payload.email)
    
    # 4. Vérifier les ressources liées
    if payload.role_id:
        role = db.query(models.Roles).filter_by(id=payload.role_id).first()
        assert_found(role, "Rôle", str(payload.role_id))
    
    # 5. Créer la ressource
    try:
        user = models.Utilisateurs(**payload.dict())
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        handle_db_error(e, "création de l'utilisateur")
    
    return user


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Exemple de récupération avec gestion des erreurs 404.
    """
    user = db.query(models.Utilisateurs).filter_by(id=user_id).first()
    return assert_found(user, "Utilisateur", str(user_id))


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateurs = Depends(get_current_user),
):
    """
    Exemple de mise à jour avec vérification de permissions et de doublons.
    """
    # Vérifier les permissions : seul l'admin ou le titulaire peut modifier
    if current_user.id != user_id and current_user.role.value != "admin":
        raise ForbiddenError("Vous ne pouvez modifier que votre propre profil")
    
    user = db.query(models.Utilisateurs).filter_by(id=user_id).first()
    assert_found(user, "Utilisateur", str(user_id))
    
    # Si l'email change, vérifier qu'il n'existe pas déjà
    if payload.email and payload.email != user.email:
        assert_valid_email(payload.email)
        existing = db.query(models.Utilisateurs).filter_by(email=payload.email).first()
        assert_unique(db, existing, "Utilisateur", "email", payload.email)
    
    # Mettre à jour les champs
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(user, key, value)
    
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        handle_db_error(e, "mise à jour de l'utilisateur")
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utilisateurs = Depends(get_current_user),
):
    """
    Exemple de suppression avec cas de conflit métier.
    """
    # Vérifier les permissions
    assert_user_can_write(current_user, ["admin"])
    
    user = db.query(models.Utilisateurs).filter_by(id=user_id).first()
    assert_found(user, "Utilisateur", str(user_id))
    
    # Vérifier qu'on ne supprime pas le dernier admin
    if user.role.value == "admin":
        other_admins = db.query(models.Utilisateurs).filter(
            models.Utilisateurs.role == "admin",
            models.Utilisateurs.id != user_id,
        ).count()
        if other_admins == 0:
            raise BusinessLogicError(
                "Impossible de supprimer le dernier administrateur",
                {"user_id": user_id, "role": "admin"}
            )
    
    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        handle_db_error(e, "suppression de l'utilisateur")
    
    return None


@router.post("/users/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utilisateurs = Depends(get_current_user),
):
    """
    Exemple de changement d'état avec vérification d'état invalide.
    """
    assert_user_can_write(current_user, ["admin"])
    
    user = db.query(models.Utilisateurs).filter_by(id=user_id).first()
    assert_found(user, "Utilisateur", str(user_id))
    
    if user.actif:
        raise InvalidStateError("actif", "inactif")
    
    user.actif = True
    db.commit()
    
    return None
