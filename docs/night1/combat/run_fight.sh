#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat: run the scripted fight in /Game/Tests/Combat/Combat_Street.
#   run_fight.sh logic  <out_dir> <script.json>               -game -nullrhi (no GPU, no window, still inside gpu_slot.sh): logic + telemetry only
#   run_fight.sh movie  <out_dir> <script.json> [WxH]         1080p60 -dumpmovie through Scripts/run_game.sh inside gpu_slot.sh capture
#   run_fight.sh stills <out_dir> <script.json> t1,t2,...     native 4K stills (r.ScreenPercentage 100) inside gpu_slot.sh capture
# Deterministic: -benchmark -fps=60 (fixed 1/60 s step), seeded RNG in the director.
set -uo pipefail
MODE="$1"; OUT="$2"; SCRIPT="$3"; ARG4="${4:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
WT="$(cd "$HERE/../../.." && pwd)"
PROJ="$WT/unreal/WebHomage"; UPROJECT="$PROJ/WebHomage.uproject"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
G=/Users/midir/sm2-n1/_scratch/gpu/bin
MAP=/Game/Tests/Combat/Combat_Street
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; SCRIPT="$(cd "$(dirname "$SCRIPT")" && pwd)/$(basename "$SCRIPT")"
LOOK="${WHCMB_LOOK:-}"; LOOKARG=(); [ -n "$LOOK" ] && LOOKARG=(-WHCmbLook="$LOOK")
# r03: WHCMB_EXTRA = extra director flags (e.g. "-WHCmbSweep=1 -WHCmbShakePx=3 -WHCmbFlareK=1.2"), word-split on purpose
if [ -n "${WHCMB_EXTRA:-}" ]; then read -r -a XARG <<< "$WHCMB_EXTRA"; LOOKARG+=("${XARG[@]}"); fi
QUIT=$(python3 -c "import json;print(json.load(open('$SCRIPT')).get('quit',30))")
if pgrep -f "$UPROJECT" >/dev/null; then echo "an Unreal process of this worktree is running"; exit 2; fi
# (r02: no own instance-count wait: gpu_slot.sh enforces the auto-tuned cap and queues FIFO)
case "$MODE" in
  logic)
    # r02: through the GPU lock as well (RULES: every Unreal launch), although -nullrhi uses no GPU
    $G/gpu_slot.sh capture --label combat --timeout 3600 -- "$UE" "$UPROJECT" "$MAP" -game -nullrhi -NoSound -NoCrashReports -benchmark -fps=60 -unattended -WHNoMouseCapture \
      -WHCmbScript="$SCRIPT" -WHCmbOut="$OUT" -WHCmbShotName=fight ${LOOKARG[@]+"${LOOKARG[@]}"} -abslog="$OUT/fight.log" > "$OUT/stdout.txt" 2>&1
    echo "rc $?"
    grep -o 'WH_CMB_SUMMARY.*' "$OUT/fight.log" | head -1 ;;
  movie)
    RES="${ARG4:-1920x1080}"
    # r04: WHCMB_EXEC = console commands for the game (e.g. "r.ScreenPercentage 100" = native internal resolution); the run's own timeout is 5400 s so run_game.sh
    # never SIGKILLs a rendering engine on its own (a wedged engine is stopped by hand with stop_ue.sh)
    EXARG=(); [ -n "${WHCMB_EXEC:-}" ] && EXARG=(-exec "$WHCMB_EXEC")
    $G/gpu_slot.sh capture --label combat --timeout 3600 -- "$PROJ/Scripts/run_game.sh" "$OUT" -map "$MAP" -res "$RES" -quit 400 -name fight -movie -timeout 5400 ${EXARG[@]+"${EXARG[@]}"} \
      -- -WHCmbScript="$SCRIPT" -WHCmbOut="$OUT" -WHCmbShotName=fight ${LOOKARG[@]+"${LOOKARG[@]}"}
    echo "rc $?" ;;
  stills)
    # WHCMB_RES (default 3840x2160 native) and WHCMB_QUIT (game s to stop at) are for quick look tests; r.ScreenPercentage 100 always
    QARG=(); [ -n "${WHCMB_QUIT:-}" ] && QARG=(-WHCmbQuit="$WHCMB_QUIT")
    $G/gpu_slot.sh capture --label combat --timeout 3600 -- "$PROJ/Scripts/run_game.sh" "$OUT" -map "$MAP" -res "${WHCMB_RES:-3840x2160}" -quit 400 -name still -timeout 5400 \
      -exec "r.ScreenPercentage 100" -- -benchmark -fps=60 -WHCmbScript="$SCRIPT" -WHCmbOut="$OUT" -WHCmbShotName=still -WHCmbShots="$ARG4" ${LOOKARG[@]+"${LOOKARG[@]}"} ${QARG[@]+"${QARG[@]}"}
    echo "rc $?" ;;
  *) echo "mode: logic | movie | stills"; exit 1 ;;
esac
# r02 (RULES, 2026-09-29 23:08 panic): never SIGKILL a rendering engine. A run that has not exited by now is stopped with stop_ue.sh
# (driver scripts first, SIGTERM, wait 60 s). The bracketed pattern cannot match this shell's own command line.
if pgrep -f "$UPROJECT" >/dev/null; then
  echo "engine of this worktree still running after the run: stop_ue.sh"
  $G/stop_ue.sh "$(printf '%s' "$WT" | sed 's|/\([^/]\)|/[\1]|g')/unreal"
fi
pgrep -f "CrashReportClient.*$WT" >/dev/null && pkill -f "CrashReportClient.*$WT"
exit 0
