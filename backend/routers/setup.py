import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, SessionLocal, engine, Base
from exceptions import ConflictError
from migrations import migrer_schema
from routers.etablissement import enregistrer_logo
from security import require_role
from services import initialisation
import models

logger = logging.getLogger("college_aureole")
router = APIRouter(prefix="/api/setup", tags=["Setup"])

# Tables contenant des données utilisateur : si au moins une est non vide,
# la réinitialisation de la base a un intérêt (bouton visible).
TABLES_DONNEES = [
    "eleves", "classes", "enseignants", "tuteurs", "cours",
    "notes", "absences", "paiements", "inscriptions", "echeances", "depenses",
]


# ─── Entrées ─────────────────────────────────────────────────────────────────

class EtablissementInput(BaseModel):
    nom: str = Field(min_length=1)
    sigle: str | None = None
    devise: str | None = None
    adresse: str | None = None
    telephone: str | None = None
    email: EmailStr | None = None
    logo: str | None = None


class AdminInput(BaseModel):
    nom: str = Field(min_length=1)
    prenom: str = Field(min_length=1)
    email: EmailStr
    mot_de_passe: str = Field(min_length=8)


class AnneeScolaireInput(BaseModel):
    date_debut: date
    date_fin: date

    @model_validator(mode="after")
    def verifier_dates(self):
        if self.date_fin < self.date_debut:
            raise ValueError("Date de fin invalide")
        return self


class SetupInput(BaseModel):
    etablissement: EtablissementInput
    admin: AdminInput
    annee_scolaire: AnneeScolaireInput | None = None


# ─── Réponses ────────────────────────────────────────────────────────────────

class SetupStatusResponse(BaseModel):
    configured: bool
    etablissement: bool = False
    admin: bool = False
    annee_scolaire: bool = False
    donnees_presentes: bool = False
    progression: dict | None = None


class ProgressResponse(BaseModel):
    run_id: str | None = None
    en_cours: bool = False
    etape: int = 0
    nb_etapes: int = initialisation.NB_ETAPES
    message: str = ""
    pourcent: int = 0
    termine: bool = False
    erreur: str | None = None


class SetupRunResponse(BaseModel):
    run_id: str
    status: str
    message: str


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _donnees_presentes(db: Session) -> bool:
    for table in TABLES_DONNEES:
        try:
            if (db.execute(text(f"SELECT count(*) FROM {table}")).scalar() or 0) > 0:
                return True
        except Exception:
            continue
    return False


def _supprimer_tampon_alembic() -> None:
    """drop_all ne connaît pas alembic_version : sans cette suppression, le
    démarrage suivant verrait une base « déjà migrée » et ne recréerait rien."""
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    except Exception:
        logger.exception("Impossible de supprimer alembic_version")


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/status", response_model=SetupStatusResponse)
def setup_status(db: Session = Depends(get_db)):
    prog = initialisation.get_progress()
    return SetupStatusResponse(
        configured=initialisation.est_configure(db),
        etablissement=initialisation.etablissement_existe(db),
        admin=initialisation.admin_existe(db),
        annee_scolaire=initialisation.annee_scolaire_existe(db),
        donnees_presentes=_donnees_presentes(db),
        progression=ProgressResponse(**prog).model_dump() if prog["en_cours"] else None,
    )


@router.post("/run", response_model=SetupRunResponse, status_code=status.HTTP_202_ACCEPTED)
def run_setup(
    payload: SetupInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Lance l'initialisation en arrière-plan (une seule fois dans la vie de la base)."""
    if initialisation.est_configure(db):
        raise ConflictError("Application déjà configurée")
    prog = initialisation.get_progress()
    if prog["en_cours"]:
        raise ConflictError("Initialisation en cours")

    # Course : deux appels simultanés ne peuvent pas passer tous les deux.
    run_id = initialisation.demarrer()
    background_tasks.add_task(initialisation.executer_initialisation, payload)
    return SetupRunResponse(
        run_id=run_id,
        status="en_cours",
        message="Initialisation démarrée.",
    )


@router.post("/logo")
def setup_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Importe le logo de l'établissement pendant l'initialisation.

    Aucun compte n'existe encore à ce stade : l'endpoint n'est donc pas
    authentifié. Il est uniquement disponible tant que l'application n'est pas
    configurée ; le chemin retourné est ensuite transmis dans la fiche
    d'initialisation.
    """
    if initialisation.est_configure(db):
        raise ConflictError("Application déjà configurée")
    return {"logo": enregistrer_logo(file)}


@router.get("/progress", response_model=ProgressResponse)
def setup_progress():
    return ProgressResponse(**initialisation.get_progress())


class ResetInput(BaseModel):
    confirm: bool = False


@router.post("/reset")
def reset_database(payload: ResetInput, db: Session = Depends(get_db)):
    """Vide toute la base et recrée le schéma : retour à la configuration initiale.

    Dangereux par nature (supprime toutes les données), accessible uniquement
    depuis le localhost, et requiert une confirmation explicite.
    """
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Confirmation requise")
    logger.warning("Réinitialisation complète de la base demandée.")
    db.close()
    Base.metadata.drop_all(bind=engine)
    _supprimer_tampon_alembic()
    migrer_schema()
    logger.warning("Base réinitialisée avec succès.")
    return {"message": "Base réinitialisée."}


class PurgeInput(BaseModel):
    confirm: bool = False


# Valeur d'en-tête obligatoire pour toute réinitialisation de données.
# En plus du rôle admin et du `confirm: true` du corps, la requête doit
# transmettre ce header : une exécution accidentelle (ou un CSRF, les CORS
# n'étant pas une protection) devient beaucoup moins probable.
PURGE_HEADER = "x-confirm"
PURGE_TOKEN = "PURGE-DONNEES"


@router.post("/purge-donnees")
def purge_donnees(
    payload: PurgeInput,
    x_confirm: str | None = Header(default=None, alias="X-Confirm"),
    utilisateur_courant: models.Utilisateurs = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Vide entièrement la base de données et ne conserve que le compte de
    l'utilisateur courant, afin de garder la session valide après la
    réinitialisation (reconnexion inutile)."
    """
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Confirmation requise")
    if x_confirm != PURGE_TOKEN:
        raise HTTPException(status_code=400, detail="Confirmation requise")

    compte = {
        "id": utilisateur_courant.id,
        "nom": utilisateur_courant.nom,
        "prenom": utilisateur_courant.prenom,
        "email": utilisateur_courant.email,
        "mot_de_passe": utilisateur_courant.mot_de_passe,
        "role": utilisateur_courant.role,
        "actif": utilisateur_courant.actif,
        "tentatives_echouees": 0,
        "verrouille_jusqua": None,
    }

    logger.warning(
        "Réinitialisation complète demandée par %s (id=%s) : seul ce compte sera conservé.",
        utilisateur_courant.email,
        utilisateur_courant.id,
    )
    db.close()
    Base.metadata.drop_all(bind=engine)
    _supprimer_tampon_alembic()
    migrer_schema()

    session = SessionLocal()
    try:
        session.add(models.Utilisateurs(**compte))
        session.commit()
    finally:
        session.close()

    return {"message": "Base réinitialisée : seul votre compte a été conservé."}
