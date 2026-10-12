#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02: the whole capture in ONE gpu_slot hold: map rebuild + seed sweep (-nullrhi), automatic seed pick, freeze, 1080p60 movie + measure, native 4K stills.
#   final_r02.sh <work_dir> <still_times> <seed> [<seed> ...]
set -uo pipefail
WORK="$1"; STILLS="$2"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$WORK"; WORK="$(cd "$WORK" && pwd)"
exec $G/gpu_slot.sh capture --label combat --timeout 7200 -- bash -c '
  HERE="$1"; WORK="$2"; STILLS="$3"; shift 3
  "$HERE/prep_r02.sh" "$WORK/sweep" "$HERE/scripts/fight30_record.json" "$@"
  SEED=$(python3 "$HERE/pick_seed.py" "$WORK/sweep"); echo "picked seed $SEED"
  if [ "$STILLS" = auto ]; then STILLS=$(python3 "$HERE/still_times.py" "$WORK/sweep/seed$SEED"); echo "still times $STILLS"; fi
  "$HERE/capture_r02.sh" "$WORK/cap" "$WORK/sweep/seed$SEED" "$WORK/sweep/script_seed$SEED.json" "$STILLS"
  echo "final chain done"' _ "$HERE" "$WORK" "$STILLS" "$@"
