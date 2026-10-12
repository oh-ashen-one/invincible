#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r03 captures, driver v2 (replaces holds_r03.sh at 11:27 without losing the queue place of its hold-1 waiter): waits for that
# waiter (pid $1) to end; if hold 1 never ran (gpu_slot exit 75: wait timed out) it is re-queued; then holds 2 and 3. Every re-queue waits
# up to 3 h in the FIFO (GPU_SLOT_CAPTURE_WAIT_TIMEOUT=10800) instead of 1 h, so a timeout does not send the hold to the back of the queue.
set -u
WT=/Users/midir/sm2-n1/island
ROUND=$WT/docs/night1/island/round-03
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
LOG=/Users/midir/sm2-n1/_scratch/island/logs/holds_r03.log
export GPU_SLOT_CAPTURE_WAIT_TIMEOUT=10800
hold() {  # name runs...
  local NAME="$1"; shift
  for try in 1 2 3; do
    echo "$(date +%T) hold '$NAME' try $try: $*" >> "$LOG"
    ISLAND_IN_LOCK=1 "$GPU" capture --label island --json "$ROUND/gpu_hold_${NAME// /_}.json" -- "$WT/docs/night1/island/capture_round.sh" "$ROUND" "$@" >> "$LOG" 2>&1
    local rc=$?
    echo "$(date +%T) hold '$NAME' rc $rc" >> "$LOG"
    [ $rc -ne 75 ] && return $rc
  done
}
W="${1:-}"
if [ -n "$W" ]; then
  while kill -0 "$W" 2>/dev/null; do sleep 10; done
  if grep -q "== r2_south_avenue" "$LOG"; then echo "$(date +%T) hold 'warmup r2' ran under the first driver" >> "$LOG"; else hold "warmup r2" warmup r2; fi
else
  hold "warmup r2" warmup r2
fi
hold "r1 r3" r1 r3
hold "r4 a1" r4 a1
echo "$(date +%T) all holds done" >> "$LOG"
