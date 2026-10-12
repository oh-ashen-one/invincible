#!/bin/bash
# Capture the RUNNING lineup game (/Game/Tests/Characters/Char_Lineup) with F1's Scripts/run_game.sh.
# One fixed-step (-movie, 60 fps) 1080p run of the whole 90.5 s director cycle, then ffmpeg cuts the per-shot clips
# (H.264 <= 15 MB) and stills. One launch instead of one per clip (owner rule: few Unreal instances, wait when 3+ run).
# Round-04 cycle (cumulative s): 0 hero turntable 6 | 6 hero run side (no hop) 6 | 12 hero run 3/4 5 | 17 hero run -> jump side 6.5 |
# 23.5 suit close-up 4 | 27.5 enemy lineup wide 6 | 33.5 enemy lineup 3/4 5 | 38.5 thug+brute side 4.2 m 6 | 44.5 thug 3 m 5 |
# 49.5 brute 3 m 5 | 54.5 thug face 4 | 58.5 brute face 4 | 62.5 hood face 3 | 65.5 tee face 3 | 68.5 beard face 3 |
# 71.5 civilians tracking 8 | 79.5 civilians wide 6 | 85.5 AI suits 5 (ends 90.5)
# usage: tools/ue_char/capture_lineup.sh <out_dir>        Fan homage project; not official Marvel/Sony/Insomniac.
set -e
WT="$(cd "$(dirname "$0")/../.." && pwd)"
P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"   # tools/ue_char/p2paths.py
GPU_SLOT="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"   # shared GPU lock (docs/night1/gpu/PROTOCOL.md)
OUT=${1:-$P2_SCRATCH/mov}
mkdir -p "$OUT"
FR="$OUT/lineup_frames"
if [ ! -d "$FR" ] || [ -z "$(ls "$FR" 2>/dev/null)" ]; then
  "$WT/tools/ue_char/ue_wait.sh"   # owner rule: never a 3rd+ Unreal instance (run_game.sh passes -RenderOffScreen -NoSound)
  cd "$WT/unreal/WebHomage"
  # owner rule: every game capture goes through the shared GPU lock (max 2 slots, protocol docs/night1/gpu/PROTOCOL.md)
  "$GPU_SLOT" capture --label characters -- Scripts/run_game.sh "$OUT" -map /Game/Tests/Characters/Char_Lineup -res 1920x1080 -quit 91 -name lineup -movie -timeout 5400 -- -WHCharShot=0 < /dev/null | tail -3
fi
cut_clip() {   # name start_s dur_s
  ffmpeg -loglevel error -y -framerate 60 -start_number $(python3 -c "print(int(round($2 * 60)))") -i "$FR/MovieFrame%05d.png" -frames:v $(python3 -c "print(int(round($3 * 60)))") \
    -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "$OUT/$1.mp4"
}
cut_still() {  # name time_s
  ffmpeg -loglevel error -y -framerate 60 -start_number $(python3 -c "print(int(round($2 * 60)))") -i "$FR/MovieFrame%05d.png" -frames:v 1 -q:v 2 "$OUT/$1.jpg"
}
cut_clip hero_turntable_walk 0 6
cut_clip hero_run_side 6 6
cut_clip hero_run_34 12 5
cut_clip hero_run_jump_side 17 6.5
cut_clip hero_suit_fabric_closeup 23.5 4
cut_clip enemy_lineup 27.5 11
cut_clip thug_brute_pair_side 38.5 6
cut_clip thug_side_3m 44.5 5
cut_clip brute_side_3m 49.5 5
cut_clip enemy_faces 54.5 17
cut_clip civilians_tracking 71.5 8
cut_clip civilians_wide 79.5 6
cut_clip ai_suits_walk 85.5 5
cut_still enemy_lineup_1080 30.5
cut_still civilians_tracking_1080 75.5
cut_still civilians_wide_1080 82.5
ls -la "$OUT"/*.mp4 "$OUT"/*.jpg
