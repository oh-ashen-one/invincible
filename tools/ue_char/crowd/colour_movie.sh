#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 08: native 3840x2160 frames of the COLOUR crowd (Char_Crowd), fixed 1/60 s steps, frame numbers line up with the id movie (id_movie.sh) and the clip, so a crowd still can be
# picked by frame number where head_overlap.py finds no head touching another walker.  Frames land in <out_dir>/segQ_frames (scratch, never committed).
#   tools/ue_char/crowd/colour_movie.sh <out_dir> [quit_s=6.0]
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT=${1:?out dir}; QUIT=${2:-6.0}; mkdir -p "$OUT"
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
cd "$WT/unreal/WebHomage"
"$WT/tools/ue_char/ue_wait.sh"
"$GPU" capture --label characters -- Scripts/run_game.sh "$OUT" -map /Game/Tests/Characters/Char_Crowd -res 3840x2160 -quit "$QUIT" -name segQ -movie \
   -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -timeout 3000 -- -WHCharShot=0 < /dev/null | tail -4
