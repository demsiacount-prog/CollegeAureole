"""Point d'entrée de l'exécutable serveur College Aureole.

Lancé par le service Windows (WinSW) installé par l'installeur NSIS, ou
manuellement pour diagnostic : `college-aureole-serveur.exe`.

Configuration lue depuis le fichier .env du répertoire d'installation
(chargé par database.py via python-dotenv, CWD = répertoire d'installation) :
- AUREOLE_HOST  : interface d'écoute (défaut 0.0.0.0 pour être joignable du LAN)
- AUREOLE_PORT  : port HTTP (défaut 8000)
- DATABASE_URL  : connexion PostgreSQL (générée par l'installeur)
"""
import logging
import os

import uvicorn


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    host = os.getenv("AUREOLE_HOST", "0.0.0.0")
    port = int(os.getenv("AUREOLE_PORT", "8000"))

    # Import tardif : database.py charge le .env avant toute autre lecture
    # de configuration (JWT_SECRET_KEY, CORS_ORIGINS, …).
    from main import app

    uvicorn.run(app, host=host, port=port, log_config=None)


if __name__ == "__main__":
    main()
