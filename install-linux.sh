#!/bin/bash
# install-linux.sh — Installe College Aureole sur Linux (Ubuntu/Debian)
# Usage : sudo ./install-linux.sh
# Les deux .deb doivent être dans le même dossier que ce script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${GREEN}[✔]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✘]${NC} $1"; exit 1; }

# ── Vérifications préalables ─────────────────────────────────────────────────
[ "$(id -u)" -eq 0 ] || err "Ce script doit être exécuté en root : sudo ./install-linux.sh"
command -v dpkg >/dev/null 2>&1 || err "Ce script nécessite un système basé sur Debian/Ubuntu."

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}   Installation Collège Auréole${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── Trouver les .deb dans le répertoire courant ──────────────────────────────
SERVEUR_DEB=$(ls "$SCRIPT_DIR"/college-aureole-serveur_*.deb 2>/dev/null | sort -V | tail -1 || true)
CLIENT_DEB=$(ls "$SCRIPT_DIR"/college-aureole_*.deb 2>/dev/null | sort -V | tail -1 || true)

[ -z "$SERVEUR_DEB" ] && err "Fichier college-aureole-serveur_*.deb introuvable dans $SCRIPT_DIR"
[ -z "$CLIENT_DEB" ]  && err "Fichier college-aureole_*.deb introuvable dans $SCRIPT_DIR"

log "Serveur trouvé : $(basename "$SERVEUR_DEB")"
log "Client trouvé  : $(basename "$CLIENT_DEB")"
echo ""

# ── 1. PostgreSQL ────────────────────────────────────────────────────────────
if ! systemctl is-active --quiet postgresql 2>/dev/null; then
    log "Installation de PostgreSQL..."
    apt-get update -q
    apt-get install -y postgresql postgresql-client
    systemctl enable postgresql
    systemctl start postgresql
    log "PostgreSQL installé et démarré."
else
    log "PostgreSQL déjà actif, skip."
fi

# ── 2. Serveur backend ───────────────────────────────────────────────────────
log "Installation du serveur backend..."
dpkg -i "$SERVEUR_DEB" 2>/dev/null || apt-get install -f -y -q
log "Serveur installé."

# ── 3. Client Tauri ──────────────────────────────────────────────────────────
log "Installation du client..."
dpkg -i "$CLIENT_DEB" 2>/dev/null || apt-get install -f -y -q
log "Client installé."

# ── 4. Vérification ──────────────────────────────────────────────────────────
echo ""
log "Vérification du démarrage (max 20 s)..."
for i in $(seq 1 10); do
    sleep 2
    if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
        HEALTH=$(curl -s http://localhost:8000/api/health)
        log "Serveur opérationnel : $HEALTH"
        break
    fi
    [ "$i" -eq 10 ] && warn "Le serveur ne répond pas encore. Vérifiez : journalctl -u college-aureole -f"
done

# ── Résumé ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Collège Auréole installé avec succès !${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Lancer l'application : menu Applications → College Aureole"
echo "  Logs serveur         : journalctl -u college-aureole -f"
echo "  Santé API            : curl http://localhost:8000/api/health"
echo "  Mise à jour          : re-exécuter ce script avec les nouveaux .deb"
echo ""
