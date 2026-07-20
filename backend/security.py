# core/security.py
# Nécessite : pip install pyjwt
import logging
import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
import models

logger = logging.getLogger("college_aureole")

_DEFAULT_SECRET = "changez-moi-en-production"
# À définir en variable d'environnement en production (ne jamais committer la vraie valeur)
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", _DEFAULT_SECRET)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8h

_ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").strip().lower()

if _ENVIRONMENT == "production" and (SECRET_KEY == _DEFAULT_SECRET or len(SECRET_KEY) < 32):
    # En production, un secret par défaut ou trop court rendrait les JWT
    # falsifiables. On refuse de démarrer plutôt que de servir une API non sécurisée.
    raise RuntimeError(
        "JWT_SECRET_KEY manquant ou trop faible pour ENVIRONMENT=production. "
        "Définissez une valeur aléatoire d'au moins 32 caractères "
        "(par ex. `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`)."
    )
elif SECRET_KEY == _DEFAULT_SECRET:
    logger.warning(
        "JWT_SECRET_KEY n'est pas défini : utilisation de la valeur par défaut "
        "'%s', à usage dev/démo uniquement. Définissez JWT_SECRET_KEY avant "
        "tout déploiement réel.", _DEFAULT_SECRET,
    )

bearer_scheme = HTTPBearer()


def create_access_token(utilisateur_id: int, role: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    payload = {
        "sub": str(utilisateur_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expirée, veuillez vous reconnecter.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide.")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.Utilisateurs:
    payload = decode_access_token(credentials.credentials)
    utilisateur = db.query(models.Utilisateurs).filter(models.Utilisateurs.id == int(payload["sub"])).first()
    if not utilisateur or not utilisateur.actif:
        raise HTTPException(status_code=401, detail="Utilisateur invalide ou désactivé.")
    return utilisateur


def require_role(*roles_autorises: str):
    """Dépendance à ajouter sur une route pour la restreindre à certains rôles.
    Exemple : @router.get(..., dependencies=[Depends(require_role("admin", "directeur"))])"""

    def dependance(utilisateur: models.Utilisateurs = Depends(get_current_user)):
        if utilisateur.role.value not in roles_autorises and utilisateur.role not in roles_autorises:
            raise HTTPException(status_code=403, detail="Accès refusé pour ce rôle.")
        return utilisateur

    return dependance
