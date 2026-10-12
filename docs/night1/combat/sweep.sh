#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02: run the reactive record script for several RNG seeds inside ONE gpu_slot capture hold (-nullrhi, one engine at a time)
# and write <out_root>/seed<N>/ for each; then pick the best with sweep_report.py.
#   sweep.sh <out_root> <record_script.json> <seed> [<seed> ...]
set -uo pipefail
OUT="$1"; SCRIPT="$2"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"
G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; SCRIPT="$(cd "$(dirname "$SCRIPT")" && pwd)/$(basename "$SCRIPT")"
exec $G/gpu_slot.sh capture --label combat --timeout 7200 -- bash -c '
  HERE="$1"; OUT="$2"; SCRIPT="$3"; shift 3
  for s in "$@"; do
    python3 -c "import json,sys;j=json.load(open(sys.argv[1]));j[\"seed\"]=int(sys.argv[2]);json.dump(j,open(sys.argv[3],\"w\"),indent=1)" "$SCRIPT" "$s" "$OUT/script_seed$s.json"
    "$HERE/run_fight.sh" logic "$OUT/seed$s" "$OUT/script_seed$s.json" > "$OUT/seed$s.out" 2>&1
    echo "seed $s: $(tail -n +2 "$OUT/seed$s.out" | head -c 100)"
  done' _ "$HERE" "$OUT" "$SCRIPT" "$@"
