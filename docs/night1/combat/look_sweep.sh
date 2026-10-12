#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02: render the same fight moments under several look presets (-WHCmbLook, no map rebuild) inside ONE gpu_slot capture hold.
#   look_sweep.sh <out_root> <script.json> <shot times, comma separated> <presets file: 'name|k=v,k=v' per line> [WxH=1920x1080] [quit_s]
set -uo pipefail
OUT="$1"; SCRIPT="$2"; SHOTS="$3"; PRESETS="$4"; RES="${5:-1920x1080}"; QUIT="${6:-16}"
HERE="$(cd "$(dirname "$0")" && pwd)"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; SCRIPT="$(cd "$(dirname "$SCRIPT")" && pwd)/$(basename "$SCRIPT")"; PRESETS="$(cd "$(dirname "$PRESETS")" && pwd)/$(basename "$PRESETS")"
exec $G/gpu_slot.sh capture --label combat --timeout 7200 -- bash -c '
  HERE="$1"; OUT="$2"; SCRIPT="$3"; SHOTS="$4"; PRESETS="$5"; export WHCMB_RES="$6" WHCMB_QUIT="$7"
  while IFS="|" read -r name spec; do
    [ -z "$name" ] && continue
    WHCMB_LOOK="$spec" "$HERE/run_fight.sh" stills "$OUT/$name" "$SCRIPT" "$SHOTS" > "$OUT/$name.out" 2>&1
    echo "look $name done"
  done < "$PRESETS"' _ "$HERE" "$OUT" "$SCRIPT" "$SHOTS" "$PRESETS" "$RES" "$QUIT"
