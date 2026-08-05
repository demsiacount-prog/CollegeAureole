"""
Gestionnaire pour les erreurs de base de données.
Convertit les exceptions SQLAlchemy en exceptions métier claires.
"""

from sqlalchemy.exc import IntegrityError, DataError
from exceptions import ConstraintError, ValidationError, InternalError


def handle_db_error(error: Exception, operation: str = "opération"):
    """
    Convertit les erreurs de base de données en exceptions métier.
    
    Args:
        error: Exception levée par SQLAlchemy
        operation: Description de l'opération qui a échoué (ex. "création de l'élève")
    
    Raises:
        ConstraintError: Violation de contrainte (clé étrangère, unicité, etc.)
        ValidationError: Données invalides
        InternalError: Erreur serveur interne
    """
    if isinstance(error, IntegrityError):
        # Extraire le message original
        orig_msg = str(error.orig).lower()
        
        # Violations de contrainte de clé étrangère
        if "foreign key" in orig_msg or "fk_" in orig_msg:
            raise ConstraintError(
                "Référence invalide : la ressource liée n'existe pas",
                {"operation": operation, "type": "foreign_key"}
            )
        
        # Violations d'unicité
        if "unique" in orig_msg:
            raise ConstraintError(
                "Doublon : cette valeur existe déjà",
                {"operation": operation, "type": "unique"}
            )
        
        # Violations de NOT NULL
        if "not null" in orig_msg:
            raise ConstraintError(
                "Champ requis manquant",
                {"operation": operation, "type": "not_null"}
            )
        
        # Violation de contrainte générique
        raise ConstraintError(
            f"Violation de contrainte lors de {operation}",
            {"operation": operation, "type": "generic"}
        )
    
    elif isinstance(error, DataError):
        # Format de données invalide
        raise ValidationError(
            "données",
            f"Format de données invalide : {str(error.orig)}"
        )
    
    else:
        # Erreur inconnue
        raise InternalError(operation, {"error_type": type(error).__name__})


def safe_db_operation(func, *args, operation: str = "opération", **kwargs):
    """
    Wrapper pour exécuter une opération DB et gérer les erreurs.
    
    Usage:
        eleve = safe_db_operation(
            db.add,
            new_eleve,
            operation="création de l'élève"
        )
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_db_error(e, operation)
