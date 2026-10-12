#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 07: walker telemetry of a crowd map, no renderer (-nullrhi), fixed 1/60 s steps, through the GPU lock like every other Unreal launch.
#   tools/ue_char/crowd/run_telemetry.sh <out_dir> <map e.g. /Game/Tests/Characters/Char_Crowd> <tag> [quit_s=15]
# Writes <out_dir>/<tag>_walkers.csv (AWHCharLoopWalker -WHWalkerLog) and <out_dir>/<tag>_telemetry.log; then run tools/ue_char/crowd/telemetry_check.py on the csv.
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT=${1:?out dir}; MAP=${2:?map}; TAG=${3:?tag}; QUIT=${4:-15}
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
"$WT/tools/ue_char/ue_wait.sh"
"$GPU" capture --label characters -- "$UE" "$WT/unreal/WebHomage/WebHomage.uproject" "$MAP" -game -nullrhi -NoSound -NoCrashReports -NoVSync -WHNoMouseCapture \
  -WHQuitAt="$QUIT" -benchmark -fps=60 -WHWalkerLog="$OUT/${TAG}_walkers.csv" -abslog="$OUT/${TAG}_telemetry.log" -ExecCmds="t.MaxFPS 0" ${WHX:-} < /dev/null > "$OUT/${TAG}_telemetry.stdout.txt" 2>&1
echo "run_telemetry exit $?"; ls -la "$OUT/${TAG}_walkers.csv" 2>&1 | tail -1
