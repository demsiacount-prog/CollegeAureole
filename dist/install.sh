#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
# Script d'installation rapide College Aureole (Linux)
# Usage: sudo ./install.sh
# ─────────────────────────────────────────────────────────────────────
set -e

APP_DIR="/opt/college-aureole"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit etre execute en root : sudo ./install.sh"
    exit 1
fi

echo ">> Extraction des fichiers..."
mkdir -p "$APP_DIR"
tar xzf "$SCRIPT_DIR/college-aureole.tar.gz" -C /tmp/
cp -a /tmp/CollegeAureole/backend/* "$APP_DIR/"
mkdir -p "$APP_DIR/frontend"
cp -a /tmp/CollegeAureole/frontend/dist/* "$APP_DIR/frontend/" 2>/dev/null || true
rm -rf /tmp/CollegeAureole

echo ">> Installation des dependances Python..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip --quiet
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" --quiet

# Generer .env si absent
if [ ! -f "$APP_DIR/.env" ]; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    DB_PASS="college_$(openssl rand -hex 6)"
    cat > "$APP_DIR/.env" <<EOF
ENVIRONMENT=production
AUREOLE_HOST=0.0.0.0
AUREOLE_PORT=8000
JWT_SECRET_KEY=$JWT_SECRET
CORS_ORIGINS=http://tauri.localhost,https://tauri.localhost,tauri://localhost
DATABASE_URL=postgresql+psycopg2://collegeaureole:$DB_PASS@localhost:5432/collegeaureole
AUTO_CREATE_TABLES=true
LOG_LEVEL=INFO
EOF
    chmod 640 "$APP_DIR/.env"
    echo ">> .env cree. Modifiez DATABASE_URL si necessaire."
fi

# User dedie
if ! getent group college-aureole >/dev/null 2>&1; then
    addgroup --system college-aureole
fi
if ! getent passwd college-aureole >/dev/null 2>&1; then
    adduser --system --ingroup college-aureole --home "$APP_DIR" --no-create-home college-aureole
fi
mkdir -p "$APP_DIR/uploads/logos"
chown -R college-aureole:college-aureole "$APP_DIR"

# Systemd
cat > /etc/systemd/system/college-aureole.service <<SVCEOF
[Unit]
Description=College Aureole - Serveur API
After=network.target postgresql.service

[Service]
Type=simple
User=college-aureole
Group=college-aureole
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable college-aureole

echo ""
echo "=========================================="
echo "  College Aureole installe avec succes !"
echo "=========================================="
echo ""
echo "  Demarrer :  systemctl start college-aureole"
echo "  Statut    :  systemctl status college-aureole"
echo "  Logs      :  journalctl -u college-aureole -f"
echo "  Config    :  $APP_DIR/.env"
echo ""
