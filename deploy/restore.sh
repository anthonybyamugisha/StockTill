#!/bin/bash
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: ./restore.sh <backup_file>"
  exit 1
fi

BACKUP_FILE="$1"

docker compose exec -T db psql -U stocktill stocktill < "$BACKUP_FILE"

echo "Restored from $BACKUP_FILE"
