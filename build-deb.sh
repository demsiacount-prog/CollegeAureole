#!/bin/bash
# build-deb.sh — Construit le .deb College Aureole (backend)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_SRC="$SCRIPT_DIR/backend"
BUILD_DIR="/tmp/college-aureole-deb"
PKG_DIR="$BUILD_DIR/opt/college-aureole/backend"

echo ">> Construction du .deb College Aureole..."

# Nettoyer
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN" "$PKG_DIR" "$BUILD_DIR/etc/systemd/system"

# Copier le backend
echo ">> Copie du backend..."
cp -a "$BACKEND_SRC"/. "$PKG_DIR/"

# Supprimer les fichiers inutiles pour le package
rm -rf "$PKG_DIR/__pycache__" "$PKG_DIR/.git" "$PKG_DIR/.github" "$PKG_DIR/.gitignore" "$PKG_DIR/.env" "$PKG_DIR/.env.example" "$PKG_DIR/README.md" "$PKG_DIR/college-aureole-backend.spec" "$PKG_DIR/dist" "$PKG_DIR/build" 2>/dev/null || true

# Creer le venv pour le package
echo ">> Creation du venv dans le package..."
python3 -m venv "$PKG_DIR/venv"
"$PKG_DIR/venv/bin/pip" install --upgrade pip --quiet 2>/dev/null
"$PKG_DIR/venv/bin/pip" install -r "$PKG_DIR/requirements.txt" --quiet 2>/dev/null

# Fichiers DEBIAN
cat > "$BUILD_DIR/DEBIAN/control" <<CTRL
Package: college-aureole-serveur
Version: 1.0.0
Architecture: amd64
Maintainer: College Aureole <contact@college-aureole.local>
Depends: python3, python3-venv, python3-pip, postgresql, postgresql-client
Description: College Aureole - Serveur API Backend
 Backend FastAPI pour la gestion scolaire College Aureole.
 Connecte a PostgreSQL.
CTRL

cat > "$BUILD_DIR/DEBIAN/postinst" <<'POSTINST'
#!/bin/bash
# postinst — College Aureole serveur .deb

APP_DIR="/opt/college-aureole/backend"
VENV_DIR="$APP_DIR/venv"
ENV_FILE="$APP_DIR/.env"
DB_NAME="collegeaureole"
DB_USER="collegeaureole"

log() { echo "[college-aureole] $1"; }

# ── 1. Utilisateur dedie ──
if ! getent group college-aureole >/dev/null 2>&1; then
    addgroup --system college-aureole
fi
if ! getent passwd college-aureole >/dev/null 2>&1; then
    adduser --system --ingroup college-aureole --home "$APP_DIR" --no-create-home college-aureole
fi

# ── 2. Permissions ──
chown -R college-aureole:college-aureole "$APP_DIR"
chmod -R u=rwX,g=rX,o=rX "$APP_DIR"

# ── 3. Uploads ──
mkdir -p "$APP_DIR/uploads/logos"
chown -R college-aureole:college-aureole "$APP_DIR/uploads"
chmod -R u=rwX,g=rX,o=rwx "$APP_DIR/uploads"

# ── 4. Venv ──
if [ ! -d "$VENV_DIR" ]; then
    log "Creation de l'environnement Python..."
    python3 -m venv "$VENV_DIR" || { log "ERREUR: echec creation venv"; exit 1; }
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet 2>&1 || true
    "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt" --quiet 2>&1 || {
        log "ERREUR: echec installation dependances"; exit 1;
    }
fi
chown -R college-aureole:college-aureole "$VENV_DIR"

# ── 5. Port PG ──
PG_PORT=5432
if command -v pg_config >/dev/null 2>&1; then
    PG_PORT=$(pg_config --port 2>/dev/null || echo 5432)
fi

# ── 6. Fichier .env ──
if [ ! -f "$ENV_FILE" ]; then
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASS="college_$(openssl rand -hex 6)"
    cat > "$ENV_FILE" <<ENVEOF
ENVIRONMENT=production
AUREOLE_HOST=0.0.0.0
AUREOLE_PORT=8000
JWT_SECRET_KEY=${JWT_SECRET}
CORS_ORIGINS=http://tauri.localhost,https://tauri.localhost,tauri://localhost
DATABASE_URL=postgresql+psycopg2://${DB_USER}:${DB_PASS}@localhost:${PG_PORT}/${DB_NAME}
AUTO_CREATE_TABLES=true
LOG_LEVEL=INFO
ENVEOF
    chmod 640 "$ENV_FILE"
    chown college-aureole:college-aureole "$ENV_FILE"
    log "Fichier .env cree."
