#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A): telemetry-only route runs (no movie, 960x540, fixed 1/60 s step via -benchmark -fps=60) of the REAL game on a given map,
# every run through the GPU lock, then island_route_check.py.  Used to A/B a collision build (e.g. SM2_WHBOX_MODE=ism) before it replaces
# /Game/Maps/Manhattan_WP.
# usage: docs/night1/island/verify_map.sh <map> <out_dir> [route ...]      routes: r1 r2 r3 r4 (script names in scripts/)
set -uo pipefail
MAP="$1"; OUT="$2"; shift 2; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"; WT="$(cd "$HERE/../../.." && pwd)"; UE_DIR="$WT/unreal/WebHomage"; SCR="$HERE/scripts"
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
EXPORT=/Users/midir/sm2-n1/_scratch/island/export/midtown
CSVS=()
for R in "$@"; do
  J=$(ls "$SCR"/${R}_*.json | head -1); N=$(basename "${J%.json}")
  echo "== $N on $MAP"
  rm -rf "$OUT/$N"
  LOCK=("$GPU" capture --label island --); [ -n "${ISLAND_IN_LOCK:-}" ] && LOCK=()   # caller holds the slot for the batch
  "${LOCK[@]}" "$UE_DIR/Scripts/run_game.sh" "$OUT/$N" -map "$MAP" -res 960x540 -shots 12 -quit 30.4 -name "$N" -timeout 1500 \
     -- -benchmark -fps=60 -WHTravScript="$J" -WHTravCsv="$OUT/$N/${N}_telemetry.csv" | tail -2
  grep -h "WebTravWorld:" "$OUT/$N/$N.log" | sed 's/^.*Display: //' | head -3
  [ -f "$OUT/$N/${N}_telemetry.csv" ] && CSVS+=("$OUT/$N/${N}_telemetry.csv")
done
[ ${#CSVS[@]} -gt 0 ] && python3 "$WT/tools/export/island_route_check.py" "$EXPORT" "${CSVS[@]}" --out "$OUT/route_check.json" | tail -$(( ${#CSVS[@]} + 1 ))
echo "done: $OUT"
