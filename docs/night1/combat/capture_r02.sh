#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02: freeze a chosen record run, replay it (nullrhi) to prove determinism, then record the 1080p60 movie and measure it.
# ONE gpu_slot capture hold for the whole chain (one engine at a time, sequential).
#   capture_r02.sh <work_dir> <record_run_dir> <record_script_with_seed.json> [still_times e.g. 3.05,5.08 -> native 4K stills at the end]
set -uo pipefail
WORK="$1"; REC="$2"; RSCRIPT="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$WORK"; WORK="$(cd "$WORK" && pwd)"; REC="$(cd "$REC" && pwd)"; RSCRIPT="$(cd "$(dirname "$RSCRIPT")" && pwd)/$(basename "$RSCRIPT")"; STILLS="${4:-}"
exec $G/gpu_slot.sh capture --label combat --timeout 7200 -- bash -c '
  HERE="$1"; WORK="$2"; REC="$3"; RSCRIPT="$4"; STILLS="$5"; WT="$(cd "$HERE/../../.." && pwd)"
  SM2_COMBAT_NOWAIT=1 python3 "$WT/unreal/WebHomage/Scripts/build_combat.py" --steps combat > "$WORK/map_build.out" 2>&1 || exit 4
  python3 "$HERE/freeze_script.py" "$RSCRIPT" "$REC/fight_beats.jsonl" "$HERE/scripts/fight30.json" || exit 3
  "$HERE/run_fight.sh" logic "$WORK/replay" "$HERE/scripts/fight30.json" > "$WORK/replay.out" 2>&1
  python3 "$HERE/replay_diff.py" "$REC" "$WORK/replay" | tee "$WORK/replay_diff.txt"
  "$HERE/run_fight.sh" movie "$WORK/movie" "$HERE/scripts/fight30.json" > "$WORK/movie.out" 2>&1
  python3 "$HERE/replay_diff.py" "$REC" "$WORK/movie" | tee "$WORK/movie_diff.txt"
  python3 "$HERE/measure_r02.py" "$WORK/movie" "$WORK/measure.md" "$WORK/measure.json" --sheet "$WORK/boxes.jpg" > "$WORK/measure.out" 2>&1
  if [ -n "$STILLS" ]; then
    "$HERE/run_fight.sh" stills "$WORK/stills" "$HERE/scripts/fight30.json" "$STILLS" > "$WORK/stills.out" 2>&1
    python3 "$HERE/replay_diff.py" "$REC" "$WORK/stills" | tee "$WORK/stills_diff.txt"
  fi
  echo "chain done"' _ "$HERE" "$WORK" "$REC" "$RSCRIPT" "$STILLS"
