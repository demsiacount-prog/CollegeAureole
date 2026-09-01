"""Point d'entrée de l'exécutable serveur College Aureole.

Lancé par le service Windows (WinSW) installé par l'installeur NSIS, ou
manuellement pour diagnostic : `college-aureole-serveur.exe`.

Configuration lue depuis le fichier .env du répertoire d'installation
(chargé par database.py via python-dotenv, CWD = répertoire d'installation) :
- AUREOLE_HOST          : interface d'écoute (défaut 0.0.0.0)
- AUREOLE_PORT          : port HTTP (défaut 8000)
- DATABASE_URL          : connexion PostgreSQL (générée par l'installeur)
- DB_ATTENTE_MAX_S      : durée max d'attente de la base (défaut 60 s)
- DB_ATTENTE_INTERVAL_S : intervalle entre deux tentatives (défaut 3 s)
"""
import logging
import os
import sys
import time

import uvicorn
from sqlalchemy import create_engine, text

logger = logging.getLogger("college_aureole")


def attendre_base() -> None:
    """Bloque tant que la base n'est pas joignable, puis retourne.

    Le backend dépend entièrement de PostgreSQL (migrations Alembic au
    démarrage, requêtes en base). On attend ici, par retries, que la base
    réponde avant de lancer l'API, afin que `/api/health` ne soit jamais
    "unavailable" par course au démarrage.

    En cas de dépassement du délai, on sort avec un code d'erreur non nul :
    le wrapper de service (WinSW) est configuré en `onfailure restart` et
    relance le processus jusqu'à ce que la base soit disponible.
    """
    max_s = int(os.getenv("DB_ATTENTE_MAX_S", "60"))
    interval = float(os.getenv("DB_ATTENTE_INTERVAL_S", "3"))

    from database import DATABASE_URL  # import tardif : charge le .env

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    echec = False
    debut = time.monotonic()
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            if echec:
                logger.info("Base de données à nouveau disponible.")
            else:
                logger.info("Base de données disponible.")
            engine.dispose()
            return
        except Exception:
            echec = True
            elapsed = time.monotonic() - debut
            if elapsed >= max_s:
                logger.error(
                    "Base de données injoignable après %.0f s (DATABASE_URL=%s). "
                    "Sortie pour redémarrage.",
                    elapsed,
                    DATABASE_URL,
                )
                engine.dispose()
                sys.exit(1)
            logger.warning(
                "Base de données injoignable, nouvelle tentative dans %.0f s "
                "(écoulé: %.0f s / %d s max).",
                interval,
                elapsed,
                max_s,
            )
            time.sleep(interval)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    host = os.getenv("AUREOLE_HOST", "0.0.0.0")
    port = int(os.getenv("AUREOLE_PORT", "8000"))

    attendre_base()

    # Import tardif : main.py s'exécute après que la base soit garantie
    # disponible, donc les migrations Alembic (migrer_schema) pourront
    # s'appliquer sans échec de connexion.
    from main import app

    # Worker unique volontaire : le rate-limiting réseau (protections du
    # login contre le bruteforce) est tenu en RAM par processus. Avec plusieurs
    # workers, chaque worker compterait indépendamment, multipliant le nombre
    # de tentatives autorisées par IP. Ne pas passer en multi-workers sans
    # externaliser le compteur (Redis) ou accepter cette dilution.
    uvicorn.run(app, host=host, port=port, log_config=None)


if __name__ == "__main__":
    main()
