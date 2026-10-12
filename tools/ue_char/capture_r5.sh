#!/bin/bash
# (movies: motion blur OFF by default, MOVIE_EXEC=... overrides; round 04 clips were smeared)
# Round-05 captures of the RUNNING game (offscreen, inside the shared GPU lock, every launch waits for the loop's Unreal cap).
# Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
#
#   tools/ue_char/capture_r5.sh <out_dir> [MOVIES] [STILLS] [JUMP]      (default: everything; e.g.  ... out "" "gF" "")
#     MOVIES  space list of  H (hero) G (hero chase / toward cameras) F (fight) C (crowd) A (avoidance demo: round-06 layout, avoidance on)   -> 1080p60 -movie runs (fixed 1/60 s step) cut into clips
#     STILLS  space list of  gH gF gC gE gK gI (gK = chroma-key crowd, gI = per-walker id masks; both need the 'mapkey' build step)                    -> native 3840x2160 real-time stills (r.ScreenPercentage 100, motion blur off)
#     JUMP    "1"                                            -> 4K -movie run of the leap, frames around the apex kept as hero_jump_4k
#
# Maps: /Game/Tests/Characters/Char_Hero (hero only), Char_Fight (staged street fight, 6 enemies around the hero), Char_Crowd (two-way
# flow with a near lane), Char_Lineup (standing enemies; face close-ups only).  Director shots (build_characters.py, 'maps5'):
#   Char_Hero  0 turntable 6 s | 1 run side 6 | 2 run 3/4 5 | 3 run -> leap side 6.5 | 4 suit close-up 6 | 5 face + lens close-up 6
#   Char_Fight 0 wide 8 s | 1 3/4 8 | 2 orbit 8
#   Char_Crowd 0 tracking 8 | 1 wide 6
#   Char_Lineup 10 thug face | 11 brute face | 12 hood face | 13 tee face | 14 beard face
set -e
WT="$(cd "$(dirname "$0")/../.." && pwd)"
P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"
GPU="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
OUT=${1:?out dir}; MOVIES="${2-H F C}"; STILLS="${3-gH gF gC gE}"; JUMP="${4-1}"
mkdir -p "$OUT"
D=${SEG_OFFSET:-0.05}      # frames before the director's first cut are the default camera (measured by frame differencing in round 04)
cd "$WT/unreal/WebHomage"

seg_run() {   # name map start_shot quit_s [res]
  local FR="$OUT/seg$1_frames"
  if [ -d "$FR" ] && [ -n "$(ls "$FR" 2>/dev/null)" ]; then return; fi
  "$WT/tools/ue_char/ue_wait.sh"
  ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' > "$OUT/seg$1_gpu_util_before.txt" || true
  "$GPU" capture --label characters -- Scripts/run_game.sh "$OUT" -map "$2" -res "${5:-1920x1080}" -quit "$4" -name "seg$1" -movie -exec "${MOVIE_EXEC-r.MotionBlurQuality 0}" -timeout 3000 \
      -- -WHCharShot="$3" ${WLOG:+-WHWalkerLog="$WLOG"} ${BONELOG:+-WHBoneLog="$BONELOG"} < /dev/null | tail -4
}
cut_clip() {  # seg name start_s dur_s
  ffmpeg -loglevel error -y -framerate 60 -start_number $(python3 -c "print(int(round($3 * 60)))") -i "$OUT/seg$1_frames/MovieFrame%05d.png" \
    -frames:v $(python3 -c "print(int(round($4 * 60)))") -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "$OUT/$2.mp4"
}
cut_still() { # seg name time_s
  ffmpeg -loglevel error -y -framerate 60 -start_number $(python3 -c "print(int(round($3 * 60)))") -i "$OUT/seg$1_frames/MovieFrame%05d.png" -frames:v 1 -q:v 2 "$OUT/$2.jpg"
}
for m in $MOVIES; do
  case $m in
    H) seg_run H /Game/Tests/Characters/Char_Hero 1 18.5
       cut_clip H hero_run_side $D 6; cut_clip H hero_run_34 $(python3 -c "print($D+6)") 5; cut_clip H hero_run_leap_side $(python3 -c "print($D+11)") 6.5 ;;
    G) seg_run G /Game/Tests/Characters/Char_Hero 6 12.5     # round 05 gameplay cameras: chase (behind) 6 s, then toward the camera 6 s
       cut_clip G hero_run_chase $D 6; cut_clip G hero_run_toward $(python3 -c "print($D+6)") 6 ;;
    F) BONELOG=${BONELOG:-$OUT/fight_bones.csv} seg_run F /Game/Tests/Characters/Char_Fight 0 25.4     # round 09: bone log of the scripted fight (-WHBoneLog)
       # round 10: shot 0 lasts 8.6 s (0.6 s of texture-streaming warm-up + a full 8 s clip), the three clips are 8.0 s each: stage 0.65 - 8.65 | 8.65 - 16.65 | 16.65 - 24.65
       cut_clip F street_fight_wide $(python3 -c "print($D+0.6)") 8; cut_clip F street_fight_34 $(python3 -c "print($D+8.6)") 8; cut_clip F street_fight_orbit $(python3 -c "print($D+16.6)") 8
       cut_still F street_fight_1080 $(python3 -c "print($D+3)") ;;
    A) WLOG="$OUT/avoid_demo_walkers.csv" seg_run A /Game/Tests/Characters/Char_CrowdAvoid 0 9.5     # round 07: the OLD (colliding) layout with avoidance on: the A/B of the avoidance alone
       cut_clip A crowd_avoidance_demo $D 8 ;;
    C) WLOG="$OUT/crowd_walkers.csv" seg_run C /Game/Tests/Characters/Char_Crowd 0 15     # round 07: walker telemetry of the very run the clips are cut from
       cut_clip C crowd_tracking $D 8; cut_clip C crowd_wide $(python3 -c "print($D+8)") 6
       cut_still C crowd_tracking_1080 $(python3 -c "print($D+4)"); cut_still C crowd_wide_1080 $(python3 -c "print($D+11)") ;;
  esac
