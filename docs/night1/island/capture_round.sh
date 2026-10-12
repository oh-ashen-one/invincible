#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island piece (A) capture driver: the REAL game (-game, offscreen) on /Game/Maps/Manhattan_WP, every run through the GPU lock.
#   <round>/<route>.mp4              1920x1080 60 fps (run_game.sh -movie: fixed 1/60 s step), H.264, <= 15 MB
#   <round>/<route>_telemetry.csv    per-frame traversal telemetry (WebTravScript)
#   <round>/stills/<name>_*.jpg      3840x2160 stills (JPEG q90 from the PNG)
# usage: docs/night1/island/capture_round.sh <round dir> [run ...]      runs: warmup r1 r2 r3 r4 r5 ab a1 (default: all but ab; r5 = the M2 avenue route from y 1010)
# Heavy frames go to the island scratch (/Users/midir/sm2-n1/_scratch/island/capture); nothing heavy stays in the repo.
set -uo pipefail
ROUND="$(mkdir -p "$1" && cd "$1" && pwd)"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
UE_DIR="$(cd "$HERE/../../../unreal/WebHomage" && pwd)"
SCR="$HERE/scripts"
TMP=/Users/midir/sm2-n1/_scratch/island/capture
MAP="${ISLAND_MAP:-/Game/Maps/Manhattan_WP}"
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
# ISLAND_IN_LOCK=1: the caller already holds the GPU slot for the whole batch (gpu_slot.sh capture --label island -- capture_round.sh ...):
# several runs in one hold instead of one queue cycle each (max hold 2400 s: ~2 movie routes).
RUN() { if [ -n "${ISLAND_IN_LOCK:-}" ]; then "$UE_DIR/Scripts/run_game.sh" "$@"; else "$GPU" capture --label island -- "$UE_DIR/Scripts/run_game.sh" "$@"; fi; }
WANT=("$@"); [ ${#WANT[@]} -eq 0 ] && WANT=(warmup r1 r2 r3 r4 r5 a1)
want() { [[ " ${WANT[*]} " =~ " $1 " ]]; }
mkdir -p "$TMP" "$ROUND/stills"
# (island r02) never capture while this worktree's content is being rebuilt (rebuild_r02b.sh holds this flag; it removes it on exit)
while [ -e /Users/midir/sm2-n1/_scratch/island/BUILDING ]; do echo "$(date +%T) waiting for the island rebuild"; sleep 20; done
gpu() { ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1; }
if want warmup; then
  echo "== warm-up (shader / DDC compile, not kept)  $(gpu)"
  rm -rf "$TMP/warmup"
  # (island r02) the warm-up also writes the traversal's primitive dump (-WHTravDumpPrims, WebTravWorld.cpp round 20): checked by
  # tools/export/island_dump_check.py (every visible facade / roofs / detail / fire-escape tile a QueryOnly complex solid)
  RUN "$TMP/warmup" -map "$MAP" -res 960x540 -quit ${WARM_QUIT:-25} -name warmup -timeout $(run_timeout 2300) -- -benchmark -fps=60 -WHTravScript="$SCR/r1_north_avenue.json" \
    -WHTravDumpPrims="$TMP/warmup/prims.csv" | tail -3
  grep -h "WebTravWorld:" "$TMP/warmup/warmup.log" | sed 's/^.*Display: //' > "$ROUND/warmup_webtravworld_log.txt"
  [ -f "$TMP/warmup/prims.csv" ] && gzip -9 -c "$TMP/warmup/prims.csv" > "$ROUND/prims_dump.csv.gz"
fi
# (island r03) never let gpu_slot's max hold (2,400 s: SIGTERM, then SIGKILL after 10 s) hit a rendering engine: a route starts only if
# ISLAND_ROUTE_BUDGET_S (default 1,500 s: a 30 s 1080p60 movie took 13-25 min under a shared GPU) is left before the hold ends.
T_HOLD0=$(date +%s); HOLD_MAX=${GPU_SLOT_CAPTURE_MAX_HOLD:-2400}
budget_ok() { local left=$(( HOLD_MAX - ($(date +%s) - T_HOLD0) )); if [ "$left" -lt "${1:-${ISLAND_ROUTE_BUDGET_S:-1500}}" ]; then echo "== SKIP $2: only ${left} s left in the hold"; return 1; fi; }
# run_game.sh's own -timeout (SIGTERM, 60 s wait) ends a slow run 450 s before the hold does (r03 r1: 3 engines on the GPU, 45 frames / min;
# r03 r3: moving 1,824 1080p PNGs to the exFAT scratch took > 5 min after the engine quit)
run_timeout() { local left=$(( HOLD_MAX - ($(date +%s) - T_HOLD0) - 450 )); [ "$left" -gt "$1" ] && left=$1; echo "$left"; }
route() {  # name script
  local NAME="$1" JSON="$2" MAPURL="$MAP"
  budget_ok "" "$NAME" || return 0
  echo "== $NAME  $(gpu)"
  rm -rf "$TMP/$NAME"
  RUN "$TMP/$NAME" -map "$MAPURL" -res 1920x1080 -quit ${QUIT:-30.4} -name "$NAME" -movie -timeout $(run_timeout 2300) \
    -- -WHTravScript="$SCR/$JSON" -WHTravCsv="$TMP/$NAME/${NAME}_telemetry.csv" | tail -4
  cp "$TMP/$NAME/${NAME}_telemetry.csv" "$ROUND/" 2>/dev/null
  grep -h "WebTravWorld:\|LogWorldPartition.*[Ss]treaming\|WH_QUIT" "$TMP/$NAME/$NAME.log" | sed 's/^.*Display: //' | head -5 > "$ROUND/${NAME}_log_excerpt.txt"
  # <= 15 MB: H.264 2-pass at the bitrate that fills ~14.6 MB, from run_game.sh's own ~29 Mbps master (<name>.mp4 in the scratch run dir;
  # the frames as fallback). (r01) the old crf 23 -> 35 loop still gave 15.9 MB on a 30 s golden-hour swing.
  local SRC="$TMP/$NAME/$NAME.mp4" IN=()
  if [ -f "$SRC" ]; then IN=(-i "$SRC"); else IN=(-framerate 60 -i "$TMP/$NAME/${NAME}_frames/MovieFrame%05d.png"); fi
  local DUR; DUR=$(ls "$TMP/$NAME/${NAME}_frames" 2>/dev/null | wc -l | tr -d ' '); DUR=$(python3 -c "print(max(int('${DUR:-0}' or 0), 60) / 60)")
  local KB; KB=$(python3 -c "print(int(14.6e6 * 8 / $DUR / 1000) - 60)")
  local PL; PL=$(mktemp -d "$TMP/pass.XXXX")
  ( cd "$PL" && ffmpeg -loglevel error -y "${IN[@]}" -c:v libx264 -preset slow -b:v ${KB}k -pass 1 -an -f mp4 /dev/null && \
    ffmpeg -loglevel error -y "${IN[@]}" -c:v libx264 -preset slow -b:v ${KB}k -pass 2 -pix_fmt yuv420p -movflags +faststart -an "$ROUND/$NAME.mp4" )
  rm -rf "$PL"
  echo "$NAME.mp4 2-pass ${KB}k $(stat -f %z "$ROUND/$NAME.mp4") bytes, $(ls "$TMP/$NAME/${NAME}_frames" | wc -l | tr -d ' ') frames"
  # contact frames for the critic pack (1080p jpg at 5 / 12 / 20 / 26 / 28 s; r03: 26 + 28 s are the r2 road-band test frames)
  # (island r03) movie frame k shows game time (k - 1) / 60 s (probe stills at -shots 12 / 20 / 26 match frames 721 / 1201 / 1561 to 0.2-0.4 grey levels): t = s -> frame 60 s + 1
  for s in 5 12 20 26 28; do f=$(printf "%05d" $((s * 60 + 1))); [ -f "$TMP/$NAME/${NAME}_frames/MovieFrame$f.png" ] && \
    ffmpeg -loglevel error -y -i "$TMP/$NAME/${NAME}_frames/MovieFrame$f.png" -q:v 3 "$ROUND/stills/${NAME}_t${s}s_1920x1080.jpg"; done
  rm -rf "$TMP/$NAME/${NAME}_frames"
}
want r1 && route r1_north_avenue r1_north_avenue.json
want r2 && route r2_south_avenue r2_south_avenue.json
want r3 && route r3_crosstown_east r3_crosstown_east.json
want r4 && route r4_wallrun_roofs r4_wallrun_roofs.json
# (island r03) r5: swing-held avenue route over the M2 tiles, starting at y ~1010 (stills 12 / 20 / 26 / 28 s are the road-band test frames)
want r5 && route r5_m2_avenue r5_m2_avenue.json
# (island r04) r5b: the same route with the traversal tune AltChain=0 (the r23 swing chain without the r24 altitude releases), for the swing / re-web pass lines
want r5b && route r5_m2_avenue_alt0 r5_m2_avenue_alt0.json
# (island r02) A/B for traversal's default: r1 with the instanced props / trees solid (-WHTravIsmSolid=1), telemetry only (fixed 1/60 s step,
# so the sim is the movie run's; 960x540, no frames kept)
if want ab; then
  echo "== r1_ism_solid (A/B, telemetry)  $(gpu)"
  rm -rf "$TMP/r1_ism_solid"
  RUN "$TMP/r1_ism_solid" -map "$MAP" -res 960x540 -quit ${QUIT:-30.4} -name r1_ism_solid -timeout $(run_timeout 2300) -- -benchmark -fps=60 -WHTravIsmSolid=1 \
    -WHTravScript="$SCR/r1_north_avenue.json" -WHTravCsv="$TMP/r1_ism_solid/r1_ism_solid_telemetry.csv" -WHTravDumpPrims="$TMP/r1_ism_solid/prims.csv" | tail -3
  [ -f "$TMP/r1_ism_solid/prims.csv" ] && gzip -9 -c "$TMP/r1_ism_solid/prims.csv" > "$ROUND/prims_dump_ism_solid.csv.gz"
  cp "$TMP/r1_ism_solid/r1_ism_solid_telemetry.csv" "$ROUND/" 2>/dev/null
  grep -h "WebTravWorld:" "$TMP/r1_ism_solid/r1_ism_solid.log" | sed 's/^.*Display: //' > "$ROUND/r1_ism_solid_log_excerpt.txt"
fi
if want a1; then
  for A in a1_high_north a1_high_south; do
    budget_ok 600 "$A" || continue
    echo "== $A (3840x2160 still)  $(gpu)"
    rm -rf "$TMP/$A"
    RUN "$TMP/$A" -map "$MAP" -res 3840x2160 -shots 0.6 -quit 2.0 -name "$A" -timeout $(run_timeout 1200) -- -benchmark -fps=60 -WHTravScript="$SCR/$A.json" | tail -2
    for p in "$TMP/$A"/${A}_*.png; do [ -f "$p" ] && sips -s format jpeg -s formatOptions 90 "$p" --out "$ROUND/stills/$(basename "${p%.png}")_3840x2160.jpg" >/dev/null; done
  done
fi
echo "done: $ROUND"
