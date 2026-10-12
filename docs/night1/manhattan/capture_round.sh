#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Piece C capture driver (the running game, offscreen -game via Scripts/run_game.sh, every run wrapped in the GPU lock):
#   <round>/route_30s.mp4                1920x1080 60 fps movie of the 30 s scripted swing route in /Game/Maps/Manhattan (golden)
#   <round>/route_30s_telemetry.csv      per-frame P3 traversal telemetry of that movie run; route_check.json (fall-through / stuck / T-pose)
#   <round>/stills/route_NN_tSSS.jpg     3840x2160 stills of the same route (same deterministic replay)
#   <round>/stills/view_<S#>.jpg         3840x2160 stills from the P1 city shot cameras S1 / S2 / S4 (Manhattan_View_<S#>, golden)
# usage: docs/night1/manhattan/capture_round.sh <round dir> [movie|stills|views ...]      (heavy frames: _scratch/manhattan/capture)
set -uo pipefail
ROUND="$(mkdir -p "$1" && cd "$1" && pwd)"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
UE_DIR="$(cd "$HERE/../../../unreal/WebHomage" && pwd)"
G=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
TMP=/Users/midir/sm2-n1/_scratch/manhattan/capture
MAP=/Game/Maps/Manhattan
SCRIPT="$HERE/scripts/route_30s.json"
PRE=0.8          # P3 capture pre-roll (exposure / Lumen settle from the start pose), trimmed from the movie
DUR=30.0         # route length (game s)
ROUTE_SHOTS="4.0,10.0,16.0,24.0"
SP="${SP:-100}"  # stills / movie screen percentage (100 = native internal resolution)
WANT=("$@"); [ ${#WANT[@]} -eq 0 ] && WANT=(movie stills views)
has() { [[ " ${WANT[*]} " =~ " $1 " ]]; }
wait_slot() { while [ "$(pgrep -f 'MacOS/UnrealEditor( |$)' | wc -l)" -ge 3 ]; do echo "waiting: 3+ Unreal instances running"; sleep 60; done; }
util() { ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1 | grep -o '[0-9]*$'; }
mkdir -p "$TMP" "$ROUND/stills"
echo "{\"sp\": $SP, \"pre\": $PRE, \"map\": \"$MAP\", \"script\": \"docs/night1/manhattan/scripts/route_30s.json\"}" > "$ROUND/capture_settings.json"

if has movie; then
  echo "== warm-up render (shader compile, not kept)  GPU $(util) %"
  rm -rf "$TMP/warmup"; wait_slot
  $G capture --label manhattan -- "$UE_DIR/Scripts/run_game.sh" "$TMP/warmup" -map "$MAP" -res 960x540 -quit 12 -name warmup -timeout 2400 \
    -- -benchmark -fps=60 -WHTravScript="$SCRIPT" | tail -1
  echo "== movie 1080p60  GPU $(util) %"
  rm -rf "$TMP/route"; wait_slot
  QUITP=$(python3 -c "print(round($DUR + $PRE, 3))")
  $G capture --label manhattan -- "$UE_DIR/Scripts/run_game.sh" "$TMP/route" -map "$MAP" -res 1920x1080 -quit "$QUITP" -name route_30s -movie -timeout 3600 \
    -exec "r.ScreenPercentage $SP" -- -WHTravScript="$SCRIPT" -WHTravPreroll=$PRE | tail -3
  FR="$TMP/route/route_30s_frames"
  if [ -d "$FR" ] && [ -f "$TMP/route/route_30s_telemetry.csv" ]; then
    NF=$(ls "$FR" | wc -l | tr -d ' '); NT=$(( $(wc -l < "$TMP/route/route_30s_telemetry.csv") - 1 ))
    SKIP=$(( NF - NT )); echo "frames $NF, telemetry rows $NT -> trimming the first $SKIP frames"
    ffmpeg -loglevel error -y -framerate 60 -start_number $SKIP -i "$FR/MovieFrame%05d.png" -c:v libx264 -pix_fmt yuv420p -crf 20 \
      -movflags +faststart "$ROUND/route_30s.mp4"
    D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$ROUND/route_30s.mp4")
    if [ "$(stat -f %z "$ROUND/route_30s.mp4")" -gt 15000000 ]; then
      KBPS=$(python3 -c "print(int(13.5e6*8/1000/float('$D')))")
      ffmpeg -loglevel error -y -framerate 60 -start_number $SKIP -i "$FR/MovieFrame%05d.png" -c:v libx264 -preset slow \
        -b:v ${KBPS}k -maxrate ${KBPS}k -bufsize $((KBPS*2))k -pix_fmt yuv420p -movflags +faststart "$ROUND/route_30s.mp4"
    fi
    cp "$TMP/route/route_30s_telemetry.csv" "$ROUND/"
    echo "movie: $ROUND/route_30s.mp4 $(stat -f %z "$ROUND/route_30s.mp4") bytes, ${D}s"
    python3 "$HERE/route_check.py" "$ROUND/route_30s_telemetry.csv" --json "$ROUND/route_check.json" | tail -8
    python3 "$HERE/../traversal/anim_check.py" "$ROUND/route_30s_telemetry.csv" route_30s > "$ROUND/anim_check.txt" 2>&1; tail -4 "$ROUND/anim_check.txt"
  else
    echo "movie FAILED (no frames or telemetry) — see $TMP/route"
  fi
fi

if has stills; then
  echo "== route stills 4K  GPU $(util) %"
  rm -rf "$TMP/route_4k"; wait_slot
  SHOTSP=$(python3 -c "print(','.join(str(round(float(t) + $PRE, 3)) for t in '$ROUTE_SHOTS'.split(',')))")
  $G capture --label manhattan -- "$UE_DIR/Scripts/run_game.sh" "$TMP/route_4k" -map "$MAP" -res 3840x2160 -shots "$SHOTSP" -name route -timeout 2400 \
    -exec "r.ScreenPercentage $SP" -- -benchmark -fps=60 -WHTravScript="$SCRIPT" -WHTravPreroll=$PRE \
    -WHTravCsv="$TMP/route_4k/stills_telemetry.csv" | tail -2
  I=0
  for T in ${ROUTE_SHOTS//,/ }; do
    p=$(ls "$TMP/route_4k/route_$(printf %02d $I)_"*.png 2>/dev/null | head -1)
    [ -n "$p" ] && sips -s format jpeg -s formatOptions 90 "$p" --out "$ROUND/stills/route_$(printf %02d $I)_t$(printf %04.1f $T).jpg" > /dev/null
    I=$((I + 1))
  done
fi

if has views; then
  for V in S1 S2 S4; do
    echo "== view $V 4K  GPU $(util) %"
    rm -rf "$TMP/view_$V"; wait_slot
    $G capture --label manhattan -- "$UE_DIR/Scripts/run_game.sh" "$TMP/view_$V" -map /Game/Maps/Manhattan_View_$V -res 3840x2160 -shots 14 -name view_$V \
      -timeout 1500 -exec "r.ScreenPercentage $SP" | tail -1
    p=$(ls "$TMP/view_$V/view_${V}_00_"*.png 2>/dev/null | head -1)
    [ -n "$p" ] && sips -s format jpeg -s formatOptions 90 "$p" --out "$ROUND/stills/view_$V.jpg" > /dev/null && echo "still: $ROUND/stills/view_$V.jpg"
  done
fi
