#!/usr/bin/env bash
# Lance le serveur pour le mode multi-poste (une école, plusieurs postes) :
# PostgreSQL + API + interface buildée, accessible depuis tout le réseau.
#
#   ./scripts/start_server.sh            # écoute sur 0.0.0.0:3000
#   HOST=127.0.0.1 PORT=3001 ./start_server.sh
#   BUILD=1 ./start_server.sh            # force le rebuild de l'interface
#
# Les postes ouvrent ensuite http://<ip-du-serveur>:3000 dans un navigateur.
set -euo pipefail
cd "$(dirname "$0")/.."

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-3000}"
ROOT="$(pwd)"

# Interface buildée SANS URL locale : l'API est appelée sur la même origine
# (window.location.origin), donc aucune IP n'est figée dans le bundle.
if [ ! -d "$ROOT/frontend/dist" ] || [ "${BUILD:-0}" = "1" ]; then
  echo "→ Build de l'interface (VITE_API_URL vide = même origine)…"
  (cd "$ROOT/frontend" && VITE_API_URL= npm run build)
fi

echo "→ Serveur sur http://$HOST:$PORT (interface + API)"
cd "$ROOT/backend"
exec uvicorn main:app --host "$HOST" --port "$PORT"
