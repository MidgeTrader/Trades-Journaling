#!/bin/bash
# Sincroniza las capturas de trades desde Google Drive a Reports_Screenshots/
# Uso: bash sync_screenshots.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
rclone sync "capturas:" --drive-root-folder-id "1sH76L-LgJUnVgHOycpxJTCbMYxpQ4uyh" "$DIR/Reports_Screenshots/" --progress
echo ""
echo "Screenshots sincronizadas. Total: $(ls "$DIR/Reports_Screenshots/" | wc -l) archivos"
