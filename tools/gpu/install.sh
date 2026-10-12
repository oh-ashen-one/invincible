#!/bin/bash
# Homage fan game tooling. Not an official Marvel, Sony or Insomniac project; no affiliation.
# Copies the lock tool to a stable path every builder can call before they have merged night1/gpulock:
#   /Users/midir/sm2-n1/_scratch/gpu/bin/{gpu_slot.sh,gpu_slot.py,gpu_status.sh}
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$DEST"
cp "$HERE/gpu_slot.sh" "$HERE/gpu_slot.py" "$HERE/gpu_status.sh" "$DEST/"
chmod +x "$DEST"/*
echo "installed -> $DEST"
