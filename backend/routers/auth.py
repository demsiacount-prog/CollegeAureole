import hashlib
import secrets
import time
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from hashing import hash_password, verify_password
from ratelimit import limiter, L_CONNEXION
from security import create_access_token, get_current_user
from timeutils import now_utc
from exceptions import (
    UnauthorizedError,
    ForbiddenError,
    ValidationError,
)
from validators import assert_found
from services import mail as mail_service
from schemas.auth import (
    MotDePasseOublieRequest,
    MotDePasseOublieResponse,
    ReinitialiserMotDePasseRequest,
    ReinitialiserMotDePasseResponse,
)
import models
import schemas


def _valider_mot_de_passe(mot_de_passe: str, *, champ: str) -> None:
    if not mot_de_passe or len(mot_de_passe) < 8:
        raise ValidationError(
            champ.lower(),
            f"{champ} doit contenir au moins 8 caractères",
        )

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

MAX_TENTATIVES = 5
DUREE_VERROUILLAGE_MINUTES = 15

_DUREE_JETON_MINUTES = 30
_DELAI_ANTI_ENUMERATION = 0.4  # seconde : réponse muette identique en durée


@router.post("/connexion", response_model=schemas.TokenResponse, dependencies=[limiter("connexion", *L_CONNEXION)])
def connexion(payload: schemas.UtilisateurConnexion, db: Session = Depends(get_db)):
    _valider_mot_de_passe(payload.mot_de_passe, champ="Le mot de passe")
    utilisateur = db.query(models.Utilisateurs).filter(models.Utilisateurs.email == payload.email).first()

    if not utilisateur:
        raise UnauthorizedError("Email ou mot de passe incorrect")

    now = now_utc()
    if utilisateur.verrouille_jusqua and utilisateur.verrouille_jusqua.replace(tzinfo=None) > now.replace(tzinfo=None):
        minutes_restantes = int((utilisateur.verrouille_jusqua - now.replace(tzinfo=None)).total_seconds() // 60) + 1
        raise ForbiddenError(f"Compte temporairement verrouillé. Réessayez dans {minutes_restantes} min.")

    if not utilisateur.actif:
        raise ForbiddenError("Compte désactivé")

    if not verify_password(payload.mot_de_passe, utilisateur.mot_de_passe):
        utilisateur.tentatives_echouees += 1
        if utilisateur.tentatives_echouees >= MAX_TENTATIVES:
            utilisateur.verrouille_jusqua = now_utc().replace(tzinfo=None) + timedelta(minutes=DUREE_VERROUILLAGE_MINUTES)
            utilisateur.tentatives_echouees = 0
        db.commit()
        raise UnauthorizedError("Email ou mot de passe incorrect")

    utilisateur.tentatives_echouees = 0
    utilisateur.verrouille_jusqua = None
    db.commit()

    token = create_access_token(utilisateur_id=utilisateur.id)
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
    # Seul le titulaire du compte peut changer ce mot de passe.
    if utilisateur_courant.id != utilisateur_id:
        raise ForbiddenError("Accès refusé")

    utilisateur = assert_found(
        db.query(models.Utilisateurs).filter(models.Utilisateurs.id == utilisateur_id).first(),
        "Utilisateur",
        str(utilisateur_id),
    )
    if not verify_password(payload.ancien_mot_de_passe, utilisateur.mot_de_passe):
        raise UnauthorizedError("Ancien mot de passe incorrect")
    _valider_mot_de_passe(payload.nouveau_mot_de_passe, champ="Le nouveau mot de passe")
    if verify_password(payload.nouveau_mot_de_passe, utilisateur.mot_de_passe):
        raise ValidationError(
            "nouveau_mot_de_passe",
            "Le nouveau mot de passe doit être différent de l'ancien",
        )
    utilisateur.mot_de_passe = hash_password(payload.nouveau_mot_de_passe)
    db.commit()
    return None


@router.post("/mot-de-passe-oublie", response_model=MotDePasseOublieResponse, status_code=status.HTTP_200_OK)
def mot_de_passe_oublie(payload: MotDePasseOublieRequest, db: Session = Depends(get_db)):
    """Déclenche l'envoi d'un lien de réinitialisation, sans jamais révéler
    l'existence du compte : la forme ET la durée de la réponse restent
    identiques que l'email existe ou non, que le SMTP soit actif ou non."""
    email = payload.email.strip().lower()
    utilisateur = (
        db.query(models.Utilisateurs)
        .filter(models.Utilisateurs.email == email)
        .first()
    )

    email_envoye = False
    if utilisateur:
        jeton = secrets.token_hex(32)
        jeton_hash = hashlib.sha256(jeton.encode("utf-8")).hexdigest()
        enregistrement = models.MotDePasseReinitialisation(
            id_utilisateur=utilisateur.id,
            jeton_hash=jeton_hash,
            expire_le=now_utc().replace(tzinfo=None) + timedelta(minutes=_DUREE_JETON_MINUTES),
        )
        db.add(enregistrement)
        db.commit()

        if mail_service.smtp_configue():
            lien = f"/reinitialiser?jeton={jeton}"
            email_envoye = mail_service.envoyer_email(
                destinataire=utilisateur.email,
                sujet="Réinitialisation de votre mot de passe",
                corps_texte=(
                    "Bonjour,\n\n"
                    "Vous avez demandé la réinitialisation de votre mot de passe.\n"
                    "Cliquez sur le lien suivant pour choisir un nouveau mot de passe :\n\n"
                    f"{lien}\n\n"
                    "Ce lien expire dans 30 minutes. Si vous n'êtes pas à l'origine de "
                    "cette demande, ignorez cet e-mail.\n"
                ),
            )
            if not email_envoye:
                # Jeton inutilisable si l'e-mail n'est jamais parti.
                db.refresh(enregistrement)
                enregistrement.utilise_le = now_utc().replace(tzinfo=None)
                db.commit()

    # Anti-énumération : les réponses prennent (à peu près) le même temps
    # que le traitement + l'envoi SMTP réel.
    time.sleep(_DELAI_ANTI_ENUMERATION)

    message = (
        "Si un compte est associé à cet e-mail, un lien de réinitialisation vous a été envoyé."
        if mail_service.smtp_configue()
        else "La réinitialisation par e-mail n'est pas activée. Contactez l'administrateur."
    )
    return MotDePasseOublieResponse(email_envoye=email_envoye, message=message)


@router.post("/reinitialiser-mot-de-passe", response_model=ReinitialiserMotDePasseResponse)
def reinitialiser_mot_de_passe(payload: ReinitialiserMotDePasseRequest, db: Session = Depends(get_db)):
    """Consomme un jeton valide (non expiré, non utilisé) : change le mot de
    passe, lève le verrouillage du compte et marque le jeton comme utilisé.
    Erreurs génériques (400) sans détail sur l'existence du compte."""
    jeton_hash = hashlib.sha256(payload.jeton.encode("utf-8")).hexdigest()
    enregistrement = (
        db.query(models.MotDePasseReinitialisation)
        .filter(models.MotDePasseReinitialisation.jeton_hash == jeton_hash)
        .first()
    )
    maintenant = now_utc().replace(tzinfo=None)
    if (
        not enregistrement
        or enregistrement.utilise_le is not None
        or enregistrement.expire_le is None
        or enregistrement.expire_le.replace(tzinfo=None) < maintenant
    ):
        raise HTTPException(status_code=400, detail="Jeton invalide ou expiré")

    utilisateur = (
        db.query(models.Utilisateurs)
        .filter(models.Utilisateurs.id == enregistrement.id_utilisateur)
        .first()
    )
    if not utilisateur or not utilisateur.actif:
        raise HTTPException(status_code=400, detail="Jeton invalide ou expiré")

    utilisateur.mot_de_passe = hash_password(payload.nouveau_mot_de_passe)
    utilisateur.tentatives_echouees = 0
    utilisateur.verrouille_jusqua = None
    enregistrement.utilise_le = maintenant
    db.commit()

    return ReinitialiserMotDePasseResponse(message="Mot de passe réinitialisé. Vous pouvez vous connecter.")
