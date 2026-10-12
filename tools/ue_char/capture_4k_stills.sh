#!/bin/bash
# NATIVE 3840x2160 stills of the RUNNING lineup game (real-time run, not -movie). Fan homage project; not official Marvel/Sony/Insomniac.
#   tools/ue_char/capture_4k_stills.sh <out_dir>
# r.MotionBlurQuality 0: stills only (the movies keep motion blur). r.ScreenPercentage 100: the default auto percentage renders 2160p output at 1920x1080 internal and upscales it (round-02 critic).
# Timing: the director's clock runs SLOWER than the automation clock that -shots uses (about 1.5 s behind at t=5 s and about 5 s behind at
# t=66 s at 23 fps), so long runs drift out of their shots. Each group below therefore starts the director at its own shot (-WHCharShot=N)
# and keeps every still within ~20 s of the start: still time = ~1.5 s start offset + a time inside the shot.
set -e
WT="$(cd "$(dirname "$0")/../.." && pwd)"
P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"   # tools/ue_char/p2paths.py
OUT=${1:-$P2_SCRATCH/stills4k}
mkdir -p "$OUT"
ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | tee "$OUT/gpu_util_before.txt"   # shared GPU: report next to any frame time
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"         # owner rule: every game capture goes through the shared GPU lock (max 2 slots)
cd "$WT/unreal/WebHomage"
# group: start_shot | still times (s) | quit | names (one per still)
run_group() {
  local start="$1" shots="$2" quit="$3" tag="$4"; shift 4
  if [ -n "$ONLY" ]; then case " $ONLY " in *" $tag "*) ;; *) return 0;; esac; fi   # ONLY="gC gE" runs a subset
  "$WT/tools/ue_char/ue_wait.sh"          # owner rule: never a 3rd+ Unreal instance (run_game.sh passes -RenderOffScreen -NoSound)
  "$GPU" capture --label characters -- Scripts/run_game.sh "$OUT" -map /Game/Tests/Characters/Char_Lineup -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" \
    -shots "$shots" -perf 3:$(( quit - 1 )) -quit "$quit" -name "$tag" -timeout 3600 -- -WHCharShot="$start" < /dev/null | tail -12
  local i=0
  for f in "$OUT"/${tag}_[0-9][0-9]_t*.png; do
    ffmpeg -loglevel error -y -i "$f" -q:v 2 "$OUT/${1}_4k.jpg"; shift; rm -f "$f"
  done
}
# round-04 shot indices: 0 turntable, 1 hero run side, 2 hero run 3/4, 3 run -> jump, 4 suit close-up, 5 lineup wide, 6 lineup 3/4,
# 7 thug+brute 4.2 m, 8 thug 3 m, 9 brute 3 m, 10 thug face, 11 brute face, 12 hood face, 13 tee face, 14 beard face, 15 civilians tracking,
# 16 civilians wide, 17 AI suits
run_group 0  "4.5,10.5,16"            18 gA hero_turntable hero_run_side hero_run_34
run_group 3  "2.95,3.4,10"            11 gB hero_takeoff hero_jump suit_closeup
run_group 5  "4.5,10"                 12 gC enemy_lineup_wide enemy_lineup_34
run_group 7  "4.5,10,15"              17 gD thug_brute_pair_side thug_side_3m brute_side_3m
run_group 10 "3.5,7.5"                10 gE thug_face brute_face
# 3 s face shots drift out of their window when started from shot 10: one short run per face (round 04b)
run_group 12 "3.0"                    6  gE2 hood_face
run_group 13 "3.0"                    6  gE3 tee_face
run_group 14 "3.0"                    6  gE4 beard_face
run_group 15 "5.5,12.5"               14 gF civilians_tracking civilians_wide
ls -la "$OUT"/*_4k.jpg "$OUT"/*_perf.json
