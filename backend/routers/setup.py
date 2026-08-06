import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import get_db, SessionLocal, engine, Base
from hashing import hash_password
from enums import RoleUtilisateur
import models

logger = logging.getLogger("college_aureole")
router = APIRouter(prefix="/api/setup", tags=["Setup"])


class SetupInput(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str
    seed_data: bool = True


class SetupStatusResponse(BaseModel):
    configured: bool


@router.get("/status", response_model=SetupStatusResponse)
def setup_status(db: Session = Depends(get_db)):
    admin_exists = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.role == RoleUtilisateur.ADMIN,
    ).first() is not None
    nb_users = db.query(models.Utilisateurs).count()
    logger.info(
        "setup/status : configured=%s utilisateurs=%s",
        admin_exists, nb_users,
    )
    return SetupStatusResponse(configured=admin_exists)


@router.post("/run", status_code=status.HTTP_201_CREATED)
def run_setup(payload: SetupInput, db: Session = Depends(get_db)):
    admin_exists = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.role == RoleUtilisateur.ADMIN,
    ).first() is not None
    if admin_exists:
        raise HTTPException(status_code=400, detail="Déjà configuré.")

    if payload.seed_data:
        try:
            db.commit()
            from seed import seed_database
            seed_database()
            db.rollback()
        except Exception as e:
            logger.exception("Seed échoué")
            try:
                db.rollback()
                db.query(models.Utilisateurs).delete()
                db.commit()
            except Exception as e2:
                logger.exception("Nettoyage des comptes après échec du seed impossible")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors du seed : {e}",
            )

    admin = db.query(models.Utilisateurs).filter(
        models.Utilisateurs.role == RoleUtilisateur.ADMIN,
    ).first()

    if admin:
        admin.nom = payload.nom
        admin.prenom = payload.prenom
        admin.email = payload.email
        admin.mot_de_passe = hash_password(payload.mot_de_passe)
    else:
        db.add(models.Utilisateurs(
            nom=payload.nom,
            prenom=payload.prenom,
            email=payload.email,
            mot_de_passe=hash_password(payload.mot_de_passe),
            role=RoleUtilisateur.ADMIN,
        ))

    db.commit()
    return {"message": "Configuration terminée."}
