#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r03: rebuild /Game/Tests/Combat/Combat_Street from the committed script (headless commandlet) and run the seed sweep, in ONE gpu_slot hold.
#   prep_r03.sh <out_root> <record_script.json> <seed> [<seed> ...]
set -uo pipefail
OUT="$1"; SCRIPT="$2"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"; WT="$(cd "$HERE/../../.." && pwd)"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; SCRIPT="$(cd "$(dirname "$SCRIPT")" && pwd)/$(basename "$SCRIPT")"
exec $G/gpu_slot.sh capture --label combat --timeout 7200 -- bash -c '
  HERE="$1"; WT="$2"; OUT="$3"; SCRIPT="$4"; shift 4
  SM2_COMBAT_NOWAIT=1 python3 "$WT/unreal/WebHomage/Scripts/build_combat.py" --steps combat > "$OUT/map_build.out" 2>&1; echo "map build rc $?"
  for s in "$@"; do
    python3 -c "import json,sys;j=json.load(open(sys.argv[1]));j[\"seed\"]=int(sys.argv[2]);json.dump(j,open(sys.argv[3],\"w\"),indent=1)" "$SCRIPT" "$s" "$OUT/script_seed$s.json"
    "$HERE/run_fight.sh" logic "$OUT/seed$s" "$OUT/script_seed$s.json" > "$OUT/seed$s.out" 2>&1
    echo "seed $s done"
  done
' _ "$HERE" "$WT" "$OUT" "$SCRIPT" "$@"
