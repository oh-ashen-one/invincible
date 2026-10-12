#!/bin/zsh
# One view, one resolution, one frame at t = 28 s (no perf window): usage: capture_one.sh <out_dir> <shot id> [WxH]
OUT=$1; ID=$2; RES=${3:-1920x1080}
mkdir -p "$OUT"
HERE=${0:A:h}   # (r07) worktree-relative: another worktree can run its own copy
"$HERE/ue/wait_slot.sh"
cd "$HERE/../../unreal/WebHomage"
${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh} capture --label city -- Scripts/run_game.sh "$OUT" -map /Game/Tests/City/City_View_$ID -res $RES -shots 28 -quit 30 -name ${ID%%_*}_$RES -timeout 900
