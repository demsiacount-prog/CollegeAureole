"""
Gestion centralisée des exceptions et erreurs de l'API.
Fournit des classes d'exception cohérentes pour tous les cas d'erreur.
"""

from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Format standard de réponse d'erreur."""
    error_code: str
    message: str
    details: dict | None = None


class AureoleException(HTTPException):
    """Classe de base pour toutes les exceptions métier."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "details": details,
            },
        )


class NotFoundError(AureoleException):
    """Ressource non trouvée."""

    def __init__(self, resource_type: str, identifier: str = ""):
        msg = f"{resource_type} non trouvée"
        if identifier:
            msg += f" : {identifier}"
        super().__init__(
            error_code="NOT_FOUND",
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationError(AureoleException):
    """Données invalides."""

    def __init__(self, field: str, reason: str):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=f"Données invalides : {field}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field, "reason": reason},
        )


class DuplicateError(AureoleException):
    """Doublon détecté."""

    def __init__(self, resource_type: str, field: str, value: str):
        super().__init__(
            error_code="DUPLICATE_ERROR",
            message=f"{resource_type} en doublon",
            status_code=status.HTTP_409_CONFLICT,
            details={"field": field, "value": value},
        )


class UnauthorizedError(AureoleException):
    """Authentification requise."""

    def __init__(self, reason: str = "Authentification requise"):
        super().__init__(
            error_code="UNAUTHORIZED",
            message=reason,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(AureoleException):
    """Accès refusé."""

    def __init__(self, reason: str = "Vous n'avez pas la permission d'accéder à cette ressource"):
        super().__init__(
            error_code="FORBIDDEN",
            message=reason,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(AureoleException):
    """Conflit d'état."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            error_code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class InternalError(AureoleException):
    """Erreur interne du serveur."""

    def __init__(self, operation: str, details: dict | None = None):
        super().__init__(
            error_code="INTERNAL_ERROR",
            message=f"Erreur lors de {operation}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class InvalidStateError(AureoleException):
    """État invalide pour l'opération demandée."""

    def __init__(self, current_state: str, required_state: str):
        super().__init__(
            error_code="INVALID_STATE",
            message=f"État invalide : {current_state}",
            status_code=status.HTTP_409_CONFLICT,
            details={
                "current_state": current_state,
                "required_state": required_state,
            },
        )


class BusinessLogicError(AureoleException):
    """Violation de règle métier."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            error_code="BUSINESS_LOGIC_ERROR",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ConstraintError(AureoleException):
    """Violation de contrainte de données."""

    def __init__(self, constraint: str, details: dict | None = None):
        super().__init__(
            error_code="CONSTRAINT_ERROR",
            message=f"Violation de contrainte : {constraint}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )
