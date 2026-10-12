#!/bin/bash
# Round-04 1080p60 clips of the RUNNING lineup game, in three short fixed-step (-movie) runs instead of one 91 s run.
# Why: under a shared GPU the 91 s run took ~0.27 s per frame (~25 min holding a capture slot; it was running during the
# 16:43 WindowServer reset). Each segment starts the director at its first shot (-WHCharShot=N) and only renders what the
# round-04 shot list needs:
#   A  shot 1..3   hero run side (no hop) 6 | hero run 3/4 5 | hero run -> jump side 6.5                 (17.5 s)
#   B  shot 5..9   enemy lineup wide 6 | lineup 3/4 5 | thug+brute side 6 | thug 3 m 5 | brute 3 m 5     (27 s)
#   C  shot 15..16 civilians tracking 8 | civilians wide 6                                                (14 s)
# Face close-ups are native-4K stills (capture_4k_stills.sh group gE).
# usage: tools/ue_char/capture_segments.sh <out_dir> [A B C]      Fan homage project; not official Marvel/Sony/Insomniac.
set -e
WT="$(cd "$(dirname "$0")/../.." && pwd)"
P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"   # tools/ue_char/p2paths.py
GPU_SLOT="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"   # shared GPU lock (docs/night1/gpu/PROTOCOL.md)
OUT=${1:-$P2_SCRATCH/mov}; shift || true
SEGS="${*:-A B C}"
mkdir -p "$OUT"
seg_run() {   # name start_shot quit_s
  local FR="$OUT/seg$1_frames"
  if [ -d "$FR" ] && [ -n "$(ls "$FR" 2>/dev/null)" ]; then return; fi
  "$WT/tools/ue_char/ue_wait.sh"   # never a 4th+ Unreal instance (run_game.sh passes -RenderOffScreen -NoSound)
  ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' > "$OUT/seg$1_gpu_util_before.txt" || true
  ( cd "$WT/unreal/WebHomage" && "$GPU_SLOT" capture --label characters -- Scripts/run_game.sh "$OUT" -map /Game/Tests/Characters/Char_Lineup \
      -res 1920x1080 -quit "$3" -name "seg$1" -movie -timeout 2200 -- -WHCharShot="$2" < /dev/null | tail -4 )
}
cut_clip() {   # seg name start_s dur_s
  ffmpeg -loglevel error -y -framerate 60 -start_number $(python3 -c "print(int(round($3 * 60)))") -i "$OUT/seg$1_frames/MovieFrame%05d.png" \
    -frames:v $(python3 -c "print(int(round($4 * 60)))") -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "$OUT/$2.mp4"
}
cut_still() {  # seg name time_s
  ffmpeg -loglevel error -y -framerate 60 -start_number $(python3 -c "print(int(round($3 * 60)))") -i "$OUT/seg$1_frames/MovieFrame%05d.png" -frames:v 1 -q:v 2 "$OUT/$2.jpg"
}
# D = director start offset inside a segment (s): frames before the first shot's t=0 (loading); measured on the frames, override with SEG_OFFSET
D=${SEG_OFFSET:-0}
for s in $SEGS; do
  case $s in
    A) seg_run A 1 18.5
       cut_clip A hero_run_side $D 6; cut_clip A hero_run_34 $(python3 -c "print($D+6)") 5; cut_clip A hero_run_jump_side $(python3 -c "print($D+11)") 6.5 ;;
    B) seg_run B 5 28
       cut_clip B enemy_lineup $D 11; cut_clip B thug_brute_pair_side $(python3 -c "print($D+11)") 6
       cut_clip B thug_side_3m $(python3 -c "print($D+17)") 5; cut_clip B brute_side_3m $(python3 -c "print($D+22)") 5
       cut_still B enemy_lineup_1080 $(python3 -c "print($D+3)") ;;
    C) seg_run C 15 15
       cut_clip C civilians_tracking $D 8; cut_clip C civilians_wide $(python3 -c "print($D+8)") 6
       cut_still C civilians_tracking_1080 $(python3 -c "print($D+4)"); cut_still C civilians_wide_1080 $(python3 -c "print($D+11)") ;;
  esac
done
ls -la "$OUT"/*.mp4 "$OUT"/*.jpg 2>/dev/null
