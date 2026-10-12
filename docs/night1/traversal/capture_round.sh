#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Piece P3 capture driver: replays the traversal scripts in the real game (-game, offscreen) and writes, per sequence,
#   <round>/<seq>.mp4            1920x1080 60 fps (run_game.sh -movie: fixed 1/60 s step, every frame dumped), <= 15 MB
#   <round>/<seq>_telemetry.csv  per-frame traversal / camera / input telemetry of that movie run
#   <round>/stills/<seq>_NN_tSSS.jpg  3840x2160 stills (separate deterministic run, JPEG q92 from the PNG)
# usage: docs/night1/traversal/capture_round.sh <round dir> [seq ...]     (heavy frames go to /Users/midir/sm2-n1/_scratch/traversal)
set -uo pipefail
ROUND="$(mkdir -p "$1" && cd "$1" && pwd)"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
UE_DIR="$(cd "$HERE/../../../unreal/WebHomage" && pwd)"
# round 10: captures run in the integrated lit city /Game/Maps/Manhattan (golden; built in this worktree by Scripts/build_manhattan.py) with the
# city scripts; TRAV_MAP=/Game/Tests/Traversal/Trav_Canyon TRAV_SCRIPTS=$HERE/scripts for the gray-box canyon
SCR="${TRAV_SCRIPTS:-$HERE/scripts/city}"
TMP=/Users/midir/sm2-n1/_scratch/traversal/capture
MAP="${TRAV_MAP:-/Game/Maps/Manhattan}"
# GPU lock (RULES / docs/night1/gpu/PROTOCOL.md): every game run takes a shared capture slot
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
# round 12: GPU_OUTER=1 = the caller already holds one capture slot for the whole batch (gpu_slot.sh capture -- capture_round.sh ...;
# max hold 40 min): the runs then go straight to run_game.sh instead of queueing once per run
if [ -n "${GPU_OUTER:-}" ]; then RUN() { "$UE_DIR/Scripts/run_game.sh" "$@"; }
else RUN() { "$GPU" capture --label traversal -- "$UE_DIR/Scripts/run_game.sh" "$@"; }; fi
# round 06: pre-roll (s) rendered from the start pose before the sequence starts (exposure / Lumen settle), trimmed from the movie
PRE=0.8
mkdir -p "$TMP" "$ROUND/stills"
# name  script                          quit(s)  still times (game s)
SEQS=(
  "a_swing_chain a_swing_chain.json 15.6 1.0,2.6,3.4,5.9,9.5"
  "b_release_trick_dive_zip b_release_trick_dive_zip.json 7.0 0.8,1.9,2.5,4.4,5.8"
  "c_wallrun_perch c_wallrun_perch.json 10.5 1.0,2.6,3.6,4.9,9.8"
  "d_sprint_jump_first_swing d_sprint_jump_first_swing.json 12.0 2.3,5.6,7.6,11.8"
  # round 17: f1-f5 = the y -560 cross street heading east, a flip on every release, each solved for an apex >= 3 m over the lower roofline
  # round 13 (flow flips: the program starts at the web release, the next web attaches in its final reach): f1-f3 the west avenue
  # (x -250 south, lower blocks), a flip on every 2nd release; f4 a flip on every release; f5 the Midtown canyon (x 250 north)
  "f1_flow_backDouble f1_flow_backDouble.json ${F1Q:-9.0} ${F1T:-2.4,3.0}"
  "f2_flow_pikeSwan f2_flow_pikeSwan.json ${F2Q:-9.0} ${F2T:-2.4,3.0}"
  "f3_flow_corkscrew f3_flow_corkscrew.json ${F3Q:-9.0} ${F3T:-2.4,3.0}"
  "f4_chain_flips f4_chain_flips.json ${F4Q:-13.3} ${F4T:-3.0,6.0}"   # round 18: 3 flips, a plain release where the catch guard finds no web (9.12 s), the 4th flip 10.88 s, its catch ~12.5 s + 0.8 s (r17: 12.2 s, the 4th flip missed its catch)
  "f5_canyon_backDouble f5_canyon_backDouble.json ${F5Q:-9.0} ${F5T:-2.4,3.0}"
  # round 19 (owner playtest 2026-10-01): wall-run IK stride + E from a wall run / side run / roof run / perch
  "w1_wallrun_tall_zip w1_wallrun_tall_zip.json ${W1Q:-7.5} 1.8,2.6"
  "w2_wallrun_side_zip w2_wallrun_side_zip.json ${W2Q:-7} 2.4,3.0"
  "r1_roofrun_zip r1_roofrun_zip.json ${R1Q:-9.5} 6.0,7.0"
  "s1_high_swing s1_high_swing.json ${S1Q:-6.0} 0.6,1.2"
  # round 20 (critic r19 owner bugs): RMB cancels a flip / a wall run into a swing (<= 0.1 s); mouse look injected into a scripted chain
  "x1_rmb_cancel_flip x1_rmb_cancel_flip.json ${X1Q:-4.0} 1.8,2.2"
  "x2_rmb_cancel_wall x2_rmb_cancel_wall.json ${X2Q:-5.0} 3.25,3.6"
  "m1_mouse_swing m1_mouse_swing.json ${M1Q:-6.0} 1.5,3.5"
  # round 25 (director hard line: pawn run cadence 3.2-3.8 Hz head-top FFT over 1.5-11 s): a 12 s full-stick run up the avenue
  "p1_pawn_run ${P1JSON:-p1_pawn_run.json} ${P1Q:-12.0} 2.0,6.0"
)
WANT=("$@")
# RULES (owner 2026-09-29): never add a 4th Unreal instance — wait while 3 or more are running
wait_slot() { while [ "$(pgrep -x UnrealEditor | wc -l)" -ge 3 ]; do sleep 5; done; }  # pgrep -x: the -f pattern also counted python wrappers
# round 06: shader / texture warm-up render first (a fresh DDC compiles the hero and city materials on first use, which
# rendered the suit white / unshaded in the first frames of a capture); low-res, not kept
if [ -z "${SKIP_WARM:-}" ]; then
echo "== warm-up render (not kept)"
rm -rf "$TMP/warmup"
wait_slot
RUN "$TMP/warmup" -map "$MAP" -res 960x540 -quit ${WARM_QUIT:-16} -name warmup -timeout 2400 \
  -- -benchmark -fps=60 -WHTravScript="$SCR/a_swing_chain.json" | tail -1
