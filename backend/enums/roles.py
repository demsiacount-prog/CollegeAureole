import enum


class RoleUtilisateur(str, enum.Enum):
    """Rôles possibles pour les comptes d'administration de l'établissement."""

    ADMIN = "admin"
    DIRECTEUR = "directeur"
    COMPTABLE = "comptable"
