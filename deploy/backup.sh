#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="stocktill_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

docker compose exec -T db pg_dump -U stocktill stocktill > "$BACKUP_DIR/$FILENAME"

echo "Backup saved to $BACKUP_DIR/$FILENAME"
