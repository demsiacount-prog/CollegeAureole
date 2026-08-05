"""
Utilitaires de validation et de vérification pour les routers.
Centralise la logique commune de validation métier.
"""

from sqlalchemy.orm import Session
from exceptions import (
    NotFoundError,
    DuplicateError,
    ValidationError,
    ForbiddenError,
    InvalidStateError,
)
import models


def assert_found(obj, resource_type: str, identifier: str = ""):
    """Vérifie qu'une ressource a été trouvée."""
    if obj is None:
        raise NotFoundError(resource_type, identifier)
    return obj


def assert_unique(
    db: Session,
    query_result,
    resource_type: str,
    field: str,
    value: str,
):
    """Vérifie l'unicité d'un champ."""
    if query_result is not None:
        raise DuplicateError(resource_type, field, value)


def assert_valid_email(email: str):
    """Valide le format d'un email."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError("email", "Format d'email invalide")


def assert_valid_phone(phone: str):
    """Valide le format d'un numéro de téléphone."""
    import re

    pattern = r"^\+?[\d\s\-()]{7,}$"
    if not re.match(pattern, phone):
        raise ValidationError("telephone", "Numéro de téléphone invalide")


def assert_active_school_year(db: Session):
    """Récupère et vérifie qu'une année scolaire est active."""
    annee = db.query(models.AnneesScolaires).filter(
        models.AnneesScolaires.active == True
    ).first()
    return assert_found(annee, "Année scolaire active")


def assert_user_can_write(user, required_roles: list[str]):
    """Vérifie que l'utilisateur a les permissions d'écriture."""
    if user.role not in required_roles:
        raise ForbiddenError(
            f"Rôle insuffisant. Rôles requis : {', '.join(required_roles)}"
        )


def assert_valid_status(status_value: str, valid_statuses: list[str]):
    """Valide qu'un statut fait partie des valeurs acceptées."""
    if status_value not in valid_statuses:
        raise ValidationError(
            "status",
            f"Statut invalide. Valeurs acceptées : {', '.join(valid_statuses)}",
        )
