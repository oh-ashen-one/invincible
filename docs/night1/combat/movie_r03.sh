#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r03: re-capture the frozen fight with a choice of two hit-feel settings in ONE gpu_slot hold: movie A (code defaults) and movie B (WHCMB_EXTRA_B flags),
# both measured on the crf-18 master with measure_r03.py, the setting with more 'good_run >= 3' blows wins (ties: more 'crop_run >= 3'), then the 10 native-4K stills
# are taken with the winner's flags.  The record run (event log to compare with) is the seed sweep pick.
#   movie_r03.sh <work_dir> <record_run_dir> "<flags for B>" <still_times>
set -uo pipefail
WORK="$1"; REC="$2"; XB="$3"; STILLS="$4"
HERE="$(cd "$(dirname "$0")" && pwd)"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$WORK"; WORK="$(cd "$WORK" && pwd)"; REC="$(cd "$REC" && pwd)"
exec $G/gpu_slot.sh capture --label combat --timeout 7200 -- bash -c '
  HERE="$1"; WORK="$2"; REC="$3"; XB="$4"; STILLS="$5"; SC="$HERE/scripts/fight30.json"
  SM2_COMBAT_NOWAIT=1 python3 "$(cd "$HERE/../../.." && pwd)/unreal/WebHomage/Scripts/build_combat.py" --steps combat > "$WORK/map_build.out" 2>&1 || exit 4
  "$HERE/run_fight.sh" movie "$WORK/movieA" "$SC" > "$WORK/movieA.out" 2>&1; echo "movie A done"
  python3 "$HERE/measure_r03.py" "$WORK/movieA" "$WORK/mA.md" "$WORK/mA.json" --label "A defaults" > "$WORK/mA.out" 2>&1; rm -rf "$WORK/movieA/fight_frames"
  WHCMB_EXTRA="$XB" "$HERE/run_fight.sh" movie "$WORK/movieB" "$SC" > "$WORK/movieB.out" 2>&1; echo "movie B done"
  python3 "$HERE/measure_r03.py" "$WORK/movieB" "$WORK/mB.md" "$WORK/mB.json" --label "B $XB" > "$WORK/mB.out" 2>&1; rm -rf "$WORK/movieB/fight_frames"
  PICK=$(python3 "$HERE/pick_movie.py" "$WORK" | tee "$WORK/pick.txt" | tail -1); cat "$WORK/pick.txt"
  if [ "$PICK" = B ]; then export WHCMB_EXTRA="$XB"; else unset WHCMB_EXTRA; fi
  "$HERE/run_fight.sh" stills "$WORK/stills" "$SC" "$STILLS" > "$WORK/stills.out" 2>&1
  python3 "$HERE/replay_diff.py" "$REC" "$WORK/movie$PICK" | tee "$WORK/movie_diff.txt"
  echo "movie chain done"' _ "$HERE" "$WORK" "$REC" "$XB" "$STILLS"
