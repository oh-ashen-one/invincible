#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r02 capture driver: waits for the r02 rebuild (build_manhattan.py, PID in _scratch/island/build_r02.pid) to finish OK, then runs the
# round's captures in three GPU-lock holds (one heavy renderer at a time; every engine run goes through gpu_slot.sh, max hold 2400 s):
#   hold 1: warmup (+ traversal primitive dump) + r3 crosstown east (critic test 1)
#   hold 2: r4 wall-run / roofs (critic test 2) + r1 north avenue
#   hold 3: r2 south avenue + r1 -WHTravIsmSolid=1 A/B (telemetry) + a1 4K stills
# Stops after 2 engine runs without a WH_QUIT line (crash rule) or a lock wait timeout (exit 75). Log: _scratch/island/logs/holds_r02.log
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
R="$HERE/round-02"; CAP="$HERE/capture_round.sh"
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
TMP=/Users/midir/sm2-n1/_scratch/island/capture
BLOG=/Users/midir/sm2-n1/_scratch/island/logs/build_r02.log
BPID=$(cat /Users/midir/sm2-n1/_scratch/island/build_r02.pid 2>/dev/null)
if [ -n "${BPID:-}" ]; then while kill -0 "$BPID" 2>/dev/null; do sleep 30; done; fi
grep -q "all done" "$BLOG" || { echo "$(date +%T) rebuild did not finish OK (see $BLOG): no captures"; exit 1; }
echo "$(date +%T) rebuild OK: $(tail -1 "$BLOG")"
mkdir -p "$R"
CRASH=0
for batch in "warmup r3" "r4 r1" "r2 ab a1"; do
  echo "$(date +%T) queue hold: $batch  ($(ls /Users/midir/sm2-n1/_scratch/gpu/PAUSED 2>/dev/null && echo PAUSED))"
  ISLAND_IN_LOCK=1 "$GPU" capture --label island --timeout 21600 --json "$R/gpu_hold_${batch// /_}.json" -- "$CAP" "$R" $batch
  rc=$?
  echo "$(date +%T) hold '$batch' rc $rc"
  [ $rc -eq 75 ] && { echo "lock wait timed out"; exit 75; }
  for n in $batch; do
    case $n in warmup) L=warmup;; r1) L=r1_north_avenue;; r2) L=r2_south_avenue;; r3) L=r3_crosstown_east;; r4) L=r4_wallrun_roofs;; ab) L=r1_ism_solid;; *) continue;; esac
    if ! grep -q "WH_QUIT" "$TMP/$L/$L.log" 2>/dev/null; then CRASH=$((CRASH + 1)); echo "$(date +%T) $L: no WH_QUIT (crash / kill #$CRASH)"; fi
  done
  [ $CRASH -ge 2 ] && { echo "2 engine runs failed: stop (RULES.md)"; exit 2; }
done
echo "$(date +%T) all holds done"
