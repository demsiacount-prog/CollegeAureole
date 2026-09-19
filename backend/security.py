# core/security.py
# Nécessite : pip install pyjwt
import logging
import os
from datetime import timedelta

import jwt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from exceptions import ForbiddenError, UnauthorizedError
import models
from timeutils import now_utc

logger = logging.getLogger("college_aureole")

_DEFAULT_SECRET = "changez-moi-en-production"
# À définir en variable d'environnement en production (ne jamais committer la vraie valeur)
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", _DEFAULT_SECRET).strip()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8h

_ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").strip().lower()

if not SECRET_KEY:
    raise RuntimeError("Clé JWT manquante")

if _ENVIRONMENT == "production" and (SECRET_KEY == _DEFAULT_SECRET or len(SECRET_KEY) < 32):
    # En production, un secret par défaut ou trop court rendrait les JWT
    # falsifiables. On refuse de démarrer plutôt que de servir une API non sécurisée.
    raise RuntimeError("Clé JWT invalide")
elif SECRET_KEY == _DEFAULT_SECRET:
    logger.warning(
        "JWT_SECRET_KEY n'est pas défini : utilisation de la valeur par défaut "
        "'%s', à usage dev/démo uniquement. Définissez JWT_SECRET_KEY avant "
        "tout déploiement réel.", _DEFAULT_SECRET,
    )

bearer_scheme = HTTPBearer()


def create_access_token(utilisateur_id: int, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    now = now_utc()
    payload = {
        "sub": str(utilisateur_id),
        "exp": now + timedelta(minutes=expires_minutes),
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Session expirée, veuillez vous reconnecter.")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Token invalide")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.Utilisateurs:
    payload = decode_access_token(credentials.credentials)
    utilisateur = db.query(models.Utilisateurs).filter(models.Utilisateurs.id == int(payload["sub"])).first()
    if not utilisateur or not utilisateur.actif:
        raise UnauthorizedError("Compte invalide")
    return utilisateur


def require_admin(
    utilisateur_courant: models.Utilisateurs = Depends(get_current_user),
) -> models.Utilisateurs:
    """Réserve l'accès aux seuls comptes administrateurs.

    Les rôles sont portés par le champ `role` du compte. Toute opération de
    gestion sensible (comptes, purge de base, export complet, paramètres,
    cycle des années scolaires) doit passer par cette dépendance : l'authentification
    seule (get_current_user) ne confère aucun droit d'administration.
    """
    if (utilisateur_courant.role or "").strip().upper() != "ADMIN":
        raise ForbiddenError("Action réservée à l'administrateur")
    return utilisateur_courant