fi

# ── 7. PostgreSQL (postinst tourne en root → su suffit) ──
if command -v psql >/dev/null 2>&1; then
    log "Configuration de PostgreSQL..."
    DB_PASS_CURRENT=$(grep DATABASE_URL "$ENV_FILE" | sed 's|.*://[^:]*:\([^@]*\)@.*|\1|')
    PG_EXEC() { su -s /bin/bash postgres -c "psql -Atc \"$1\"" 2>/dev/null; }
    PG_EXEC_RAW() { su -s /bin/bash postgres -c "psql -c \"$1\"" 2>/dev/null; }

    # Utilisateur
    if ! PG_EXEC "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
        PG_EXEC_RAW "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS_CURRENT}'" && \
            log "Utilisateur ${DB_USER} cree." || \
            log "WARN: Impossible de creer l'utilisateur ${DB_USER}."
    else
        PG_EXEC_RAW "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS_CURRENT}'" || true
    fi

    # Base de donnees
    if ! PG_EXEC "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
        PG_EXEC_RAW "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}" && \
            log "Base ${DB_NAME} creee." || \
            log "WARN: Impossible de creer la base ${DB_NAME}."
    else
        log "Base ${DB_NAME} existe deja."
    fi

    # pg_hba.conf : autoriser les connexions TCP
    PG_HBA=$(PG_EXEC "SHOW hba_file")
    if [ -n "$PG_HBA" ] && [ -f "$PG_HBA" ]; then
        if ! grep -q "^host.*${DB_USER}.*127.0.0.1" "$PG_HBA" 2>/dev/null; then
            {
                echo "host ${DB_NAME} ${DB_USER} 127.0.0.1/32 md5"
                echo "host ${DB_NAME} ${DB_USER} ::1/128 md5"
            } | su -s /bin/bash postgres -c "tee -a '$PG_HBA'" >/dev/null
            systemctl reload postgresql 2>/dev/null || true
            log "Regles pg_hba.conf mises a jour."
        fi
    fi
fi

# ── 8. Permissions finales ──
chown -R college-aureole:college-aureole "$APP_DIR"

# ── 9. Systemd ──
systemctl daemon-reload 2>/dev/null || true
systemctl enable college-aureole.service 2>/dev/null || true

log "College Aureole installe !"
log "  Demarrer : systemctl start college-aureole"
log "  Logs     : journalctl -u college-aureole -f"
POSTINST

cat > "$BUILD_DIR/DEBIAN/prerm" <<'PRERM'
#!/bin/bash
if [ "$1" = "remove" ] || [ "$1" = "deconfigure" ]; then
    systemctl stop college-aureole.service 2>/dev/null || true
    systemctl disable college-aureole.service 2>/dev/null || true
fi
PRERM

cat > "$BUILD_DIR/DEBIAN/postrm" <<'POSTRM'
#!/bin/bash
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    systemctl daemon-reload 2>/dev/null || true
    rm -f /etc/systemd/system/college-aureole.service 2>/dev/null || true
fi
if [ "$1" = "purge" ]; then
    rm -rf /opt/college-aureole/backend/uploads
    rm -f /opt/college-aureole/backend/.env
fi
POSTRM

chmod 755 "$BUILD_DIR/DEBIAN/postinst" "$BUILD_DIR/DEBIAN/prerm" "$BUILD_DIR/DEBIAN/postrm"

# Service file
cp "$SCRIPT_DIR/backend/college-aureole-backend.service" "$BUILD_DIR/etc/systemd/system/college-aureole.service" 2>/dev/null || cat > "$BUILD_DIR/etc/systemd/system/college-aureole.service" <<'SVC'
[Unit]
Description=College Aureole - Serveur API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=college-aureole
Group=college-aureole
WorkingDirectory=/opt/college-aureole/backend
EnvironmentFile=/opt/college-aureole/backend/.env
ExecStart=/opt/college-aureole/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVC

# Permissions finales sur les fichiers DEBIAN
chmod -R go=rX "$BUILD_DIR/opt" "$BUILD_DIR/etc"

# Construire le .deb
echo ">> Construction du .deb..."
dpkg-deb --root-owner-group --build "$BUILD_DIR" "$SCRIPT_DIR/dist/college-aureole-serveur_1.0.0_amd64.deb"

echo ""
echo ">> .deb cree : $SCRIPT_DIR/dist/college-aureole-serveur_1.0.0_amd64.deb"
echo ">> Installer : sudo dpkg -i $SCRIPT_DIR/dist/college-aureole-serveur_1.0.0_amd64.deb"
