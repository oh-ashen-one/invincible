#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r04: the whole capture in ONE gpu_slot hold (one engine at a time, sequential, nothing SIGKILLed):
#   1. map + materials rebuilt from the committed script (-nullrhi commandlet, no GPU)
#   2. movie A: the frozen fight30 with the r04 starburst, 1080p60, r.ScreenPercentage 100 (native internal resolution, checked by the WH_CMB_RES log line)
#   3. movie B: the SAME fight with -WHCmbFlare=0 (no starburst): |A - B| is exactly the flare (measure_r04.py)
#   4. native 3840x2160 stills of the shot list
# The sim is unchanged since r03 (recoil / starburst are visual only): both movies must replay the r03 record event for event (replay_diff.py).
#   final_r04.sh <work_dir> <still_times|auto> [record_dir]
set -uo pipefail
WORK="$1"; STILLS="$2"; HERE="$(cd "$(dirname "$0")" && pwd)"; REC="${3:-$HERE/round-03/ue/record}"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
mkdir -p "$WORK"; WORK="$(cd "$WORK" && pwd)"; REC="$(cd "$REC" && pwd)"
[ "$STILLS" = auto ] && STILLS=$(python3 "$HERE/still_times.py" "$REC")
echo "still times $STILLS"
# the outer hold may last long: raise the wrapper's max hold so that IT never SIGKILLs a healthy (or wedged) engine on a timer
export GPU_SLOT_CAPTURE_MAX_HOLD=5400
exec $G/gpu_slot.sh capture --label combat --timeout 14400 -- bash -c '
  HERE="$1"; WORK="$2"; REC="$3"; STILLS="$4"; WT="$(cd "$HERE/../../.." && pwd)"; SC="$HERE/scripts/fight30.json"
  date "+chain start %H:%M:%S"
  SM2_COMBAT_NOWAIT=1 python3 "$WT/unreal/WebHomage/Scripts/build_combat.py" --steps combat > "$WORK/map_build.out" 2>&1 || { echo "map build failed"; exit 4; }
  date "+map built %H:%M:%S"
  export WHCMB_EXEC="r.ScreenPercentage 100"
  "$HERE/run_fight.sh" movie "$WORK/movieA" "$SC" > "$WORK/movieA.out" 2>&1; echo "movie A done rc=$?"; date "+%H:%M:%S"
  grep -h "WH_CMB_RES" "$WORK/movieA/fight.log" | head -2
  python3 "$HERE/replay_diff.py" "$REC" "$WORK/movieA" | tee "$WORK/movieA_diff.txt"
  WHCMB_EXTRA="-WHCmbFlare=0" "$HERE/run_fight.sh" movie "$WORK/movieB" "$SC" > "$WORK/movieB.out" 2>&1; echo "movie B done rc=$?"; date "+%H:%M:%S"
  python3 "$HERE/replay_diff.py" "$REC" "$WORK/movieB" | tee "$WORK/movieB_diff.txt"
  if [ -n "$STILLS" ]; then
    "$HERE/run_fight.sh" stills "$WORK/stills" "$SC" "$STILLS" > "$WORK/stills.out" 2>&1; echo "stills done rc=$?"; date "+%H:%M:%S"
    grep -h "WH_CMB_RES" "$WORK/stills/still.log" | head -2
    python3 "$HERE/replay_diff.py" "$REC" "$WORK/stills" | tee "$WORK/stills_diff.txt"
  fi
  echo "chain done"' _ "$HERE" "$WORK" "$REC" "$STILLS"
