#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Terrain piece (E) capture driver: the REAL game (-game, offscreen), every launch through the GPU lock. Run the WHOLE script under ONE slot hold:
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label terrain -- docs/night1/terrain/capture_round.sh docs/night1/terrain/round-01 [stills|moves|warm ...]
# (the per-run gpu_slot calls inside pass through when nested). Outputs:
#   <round>/stills/<id>.jpg           3840x2160 output, internal 1920x1080 (r.ScreenPercentage auto = 50 % -> TSR 2x upscale), terrain build   (V_<id>)
#   <round>/stills/base_<id>.jpg      same camera, the city alone (VB_<id>): the "previous round" baseline
#   <round>/<name>.mp4                1920x1080 60 fps movie (-movie: fixed 1/60 s step, internal 1920x1080 = r.ScreenPercentage 100), <= 15 MB
#   <round>/<name>_telemetry.csv      per-frame traversal telemetry
# Heavy frames stay in /Users/midir/sm2-n1/_scratch/terrain/capture.
set -uo pipefail
ROUND="$(mkdir -p "$1" && cd "$1" && pwd)"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
UE_DIR="$(cd "$HERE/../../../unreal/WebHomage" && pwd)"
SCR="$HERE/scripts"
TMP=/Users/midir/sm2-n1/_scratch/terrain/capture
GPU="${GPU_CMD:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
HOLD_START="${HOLD_START:-$(date +%s)}"; HOLD_BUDGET="${HOLD_BUDGET:-2100}"   # the lock kills a hold after 40 min: stop launching new runs after 35 min
# r04: a run stopped by the health monitor (SIGTERM -> 143 / 137) or killed at the max hold (124) -- or a second failed run -- ends the hold: nothing is relaunched automatically
# (owner rules: one stop = resume the missing shots by hand, two = stop and report; never auto-relaunch after two crashes). The marker lives in $TMP/STOPPED (round4.sh clears it at the start of a hold).
time_ok() { [ ! -e "$TMP/STOPPED" ] && [ $(( $(date +%s) - HOLD_START )) -lt "$HOLD_BUDGET" ]; }
RUN() {
  "$GPU" capture --label terrain -- "$UE_DIR/Scripts/run_game.sh" "$@" -notraceserver; local rc=$?   # r05: every call passes "--" first, so -notraceserver is an engine arg (UE auto-starts UnrealTraceServer, a listener on 1981 / 1989, otherwise)
  if [ $rc -ne 0 ]; then
    echo "rc=$rc $(date +%H:%M:%S) $*" >> "$TMP/FAILS"
    if [ $rc -eq 143 ] || [ $rc -eq 137 ] || [ $rc -eq 124 ] || [ "$(wc -l < "$TMP/FAILS")" -ge 2 ]; then echo "STOP rc=$rc $(date +%H:%M:%S) $*" >> "$TMP/STOPPED"; echo "== STOPPED (rc=$rc): not launching anything else; see $TMP/STOPPED"; fi
  fi
  return $rc
}
# GPU etiquette (2026-10-01 20:43: the first terrain warm-up pinned the GPU and WindowServer starved): throttle every run so the GPU idles between frames
export WH_CAPTURE_MAXFPS="${WH_CAPTURE_MAXFPS:-12}"; STILL_FPS="$WH_CAPTURE_MAXFPS"   # r03: kept for the r2gpu stills after the movies
WANT=("$@"); [ ${#WANT[@]} -eq 0 ] && WANT=(warm stills moves)
want() { [[ " ${WANT[*]} " =~ " $1 " ]]; }
BASE_ROOT="${BASE_ROOT:-/Game/Terrain}"
TROOT="${TERRAIN_ROOT:-/Game/Terrain}"   # r04: the content root of this round's build (a side-by-side /Game/TerrainR4 keeps /Game/Terrain readable while a new build is made)
TDIR="$UE_DIR/Content/${TROOT#/Game/}"
[ -f "$TDIR/Maps/V_p1_south.umap" ] || { echo "terrain content missing ($TDIR/Maps/V_p1_south.umap): build_terrain.py has not produced the maps"; exit 3; }
mkdir -p "$TMP" "$ROUND/stills"
gpu() { ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1; }
IDS=$(python3 -c "import json;print(' '.join(s['id'] for s in json.load(open('$HERE/shots.json'))['shots']))")
[ -n "${ONLY_IDS:-}" ] && IDS="$ONLY_IDS"   # r02 pass 3b: re-capture only the stills a stopped hold did not finish
BASE_IDS="${BASE_IDS-p1_south p2_reservoir p10_lawn_eye p6_west_shore}"   # baseline (city alone) stills only for the pair views
if want warm; then
  echo "== warm-up (shader compile, not kept)  $(gpu)"
  rm -rf "$TMP/warm"
  # r04 capture safety (two health-monitor stops on 2026-10-02): 960x540, r.ScreenPercentage 50 (480x270 internal), a 4 fps fixed step AND a 4 fps frame cap; watch _scratch/gpu/health.log
  WH_CAPTURE_MAXFPS=4 RUN "$TMP/warm" -map $TROOT/Maps/V_p1_south -res 960x540 -quit "${WARM_QUIT:-12}" -name warm -timeout 2300 -exec "r.ScreenPercentage 50" -- -benchmark -fps=4 | tail -3
  # r02: a terrain material that did not compile (or lacks the Nanite usage flag) renders as the grey default material: stop now, fix, re-queue (the stills would be wasted slot time)
  grep -aE "(M_Terrain|MI_Pool_|MI_Grass|MI_Blanket|/Game/Terrain[A-Za-z0-9]*/).*(missing usage flag|[Ff]ailed to compile)|LogShaderCompilers: Error|Failed to compile Material" "$TMP/warm/warm.log" > "$ROUND/warm_shader_check.txt" 2>/dev/null
  # a compile failure draws the grey default material everywhere: stop (the stills would be wasted slot time). A missing-usage-flag warning is only recorded (the stills are still useful).
  if grep -aqE "[Ff]ailed to compile|LogShaderCompilers: Error" "$ROUND/warm_shader_check.txt" 2>/dev/null && [ -z "${KEEP_GOING:-}" ]; then echo "== WARM-UP SHADER CHECK FAILED (see $ROUND/warm_shader_check.txt); stopping the hold"; head -5 "$ROUND/warm_shader_check.txt"; exit 4; fi
  [ -s "$ROUND/warm_shader_check.txt" ] && echo "== warm-up log notes (kept going): $(wc -l < "$ROUND/warm_shader_check.txt") lines in warm_shader_check.txt"
fi
still() {  # <prefix> <id>
  local PRE="$1" ID="$2" NAME="$1$2"
  time_ok || { echo "== SKIP still $NAME (hold budget used up)"; return; }
  echo "== still $NAME  $(gpu)"
  rm -rf "$TMP/$NAME"
  local ROOTP="${STILL_ROOT:-$TROOT}"
  RUN "$TMP/$NAME" -map "$ROOTP/Maps/$NAME" -res 3840x2160 -shots "${STILL_AT:-2}" -quit "${STILL_QUIT:-3}" -perf "${STILL_PERF:-0.8:1.9}" -name "$NAME" -timeout 1500 -- -benchmark -fps=30 | tail -2
  # r03: the capture's own GPU frame time (RHIGetGPUFrameCycles over game 0.8-1.9 s, frame-capped run: GPU ms is per frame, not throughput)
  grep -ah "WH_PERF " "$TMP/$NAME/$NAME.log" | sed 's/^.*WH_PERF /'"${STILL_TAG:-r03}"' '"$NAME"' /' >> "$ROUND/gpu_ms.txt"
  [ -n "${STILL_NOKEEP:-}" ] && return
  for p in "$TMP/$NAME"/${NAME}_*.png; do
    [ -f "$p" ] || continue
    local OUT="$ROUND/stills/$ID.jpg"; [ "$PRE" = VB_ ] && OUT="$ROUND/stills/base_$ID.jpg"
    sips -s format jpeg -s formatOptions 90 "$p" --out "$OUT" >/dev/null && echo "  -> $OUT"
  done
}
if want stills; then
  PRIO="${PRIO_IDS-p1_south p2_reservoir p10_lawn_eye p6_west_shore}"      # the pair views first (terrain, then baseline), then the rest
  for ID in $PRIO; do still V_ "$ID"; done
  for ID in $BASE_IDS; do still VB_ "$ID"; done
  for ID in $IDS; do [[ " $PRIO " =~ " $ID " ]] || still V_ "$ID"; done
fi
movie() {  # <name> <script.json> <quit seconds>
  local NAME="$1" JSON="$2" Q="$3"
  time_ok && [ $(( $(date +%s) - HOLD_START )) -lt "${MOVIE_START_BUDGET:-1500}" ] || { echo "== SKIP movie $NAME (hold budget: a movie may only start in the first ${MOVIE_START_BUDGET:-1500} s: hold 2 lost the t4 movie to the 40 min max hold)"; return; }
  echo "== movie $NAME  $(gpu)"
  rm -rf "$TMP/$NAME"
  RUN "$TMP/$NAME" -map $TROOT/Maps/Manhattan_Terrain -res 1920x1080 -quit "$Q" -name "$NAME" -movie -timeout 2300 -exec "r.ScreenPercentage 100${HIDE_HERO:+,ShowFlag.SkeletalMeshes 0}" \
    -- -WHTravScript="$([[ "$JSON" == /* ]] && echo "$JSON" || echo "$SCR/$JSON")" -WHTravCsv="$TMP/$NAME/${NAME}_telemetry.csv" | tail -4
  cp "$TMP/$NAME/${NAME}_telemetry.csv" "$ROUND/" 2>/dev/null
  grep -h "WebTravWorld:\|WH_QUIT" "$TMP/$NAME/$NAME.log" | sed 's/^.*Display: //' | head -5 > "$ROUND/${NAME}_log_excerpt.txt"
  local CRF="${MOVIE_CRF:-28}"   # r04: 1080p movies of the lawn need crf 28-29 to fit 15 MB (crf 23 / 25 / 27 each cost a 4 min pass and were over)
  while :; do
    ffmpeg -loglevel error -y -framerate 60 -i "$TMP/$NAME/${NAME}_frames/MovieFrame%05d.png" -c:v libx264 -preset slow -pix_fmt yuv420p -crf $CRF -movflags +faststart "$ROUND/$NAME.mp4" || break
    [ "$(stat -f %z "$ROUND/$NAME.mp4")" -le 15000000 ] && break
    CRF=$((CRF + 2)); [ $CRF -gt 35 ] && break
  done
  echo "$NAME.mp4 crf $CRF $(stat -f %z "$ROUND/$NAME.mp4") bytes, $(ls "$TMP/$NAME/${NAME}_frames" | wc -l | tr -d ' ') frames"
  for s in 3 7 11; do ffmpeg -loglevel error -y -ss $s -i "$ROUND/$NAME.mp4" -frames:v 1 -q:v 3 "$ROUND/stills/${NAME}_t${s}s_1920x1080.jpg"; done   # contact frames from the encoded movie (r02: the frame-file names did not match)
  rm -rf "$TMP/$NAME/${NAME}_frames"
}
# (r02: the round-01 'turn 3' in-hold rebuild block was removed: the terrain content is rebuilt BEFORE taking the slot, never inside the hold)
if want moves; then
  export WH_CAPTURE_MAXFPS="${MOVIE_MAXFPS:-20}"
  MOVIES="${MOVIES:-t4_lawn_sprint t5_avenue_to_park}"   # r04: MOVIES="t4_lawn_sprint" = only that movie
  T5J=t5_avenue_to_park.json; [ -f "$ROUND/t5_probe/chosen.json" ] && T5J="$ROUND/t5_probe/chosen.json"   # r04: the probe's best candidate (absolute path) wins over the committed script
  for MV in $MOVIES; do   # in the order given (r04 movies hold: t5 first)
    case "$MV" in
      t4_lawn_sprint) movie t4_lawn_sprint t4_lawn_sprint.json "${MOVE_QUIT:-13.4}";;
      t5_avenue_to_park) movie t5_avenue_to_park "$T5J" "${MOVE_QUIT:-15.4}";;
    esac
  done
