#!/bin/bash
# Sincroniza las capturas de trades desde Google Drive a data/Reports_Screenshots/
# Uso: bash sync_screenshots.sh
#
# El id de la carpeta de Drive no vive en el repo (es público): se lee de .env
# como SCREENSHOTS_FOLDER_ID. Sin él, el script no hace nada.

set -uo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Falta $ENV_FILE. Copia config/.env.example y rellénalo." >&2
    exit 1
fi

FOLDER_ID="$(grep -E '^SCREENSHOTS_FOLDER_ID=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '[:space:]"' || true)"

if [ -z "$FOLDER_ID" ]; then
    echo "❌ SCREENSHOTS_FOLDER_ID no está definido en $ENV_FILE." >&2
    exit 1
fi

rclone sync "capturas:" --drive-root-folder-id "$FOLDER_ID" "$DIR/data/Reports_Screenshots/" --progress
echo ""
echo "Screenshots sincronizadas. Total: $(ls "$DIR/data/Reports_Screenshots/" | wc -l) archivos"
