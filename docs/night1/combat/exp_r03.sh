#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r03 experiment hold: map rebuild (new flare material), nullrhi record runs (sim numbers: victim push / twist / launch) and ONE 1080p60 movie of the
# reactive record script with -WHCmbSweep=1 (every blow gets the next shake px / Hz / flare-size variant, logged as 'variant' events) to calibrate the
# hit shake and flare size against the pixel tests. ONE gpu_slot hold, one engine at a time.
#   exp_r03.sh <work_dir> <movie_seed> <quit_s> [<sim seed> ...]
set -uo pipefail
WORK="$1"; MSEED="$2"; QUIT="$3"; shift 3
HERE="$(cd "$(dirname "$0")" && pwd)"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$WORK"; WORK="$(cd "$WORK" && pwd)"
exec $G/gpu_slot.sh capture --label combat --timeout 5400 -- bash -c '
  HERE="$1"; WORK="$2"; MSEED="$3"; QUIT="$4"; shift 4; WT="$(cd "$HERE/../../.." && pwd)"
  SM2_COMBAT_NOWAIT=1 python3 "$WT/unreal/WebHomage/Scripts/build_combat.py" --steps combat > "$WORK/map_build.out" 2>&1; echo "map build rc $?"
  for s in "$@"; do
    python3 -c "import json,sys;j=json.load(open(sys.argv[1]));j[\"seed\"]=int(sys.argv[2]);json.dump(j,open(sys.argv[3],\"w\"),indent=1)" "$HERE/scripts/fight30_record.json" "$s" "$WORK/script_seed$s.json"
    "$HERE/run_fight.sh" logic "$WORK/sim$s" "$WORK/script_seed$s.json" > "$WORK/sim$s.out" 2>&1; echo "sim seed $s done"
  done
  python3 -c "import json,sys;j=json.load(open(sys.argv[1]));j[\"seed\"]=int(sys.argv[2]);j[\"quit\"]=float(sys.argv[3]);json.dump(j,open(sys.argv[4],\"w\"),indent=1)" "$HERE/scripts/fight30_record.json" "$MSEED" "$QUIT" "$WORK/script_exp.json"
  WHCMB_EXTRA="-WHCmbSweep=1" "$HERE/run_fight.sh" movie "$WORK/exp" "$WORK/script_exp.json" > "$WORK/exp.out" 2>&1; echo "experiment movie done"
  echo "exp chain done"' _ "$HERE" "$WORK" "$MSEED" "$QUIT" "$@"
