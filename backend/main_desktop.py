import os
import sys
import socket
import logging
import threading
import time

os.environ.setdefault("AUTO_CREATE_TABLES", "true")
# Tauri v2 : origine HTTP sur Windows (http://tauri.localhost), schéma tauri://
# sur Linux/macOS. https://tauri.localhost = ancien schéma v1 (compatibilité).
os.environ.setdefault(
    "CORS_ORIGINS",
    "tauri://localhost,http://tauri.localhost,https://tauri.localhost",
)

from database import get_data_dir

def _configurer_logs():
    data_dir = get_data_dir() or os.path.expanduser("~")
    log_file = os.path.join(data_dir, "backend.log")
    niveau = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    formateur = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(niveau)
    fh.setFormatter(formateur)

    logger = logging.getLogger("college_aureole")
    logger.setLevel(niveau)
    logger.addHandler(fh)
    for nom in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(nom)
        lg.setLevel(logging.INFO)
        lg.handlers.clear()
        lg.addHandler(fh)
    logger.info("Backend démarré. Journal : %s", log_file)
    logger.info("CORS_ORIGINS=%s", os.getenv("CORS_ORIGINS"))
    logger.info("DATABASE_URL=%s", os.getenv("DATABASE_URL") or f"sqlite:///{os.path.join(data_dir, 'collegeaureole.db')}")
    return log_file

_LOG_FILE = _configurer_logs()
logger = logging.getLogger("college_aureole")

def _trouver_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

PORT = int(os.getenv("AUREOLE_PORT", "0"))
if PORT == 0:
    PORT = _trouver_port()

from main import app

def _servir():
    import uvicorn
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=PORT,
        log_level="info",
        access_log=True,
    )
    server = uvicorn.Server(config)

    def _annoncer_port():
        while not server.started:
            time.sleep(0.05)
        print(f"AUREOLE_PORT={PORT}", flush=True)

    threading.Thread(target=_annoncer_port, daemon=True).start()
    server.run()

if __name__ == "__main__":
    _servir()
