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

logging.basicConfig(level=os.getenv("LOG_LEVEL", "WARNING"))
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
        log_level=os.getenv("LOG_LEVEL", "warning").lower(),
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
