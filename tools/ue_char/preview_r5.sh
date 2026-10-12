#!/bin/bash
# Quick real-time 1920x1080 stills for a look at a round-05 map (not evidence): tools/ue_char/preview_r5.sh OUT MAP START_SHOT TIME NAME
# Fan homage project; not official Marvel/Sony/Insomniac.
set -e
WT="$(cd "$(dirname "$0")/../.." && pwd)"
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
OUT=$1; MAP=$2; START=$3; T=$4; NAME=$5; QUIT=$(python3 -c "print(float('$T')+3)")
mkdir -p "$OUT"; cd "$WT/unreal/WebHomage"
"$WT/tools/ue_char/ue_wait.sh"
"$GPU" capture --label characters -- Scripts/run_game.sh "$OUT" -map /Game/Tests/Characters/$MAP -res 1920x1080 -shots "$T" -quit "$QUIT" -name "$NAME" -timeout 900 -- -WHCharShot="$START" < /dev/null | tail -3
