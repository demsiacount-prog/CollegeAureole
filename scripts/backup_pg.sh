#!/usr/bin/env bash
# Sauvegarde PostgreSQL (format custom, pg_restore) + rotation.
#
# Variables d'environnement attendues (ou ~/.pgpass) :
#   PGHOST, PGPORT, PGUSER, PGDATABASE, PGPASSWORD
# Exemple (crontab quotidien) :
#   15 1 * * * PGHOST=localhost PGUSER=demsi PGDATABASE=collegeaureole \
#     PGPASSWORD='...' /chemin/scripts/backup_pg.sh
set -euo pipefail
cd "$(dirname "$0")"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/collegeaureole}"
KEEP="${KEEP:-7}"
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-demsi}"
PGDATABASE="${PGDATABASE:-collegeaureole}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="$BACKUP_DIR/collegeaureole_${STAMP}.sql"

pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -F c -f "$FILE"
echo "✓ Sauvegarde : $FILE ($(du -h "$FILE" | cut -f1))"

# Rotation : on ne garde que les KEEP dernières sauvegardes
ls -1t "$BACKUP_DIR"/collegeaureole_*.sql 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
echo "✓ Rotation : ${KEEP} sauvegarde(s) conservée(s)."
