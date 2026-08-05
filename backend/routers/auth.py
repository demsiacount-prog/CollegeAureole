from datetime import timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from hashing import hash_password, verify_password
from security import create_access_token, get_current_user
from timeutils import now_utc
from exceptions import (
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from validators import assert_found
import models
import schemas


def _valider_mot_de_passe(mot_de_passe: str, *, champ: str) -> None:
    if not mot_de_passe or len(mot_de_passe) < 8:
        raise ValidationError(
            champ.lower(),
            f"{champ} doit contenir au moins 8 caractères.",
        )

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

MAX_TENTATIVES = 5
DUREE_VERROUILLAGE_MINUTES = 15


@router.post("/connexion", response_model=schemas.TokenResponse)
def connexion(payload: schemas.UtilisateurConnexion, db: Session = Depends(get_db)):
    _valider_mot_de_passe(payload.mot_de_passe, champ="Le mot de passe")
    utilisateur = db.query(models.Utilisateurs).filter(models.Utilisateurs.email == payload.email).first()

    if not utilisateur:
        raise UnauthorizedError("Email ou mot de passe incorrect.")

    now = now_utc()
    if utilisateur.verrouille_jusqua and utilisateur.verrouille_jusqua.replace(tzinfo=None) > now.replace(tzinfo=None):
        minutes_restantes = int((utilisateur.verrouille_jusqua - now.replace(tzinfo=None)).total_seconds() // 60) + 1
        raise ForbiddenError(f"Compte temporairement verrouillé. Réessayez dans {minutes_restantes} min.")

    if not utilisateur.actif:
        raise ForbiddenError("Ce compte a été désactivé.")

    if not verify_password(payload.mot_de_passe, utilisateur.mot_de_passe):
        utilisateur.tentatives_echouees += 1
        if utilisateur.tentatives_echouees >= MAX_TENTATIVES:
            utilisateur.verrouille_jusqua = now_utc().replace(tzinfo=None) + timedelta(minutes=DUREE_VERROUILLAGE_MINUTES)
            utilisateur.tentatives_echouees = 0
        db.commit()
        raise UnauthorizedError("Email ou mot de passe incorrect.")

    utilisateur.tentatives_echouees = 0
    utilisateur.verrouille_jusqua = None
    db.commit()

    token = create_access_token(utilisateur_id=utilisateur.id, role=utilisateur.role.value)
    return schemas.TokenResponse(access_token=token, utilisateur=utilisateur)


@router.get("/moi", response_model=schemas.UtilisateurResponse)
def qui_suis_je(utilisateur_courant: models.Utilisateurs = Depends(get_current_user)):
    """Permet au frontend de vérifier la validité du token et de récupérer le profil courant."""
    return utilisateur_courant


@router.put("/utilisateurs/{utilisateur_id}/mot-de-passe", status_code=status.HTTP_204_NO_CONTENT)
def changer_mot_de_passe(
    utilisateur_id: int,
    payload: schemas.UtilisateurChangerMotDePasse,
    db: Session = Depends(get_db),
    utilisateur_courant: models.Utilisateurs = Depends(get_current_user),
):
    # Seul le titulaire du compte ou un admin peut changer ce mot de passe.
    if utilisateur_courant.id != utilisateur_id and utilisateur_courant.role.value != "admin":
        raise ForbiddenError("Vous ne pouvez modifier que votre propre mot de passe.")

    utilisateur = assert_found(
        db.query(models.Utilisateurs).filter(models.Utilisateurs.id == utilisateur_id).first(),
        "Utilisateur",
        str(utilisateur_id),
    )
    if not verify_password(payload.ancien_mot_de_passe, utilisateur.mot_de_passe):
        raise UnauthorizedError("Ancien mot de passe incorrect.")
    _valider_mot_de_passe(payload.nouveau_mot_de_passe, champ="Le nouveau mot de passe")
    utilisateur.mot_de_passe = hash_password(payload.nouveau_mot_de_passe)
    db.commit()
    return None