fi
# r03: round-02 content built side by side into /Game/TerrainR2 (scratch copy of the r02 scripts) -> the same stills' GPU ms under the same hold, for "capture GPU ms vs r2"
if want r2gpu && [ -f "$UE_DIR/Content/TerrainR2/Maps/V_p1_south.umap" ]; then
  export WH_CAPTURE_MAXFPS="$STILL_FPS"
  if time_ok; then echo "== r2 warm-up  $(gpu)"; rm -rf "$TMP/warm_r2"
    RUN "$TMP/warm_r2" -map /Game/TerrainR2/Maps/V_p1_south -res 960x540 -quit 20 -name warm_r2 -timeout 2300 -- -benchmark -fps=30 | tail -2; fi
  for ID in ${R2GPU_IDS:-p1_south p10_lawn_eye}; do STILL_ROOT=/Game/TerrainR2 STILL_TAG=r02 STILL_NOKEEP=1 still V_ "$ID"; done
  for ID in ${R2GPU_IDS:-p1_south p10_lawn_eye}; do STILL_TAG=r03-again STILL_NOKEEP=1 still V_ "$ID"; done   # r03 again right after (same GPU state)
fi

# r04: t5 route probes = headless telemetry-only runs (-nullrhi: no pixels, no GPU) of every candidate script in $PROBE_DIR (default <round>/t5_candidates), scored by tools/terrain/t5_score.py
if want t5probe; then
  PD="${PROBE_DIR:-$ROUND/t5_candidates}"; mkdir -p "$ROUND/t5_probe"
  for J in "$PD"/*.json; do
    [ -f "$J" ] || continue
    N=$(basename "$J" .json); time_ok || { echo "== SKIP probe $N (hold budget used up)"; continue; }
    echo "== t5 probe $N"
    rm -rf "$TMP/probe_$N"
    WH_CAPTURE_MAXFPS=60 RUN "$TMP/probe_$N" -map $TROOT/Maps/Manhattan_Terrain -res 960x540 -quit "${PROBE_QUIT:-15.6}" -name "probe_$N" -timeout 600 -- -nullrhi -benchmark -fps=60 -WHTravScript="$J" -WHTravCsv="$ROUND/t5_probe/$N.csv" | tail -2
  done
  python3 "$HERE/../../../tools/terrain/t5_score.py" "$ROUND/t5_probe" "$ROUND/t5_probe/scores.json" | tee "$ROUND/t5_probe/scores.txt"
  # the best candidate (highest share of the last 5 s over the park at 25-40 m, then 20-45 m; the control b0 is never chosen) becomes the t5 movie of this hold
  BEST=$(python3 -c "
import json
r=[x for x in json.load(open('$ROUND/t5_probe/scores.json')) if 'error' not in x and not x['name'].startswith('b0')]
print(r[0]['name'] if r and r[0]['in_park'] > 0.2 else '')")
  [ -n "$BEST" ] && cp "$PD/$BEST.json" "$ROUND/t5_probe/chosen.json" && echo "== t5 route chosen: $BEST" | tee "$ROUND/t5_probe/chosen.txt"
fi

# r04: GPU ms of the same two stills on the previous build (BASE_ROOT, default /Game/Terrain = the HEAD content without the r04 lawn) and on this build again, inside this hold (same GPU state)
if want basegpu && [ -f "$UE_DIR/Content/${BASE_ROOT#/Game/}/Maps/V_p1_south.umap" ]; then
  export WH_CAPTURE_MAXFPS="$STILL_FPS"
  for ID in ${BASEGPU_IDS:-p1_south p10_lawn_eye}; do STILL_ROOT=$BASE_ROOT STILL_TAG="${BASE_TAG:-r03p2-head}" STILL_NOKEEP=1 still V_ "$ID"; done
  for ID in ${BASEGPU_IDS:-p1_south p10_lawn_eye}; do STILL_TAG="${STILL_TAG:-r04}-again" STILL_NOKEEP=1 still V_ "$ID"; done
fi
echo "done: $ROUND"
