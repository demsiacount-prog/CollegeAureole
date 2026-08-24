"""Migration automatique du schéma via Alembic au démarrage.

Remplace l'ancien `Base.metadata.create_all()` : les révisions Alembic sont la
source de vérité du schéma, exécutées à chaque lancement (idempotent).

Trois cas possibles au premier démarrage :
- base vierge            → `alembic upgrade head` crée tout le schéma ;
- base déjà migrée       → `alembic upgrade head` est un no-op rapide ;
- base héritée           → créée à l'époque par create_all() sans suivi
  Alembic : on complète les tables manquantes (create_all ne modifie jamais
  l'existant) puis on tamponne à head pour repartir sur des migrations saines.
"""
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from database import DATABASE_URL, engine, Base
import models  # noqa: F401  (peuple Base.metadata pour create_all des bases héritées)

logger = logging.getLogger("college_aureole")


def _repertoire_backend() -> Path:
    """Dossier contenant alembic.ini/alembic/ : celui du code source en dev,
    le dossier d'extraction de PyInstaller (_MEIPASS) sous exécutable gelé."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


_BACKEND_DIR = _repertoire_backend()
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"
_ALEMBIC_DIR = _BACKEND_DIR / "alembic"


def _config() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    cfg.set_main_option("prepend_sys_path", str(_BACKEND_DIR))
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    return cfg


def _tables() -> list[str]:
    return list(inspect(engine).get_table_names())


def migrer_schema() -> None:
    """Applique les migrations Alembic, gère la transition des bases héritées."""
    tables = set(_tables())
    has_version = "alembic_version" in tables
    user_tables = tables - {"alembic_version"}

    if has_version and user_tables:
        logger.info("Migrations Alembic : mise à jour du schéma…")
        command.upgrade(_config(), "head")
        return

    if has_version and not user_tables:
        # État « tamponné mais vide » : les tables ont été supprimées (reset)
        # mais alembic_version est resté, ce qui rend upgrade un no-op. On
        # repart d'une base vierge : suppression du tampon puis upgrade complet.
        logger.warning(
            "Base vidée mais tampon Alembic restant : reconstruction du schéma."
        )
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        command.upgrade(_config(), "head")
        return

    if user_tables:
        # Base héritée de l'époque create_all() : on crée les tables manquantes
        # (create_all est additif, il ne touche jamais aux tables existantes)
        # puis on tamponne à head pour activer le suivi Alembic.
        logger.warning(
            "Base existante sans suivi Alembic (create_all) : "
            "complétion du schéma puis tampon à head."
        )
        Base.metadata.create_all(bind=engine)
        command.stamp(_config(), "head")
        return

    logger.info("Base vierge : création du schéma via les migrations Alembic.")
    command.upgrade(_config(), "head")