fi
for entry in "${SEQS[@]}"; do
  read -r NAME JSON QUIT SHOTS <<< "$entry"
  if [ ${#WANT[@]} -gt 0 ] && [[ ! " ${WANT[*]} " =~ " $NAME " ]]; then continue; fi
  echo "== $NAME  (GPU $(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1))"
  # --- 1080p60 movie + telemetry
  rm -rf "$TMP/$NAME"
  QUITP=$(python3 -c "print(round($QUIT + $PRE, 3))")
  wait_slot
  RUN "$TMP/$NAME" -map "$MAP" -res 1920x1080 -quit "$QUITP" -name "$NAME" -movie -timeout 3000 \
    -exec "r.ScreenPercentage 100" -- -WHTravScript="$SCR/$JSON" -WHTravPreroll=$PRE -WHTravMask ${EXTRA_ARGS:-} $( [ "$NAME" = m1_mouse_swing ] && echo -WHTravInputTest=mouseLook -WHMouseTestPx=${M1PX:-40} ) | tail -3
  FR="$TMP/$NAME/${NAME}_frames"
  if [ -d "$FR" ] && [ -f "$TMP/$NAME/${NAME}_telemetry.csv" ]; then
    NF=$(ls "$FR" | wc -l | tr -d ' '); NT=$(( $(wc -l < "$TMP/$NAME/${NAME}_telemetry.csv") - 1 ))
    SKIP=$(( NF - NT ))   # rendered frames before the sequence's first telemetry row (engine start + pre-roll)
    echo "frames $NF, telemetry rows $NT -> trimming the first $SKIP frames"
    ffmpeg -loglevel error -y -framerate 60 -start_number $SKIP -i "$FR/MovieFrame%05d.png" -c:v libx264 -pix_fmt yuv420p -crf 18 \
      -movflags +faststart "$ROUND/$NAME.mp4"
    DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$ROUND/$NAME.mp4")
    if [ "$(stat -f %z "$ROUND/$NAME.mp4")" -gt 15000000 ]; then # re-encode at a bitrate that fits 14.5 MB
      KBPS=$(python3 -c "print(int(13.5e6*8/1000/float('$DUR')))")
      ffmpeg -loglevel error -y -framerate 60 -start_number $SKIP -i "$FR/MovieFrame%05d.png" -c:v libx264 -preset slow \
        -b:v ${KBPS}k -maxrate ${KBPS}k -bufsize $((KBPS*2))k -pix_fmt yuv420p -movflags +faststart "$ROUND/$NAME.mp4"
    fi
    cp "$TMP/$NAME/${NAME}_telemetry.csv" "$ROUND/"
    echo "movie: $ROUND/$NAME.mp4 $(stat -f %z "$ROUND/$NAME.mp4") bytes, ${DUR}s"
  fi
  # --- 3840x2160 stills (same deterministic replay); NO_STILLS=1 skips them (round 11: long shared GPU queue)
  if [ -n "${NO_STILLS:-}" ]; then continue; fi
  rm -rf "$TMP/${NAME}_4k"
  # shot times are world seconds: shift by the pre-roll; files are named by sequence time
  SHOTSP=$(python3 -c "print(','.join(str(round(float(t) + $PRE, 3)) for t in '$SHOTS'.split(',')))")
  wait_slot
  RUN "$TMP/${NAME}_4k" -map "$MAP" -res 3840x2160 -shots "$SHOTSP" -name "$NAME" -timeout 1500 \
    -exec "r.ScreenPercentage 100" -- -benchmark -fps=60 -WHTravScript="$SCR/$JSON" -WHTravPreroll=$PRE \
    -WHTravCsv="$TMP/${NAME}_4k/stills_telemetry.csv" | tail -2
  I=0
  for T in ${SHOTS//,/ }; do
    p=$(ls "$TMP/${NAME}_4k/${NAME}_$(printf %02d $I)_"*.png 2>/dev/null | head -1)
    [ -n "$p" ] && sips -s format jpeg -s formatOptions 92 "$p" --out "$ROUND/stills/${NAME}_$(printf %02d $I)_t$(printf %05.1f $T).jpg" > /dev/null
    I=$((I + 1))
  done
done
