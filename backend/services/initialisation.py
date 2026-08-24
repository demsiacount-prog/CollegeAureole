"""Phase d'initialisation unique au premier lancement.

Garantit que l'application n'est configurée qu'une seule fois : la présence
d'une ligne dans « etablissement » couplée à un compte administrateur marque
l'initialisation comme terminée. L'exécution est lancée en tâche de fond pour
remonter une progression réelle via GET /api/setup/progress.
"""
import logging
import threading
import uuid
from datetime import date

from sqlalchemy.orm import Session

from database import SessionLocal
from enums import RoleUtilisateur
from hashing import hash_password
from periodes import generer_periodes_par_defaut
import models

logger = logging.getLogger("college_aureole")

# ─── Progression (store en mémoire, une seule initialisation à la fois) ──────
_lock = threading.Lock()
_progress: dict = {
    "run_id": None,
    "en_cours": False,
    "etape": 0,
    "message": "",
    "pourcent": 0,
    "termine": False,
    "erreur": None,
}

NB_ETAPES = 5


def get_progress() -> dict:
    with _lock:
        return dict(_progress)


def _maj(**champs) -> None:
    with _lock:
        _progress.update(champs)


def _demarrer() -> str:
    run_id = uuid.uuid4().hex
    _maj(run_id=run_id, en_cours=True, etape=0, message="Initialisation lancée…",
         pourcent=0, termine=False, erreur=None)
    return run_id


def demarrer() -> str:
    """Marque le début d'une initialisation et retourne l'identifiant de la course."""
    return _demarrer()


def _finir() -> None:
    _maj(en_cours=False, etape=NB_ETAPES, pourcent=100, termine=True,
         message="Initialisation terminée.", erreur=None)


def _echouer(erreur: str) -> None:
    logger.error("Initialisation en échec : %s", erreur)
    _maj(en_cours=False, termine=True, erreur=erreur)


def _nettoyer() -> None:
    """Meilleur effort : revient à un état non configuré pour relancer proprement."""
    try:
        db = SessionLocal()
        db.query(models.Etablissement).delete()
        db.query(models.Utilisateurs).delete()
        db.query(models.AnneesScolaires).delete()
        db.commit()
    except Exception:
        logger.exception("Nettoyage après échec de l'initialisation impossible")
    finally:
        db.close()


def _etape(etape: int, message: str, pourcent: int) -> None:
    _maj(etape=etape, message=message, pourcent=pourcent)


# ─── État de configuration ──────────────────────────────────────────────────

def etablissement_existe(db: Session) -> bool:
    return db.query(models.Etablissement).first() is not None


def admin_existe(db: Session) -> bool:
    return (
        db.query(models.Utilisateurs)
        .filter(models.Utilisateurs.role == RoleUtilisateur.ADMIN)
        .first() is not None
    )


def annee_scolaire_existe(db: Session) -> bool:
    return db.query(models.AnneesScolaires).first() is not None


def est_configure(db: Session) -> bool:
    return admin_existe(db)


# ─── Helpers ────────────────────────────────────────────────────────────────

def annee_scolaire_par_defaut() -> tuple[date, date]:
    """Période par défaut d'une année scolaire malienne (oct. → juil.)."""
    aujourdhui = date.today()
    if aujourdhui.month >= 10:
        return date(aujourdhui.year, 10, 1), date(aujourdhui.year + 1, 7, 31)
    return date(aujourdhui.year - 1, 10, 1), date(aujourdhui.year, 7, 31)


def libelle_annee(debut: date, fin: date) -> str:
    return f"{debut.year}-{fin.year}"


# ─── Exécution (tâche de fond) ──────────────────────────────────────────────

def executer_initialisation(payload) -> None:
    """Crée établissement + admin + année scolaire."""
    try:
        etablissement = payload.etablissement
        admin = payload.admin
        if payload.annee_scolaire is not None:
            annee_debut = payload.annee_scolaire.date_debut
            annee_fin = payload.annee_scolaire.date_fin
        else:
            annee_debut, annee_fin = annee_scolaire_par_defaut()

        # 1. Fiche établissement (marqueur de configuration)
        _etape(1, "Enregistrement de la fiche établissement…", 8)
        db = SessionLocal()
        try:
            db.add(models.Etablissement(
                id=1,
                nom=etablissement.nom,
                sigle=etablissement.sigle,
                devise=etablissement.devise,
                adresse=etablissement.adresse,
                telephone=etablissement.telephone,
                email=etablissement.email,
                logo=etablissement.logo,
                date_initialisation=date.today(),
            ))
            db.commit()
        finally:
            db.close()

        # 2. Année scolaire + périodes (trimestres/compositions).
        _etape(2, "Création de l'année scolaire…", 20)
        annee_id = None
        db = SessionLocal()
        try:
            annee = models.AnneesScolaires(
                libelle=libelle_annee(annee_debut, annee_fin),
                date_debut=annee_debut,
                date_fin=annee_fin,
                active=True,
            )
            db.add(annee)
            db.commit()
            db.refresh(annee)
            annee_id = annee.id
            generer_periodes_par_defaut(db, annee.id, annee_debut, annee_fin)
            db.commit()
        finally:
            db.close()

        # 3. Compte administrateur personnalisé.
        _etape(3, "Création du compte administrateur…", 40)
        db = SessionLocal()
        try:
            db.add(models.Utilisateurs(
                nom=admin.nom,
                prenom=admin.prenom,
                email=admin.email,
                mot_de_passe=hash_password(admin.mot_de_passe),
                role=RoleUtilisateur.ADMIN,
            ))
            db.commit()
        finally:
            db.close()

        # 4. Données d'exemple (optionnel) : comptes démo, classes, élèves…
        if getattr(payload, "donnees_exemple", True) and annee_id is not None:
            _etape(4, "Création des données d'exemple…", 50)
            from services.donnees_exemple import peupler
            peupler(annee_id, annee_debut, annee_fin, admin.email)

        _etape(5, "Configuration de l'application…", 95)
        _finir()
    except Exception as e:
        logger.exception("Initialisation échouée")
        _nettoyer()
        _echouer(str(e))
