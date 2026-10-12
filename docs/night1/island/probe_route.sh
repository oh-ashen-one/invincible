#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A): rendered still probe of a route (no movie): 1920x1080 stills at the road-band test seconds (default 12,20,26,28) from the same
# fixed-step run (-benchmark -fps=60: the sim is the movie run's), through the GPU lock, then island_road_band.py on the PNGs.
# usage: docs/night1/island/probe_route.sh <out_dir> <route.json> [shots]
set -uo pipefail
OUT="$1"; J="$2"; SH="${3:-12,20,26,28}"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"; WT="$(cd "$HERE/../../.." && pwd)"; UE_DIR="$WT/unreal/WebHomage"
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
N=$(basename "${J%.json}")
LOCK=("$GPU" capture --label island --); [ -n "${ISLAND_IN_LOCK:-}" ] && LOCK=()
Q=$(python3 -c "print(max(map(float,'$SH'.split(',')))+0.6)")
${LOCK[@]+"${LOCK[@]}"} "$UE_DIR/Scripts/run_game.sh" "$OUT/$N" -map /Game/Maps/Manhattan_WP -res 1920x1080 -shots "$SH" -quit "$Q" -name "$N" -timeout 1500 \
   -- -benchmark -fps=60 -WHTravScript="$J" -WHTravCsv="$OUT/$N/${N}_telemetry.csv" | tail -3
python3 "$WT/tools/export/island_road_band.py" "$OUT/$N"/${N}_*.png --json "$OUT/$N/road_band.json"
echo "done: $OUT/$N"
