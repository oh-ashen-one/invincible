#!/bin/bash
# Round 09: bone log of the scripted fight WITHOUT rendering: a fixed-step (-benchmark -fps=60) -nullrhi run of Char_Fight that only writes -WHBoneLog (hips / spine2 / head / hands / feet of every
# walker at 60 Hz) for fight_check.py / contact_check.py.  Same script, same stage clock as the movie runs; no GPU work, still one engine through the lock.
# Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.
#   tools/ue_char/fight/bone_log_run.sh <out_dir>      -> <out_dir>/fight_bones.csv (+ bonelog.log)
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT=${1:?out dir}; mkdir -p "$OUT"
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
rm -f "$OUT/fight_bones.csv"
"$GPU" capture --label characters -- "$UE" "$WT/unreal/WebHomage/WebHomage.uproject" /Game/Tests/Characters/Char_Fight -game -nullrhi -NoSound -NoCrashReports -WHNoMouseCapture \
  -ResX=640 -ResY=360 -ForceRes -benchmark -fps=60 -WHCharShot=0 -WHBoneLog="$OUT/fight_bones.csv" -WHQuitAt=25 -abslog="$OUT/bonelog.log" -ExecCmds="t.MaxFPS 0" > "$OUT/bonelog.stdout.txt" 2>&1 < /dev/null
echo "bone_log_run exit=$? rows=$(wc -l < "$OUT/fight_bones.csv" 2>/dev/null)"
