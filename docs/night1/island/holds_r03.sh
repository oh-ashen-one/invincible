#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r03 captures: three GPU holds (one capture slot each, max hold 2,400 s), queued one after another.
#   hold 1: warmup (shader / DDC compile + prims dump) + r2 (the round's pass route)
#   hold 2: r1 + r3      hold 3: r4 + a1 (4K stills, 8 fps cap in run_game.sh)
# A hold that times out in the queue (gpu_slot exit 75: not run, e.g. while PAUSED) is re-queued; any other result moves on.
# Stop: kill this script's PID first (_scratch/island/holds_r03.pid), then stop_ue.sh /Users/midir/sm2-n1/island
set -u
WT=/Users/midir/sm2-n1/island
ROUND=$WT/docs/night1/island/round-03
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
LOG=/Users/midir/sm2-n1/_scratch/island/logs/holds_r03.log
hold() {  # name runs...
  local NAME="$1"; shift
  for try in 1 2 3 4 5 6; do
    echo "$(date +%T) hold '$NAME' try $try: $*" >> "$LOG"
    ISLAND_IN_LOCK=1 "$GPU" capture --label island --json "$ROUND/gpu_hold_${NAME// /_}.json" -- "$WT/docs/night1/island/capture_round.sh" "$ROUND" "$@" >> "$LOG" 2>&1
    local rc=$?
    echo "$(date +%T) hold '$NAME' rc $rc" >> "$LOG"
    [ $rc -ne 75 ] && return $rc
  done
}
hold "warmup r2" warmup r2
hold "r1 r3" r1 r3
hold "r4 a1" r4 a1
echo "$(date +%T) all holds done" >> "$LOG"