done

ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | tee "$OUT/gpu_util_before_4k.txt"
run_group() { # map start_shot "still times" quit tag names...
  local map="$1" start="$2" shots="$3" quit="$4" tag="$5"; shift 5
  if [ -n "$ONLY" ]; then case " $ONLY " in *" $tag "*) ;; *) return 0;; esac; fi
  "$WT/tools/ue_char/ue_wait.sh"
  # round 09: STAGE_SHOTS=1 takes the stills at STAGE times of the scripted fight (director clock, -WHStageShot): the automation clock of a real-time run leads the stage clock by a
  # varying 0.4 - 2.4 s (measured), so -shots would show another moment of a choreography than the one named; the run then needs a later quit (stage + 8 s)
  local SHOTARG=(-shots "$shots") XS=()
  if [ "${STAGE_SHOTS:-0}" = 1 ]; then SHOTARG=(); XS=("-WHStageShot=$shots"); quit=$(( quit + 6 )); fi
  "$GPU" capture --label characters -- Scripts/run_game.sh "$OUT" -map "$map" -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0${XEXEC:-}" \
    "${SHOTARG[@]}" -perf 3:$(( quit - 1 )) -quit "$quit" -name "$tag" -timeout 3600 -- -WHCharShot="$start" ${XARGS:-} "${XS[@]}" < /dev/null | tail -12
  for f in "$OUT"/${tag}_[0-9][0-9]_t*.png; do
    if [ "${STILL_PNG:-0}" = 1 ]; then mv "$f" "$OUT/${1}_4k.png"   # keyed / id stills stay lossless (4:2:0 JPEG bleeds the key colour into edge pixels)
    else ffmpeg -loglevel error -y -i "$f" -q:v 2 "$OUT/${1}_4k.jpg"; rm -f "$f"; fi
    shift
  done
}
HERO=/Game/Tests/Characters/Char_Hero; FIGHT=/Game/Tests/Characters/Char_Fight; CROWD=/Game/Tests/Characters/Char_Crowd; LINE=/Game/Tests/Characters/Char_Lineup
HEROKEY=/Game/Tests/Characters/Char_HeroKey   # round 08: hero on the key (flat class colours: lens / bezel / suit), build step mapkey
CROWDID=/Game/Tests/Characters/Char_CrowdID   # per-walker stencil id map (build step mapkey)
KEY=/Game/Tests/Characters/Char_CrowdKey   # chroma-key twin of Char_Crowd (unlit green street, no fog / sky): green inside a person = a crack (eval/key_holes.py)
for g in $STILLS; do
  case $g in
    gH) run_group $HERO 0 "4.5"  8 gH1 hero_turntable
        run_group $HERO 1 "3.5"  7 gH2 hero_run_side
        run_group $HERO 4 "3.0,8.0,10.0,11.5" 13 gH3 suit_closeup hero_face_lens_a hero_face_lens hero_face_lens_b ;;   # round 08: two more face angles of the turntable (8.0 / 11.5 s)
    gF) run_group $FIGHT 0 "${GF_TIMES:-3.5,13.0,22.0}" $(python3 -c "print(int(max(map(float,'${GF_TIMES:-3.5,13.0,22.0}'.split(',')))+2))") gF1 street_fight_wide street_fight_34 street_fight_orbit ;;   # round 09: GF_TIMES picks the instants of the scripted fight
    gC) run_group $CROWD 0 "5.5,11.5" 13 gC1 crowd_tracking crowd_wide ;;
    gK) XEXEC=",r.CustomDepth 3" STILL_PNG=1 run_group $KEY 0 "3.5,5.5,7.5,11.5" 13 gK1 crowd_key_a crowd_key_tracking crowd_key_c crowd_key_wide ;;
    gI) XEXEC=",r.CustomDepth 3" STILL_PNG=1 run_group $CROWDID 0 "3.5,5.5,7.5,11.5" 13 gI1 crowd_id_a crowd_id_tracking crowd_id_c crowd_id_wide ;;
    gHK) XARGS="-WHFlatClasses" XEXEC=",r.CustomDepth 3" STILL_PNG=1 run_group $HEROKEY 4 "3.0,8.0,10.0,11.5" 13 gHK1 hero_key_suit hero_key_face_a hero_key_face hero_key_face_b ;;
    gE) run_group $LINE 10 "3.5,7.5" 10 gE1 thug_face brute_face
        run_group $LINE 12 "3.0,9.0,15.0" 17 gE2 hood_face tee_face beard_face ;;
  esac
done

# 4K movie of the leap only (deterministic timing): the frames around the apex become hero_jump_4k.jpg (director shot 3 restarts the jump lane at t = 0:
# takeoff crouch from 1.3 s, lift-off 1.55 s, apex ~1.9 s)
if [ "$JUMP" = "1" ]; then
  seg_run J4 $HERO 3 3.4 3840x2160
  n=$(ls "$OUT/segJ4_frames" 2>/dev/null | wc -l | tr -d ' ')
  echo "leap 4K frames: $n"
  for t in 1.85 1.95; do cut_still J4 hero_jump_4k_t$t $(python3 -c "print($t)"); done
fi
ls -la "$OUT"/*.mp4 "$OUT"/*.jpg 2>/dev/null | head -60
