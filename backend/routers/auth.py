from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from hashing import hash_password, verify_password
from security import create_access_token, get_current_user
import models
import schemas

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

MAX_TENTATIVES = 5
DUREE_VERROUILLAGE_MINUTES = 15


@router.post("/connexion", response_model=schemas.TokenResponse)
def connexion(payload: schemas.UtilisateurConnexion, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateurs).filter(models.Utilisateurs.email == payload.email).first()

    if not utilisateur:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    if utilisateur.verrouille_jusqua and utilisateur.verrouille_jusqua > datetime.utcnow():
        minutes_restantes = int((utilisateur.verrouille_jusqua - datetime.utcnow()).total_seconds() // 60) + 1
        raise HTTPException(status_code=403, detail=f"Compte temporairement verrouillé. Réessayez dans {minutes_restantes} min.")

    if not utilisateur.actif:
        raise HTTPException(status_code=403, detail="Ce compte a été désactivé.")

    if not verify_password(payload.mot_de_passe, utilisateur.mot_de_passe):
        utilisateur.tentatives_echouees += 1
        if utilisateur.tentatives_echouees >= MAX_TENTATIVES:
            utilisateur.verrouille_jusqua = datetime.utcnow() + timedelta(minutes=DUREE_VERROUILLAGE_MINUTES)
            utilisateur.tentatives_echouees = 0
        db.commit()
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

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
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que votre propre mot de passe.")

    utilisateur = db.query(models.Utilisateurs).filter(models.Utilisateurs.id == utilisateur_id).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not verify_password(payload.ancien_mot_de_passe, utilisateur.mot_de_passe):
        raise HTTPException(status_code=401, detail="Ancien mot de passe incorrect.")
    utilisateur.mot_de_passe = hash_password(payload.nouveau_mot_de_passe)
    db.commit()
    return None
