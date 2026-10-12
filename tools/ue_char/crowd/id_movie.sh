#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 07: per-walker id movie of the crowd tracking shot (Char_CrowdID: each citizen's pixels carry its own colour, everything else is black), 1080p60 fixed-step frames
# that line up frame for frame with crowd_tracking.mp4 (same walker paths, same director clock).  Frames stay in <out_dir>/segD_frames (scratch, never committed).
#   tools/ue_char/crowd/id_movie.sh <out_dir>
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT=${1:?out dir}; mkdir -p "$OUT"
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
cd "$WT/unreal/WebHomage"
"$WT/tools/ue_char/ue_wait.sh"
"$GPU" capture --label characters -- Scripts/run_game.sh "$OUT" -map /Game/Tests/Characters/Char_CrowdID -res 1920x1080 -quit 9.5 -name segD -movie \
   -exec "r.MotionBlurQuality 0,r.CustomDepth 3" -timeout 3000 -- -WHCharShot=0 < /dev/null | tail -4
