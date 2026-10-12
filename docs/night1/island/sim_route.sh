#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A): telemetry-only route run of the REAL game on /Game/Maps/Manhattan_WP with NO renderer (-nullrhi), fixed 1/60 s step
# (-benchmark -fps=60), through the GPU lock. Used to iterate a route script cheaply; the kept movie / telemetry always come from a rendered
# capture (capture_round.sh). round-03/README.md compares a nullrhi run with a rendered one.
# usage: docs/night1/island/sim_route.sh <out_dir> <route.json> [quit_s]
set -uo pipefail
OUT="$1"; J="$2"; Q="${3:-30.4}"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"; WT="$(cd "$HERE/../../.." && pwd)"; UE_DIR="$WT/unreal/WebHomage"
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
N=$(basename "${J%.json}")
LOCK=("$GPU" capture --label island --); [ -n "${ISLAND_IN_LOCK:-}" ] && LOCK=()
WH_CAPTURE_MAXFPS=${WH_CAPTURE_MAXFPS:-240} ${LOCK[@]+"${LOCK[@]}"} "$UE_DIR/Scripts/run_game.sh" "$OUT/$N" -map /Game/Maps/Manhattan_WP -res 640x360 -quit "$Q" -name "$N" -timeout 1500 \
   -- -benchmark -fps=60 -nullrhi -WHTravScript="$J" -WHTravCsv="$OUT/$N/${N}_telemetry.csv" | tail -3
grep -h "WebTravWorld:" "$OUT/$N/$N.log" | sed 's/^.*Display: //' | head -3
echo "done: $OUT/$N"
