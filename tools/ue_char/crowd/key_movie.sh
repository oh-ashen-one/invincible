#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 07: native 3840x2160 frames of the stencil-keyed crowd (Char_CrowdKey), fixed 1/60 s steps: every frame is reproducible and lines up with the id movie (id_movie.sh)
# and the crowd clip, so a key still can be picked by frame number (e.g. one where no near-lane walker touches another silhouette).  Frames land in <out_dir>/segK_frames (scratch).
#   tools/ue_char/crowd/key_movie.sh <out_dir> [quit_s=4.4]
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT=${1:?out dir}; QUIT=${2:-4.4}; mkdir -p "$OUT"
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
cd "$WT/unreal/WebHomage"
"$WT/tools/ue_char/ue_wait.sh"
"$GPU" capture --label characters -- Scripts/run_game.sh "$OUT" -map /Game/Tests/Characters/Char_CrowdKey -res 3840x2160 -quit "$QUIT" -name segK -movie \
   -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0,r.CustomDepth 3" -timeout 3000 -- -WHCharShot=0 < /dev/null | tail -4
