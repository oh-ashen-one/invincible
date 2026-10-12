#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life capture driver (round 02): the running game (offscreen -game via Scripts/run_game.sh), every run wrapped in the GPU lock.
#   <round>/stills/S1_street_{1080p,4k}.jpg, S2_avenue_{1080p,4k}.jpg   city_shots.json S1 / S2 cameras in /Game/Tests/Life/Life_View_S1|S2, shot at game t = 28 s (-WHLifeClearAhead=24: the S1 camera stands in a lane; no moving car is drawn in a 24 m x 25 m corridor ahead of it, round 03; the S2 view does not use it)
#                                                                       (1080p runs also shoot t = 12, 16, 20, 24 into scratch: the detector series of the spec table)
#   <round>/street_clip_1080p60.mp4    18 s at 1.5 m/s along the avenue's west curb lane, sidewalk crowd on the left (Life_Street_Clip), fixed 1/60 s steps (-movie)
#   <round>/swing_clip_1080p60.mp4     10 s at swing height, 22 m over the avenue centre line, 25 m/s, aimed 70 m ahead (Life_Swing_Clip)
#   <round>/signal_clip_1080p60.mp4    10 s fixed camera, red -> green at the signal of street 160, queue of the southbound lanes (Life_Signal_Clip)
#   every clip: the rig holds 2.5 s at the start pose (warm-up: Lumen / TSR / exposure settle) and those frames are trimmed, so frame 0 of the mp4 is lit
#   <round>/probe_*.txt                WH_LIFE_* lines (frame counts, lane motion, queue, box stops, sim ms);  <round>/detector.json  spec detector numbers
#   <round>/perf_*.json / perf_gpu_*.json   GPU-locked frame times, life ON vs OFF (perf)
# usage: docs/night1/life/capture_round.sh <round dir> [warm|stills|clips|clip_street|clip_swing|clip_signal|detect|perf ...]      (heavy frames: _scratch/life/capture)
set -uo pipefail
ROUND="$(mkdir -p "$1" && cd "$1" && pwd)"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
UE_DIR="$(cd "$HERE/../../../unreal/WebHomage" && pwd)"
WT="$(cd "$HERE/../../.." && pwd)"
G=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
TMP=/Users/midir/sm2-n1/_scratch/life/capture
VENV=/Users/midir/sm2-n1/_scratch/life/venv
SP="${SP:-100}"          # r.ScreenPercentage of the stills / clips (100 = native internal resolution)
HOLD=2.5                 # warm-up seconds every clip rig holds and the capture trims
WANT=("$@"); [ ${#WANT[@]} -eq 0 ] && WANT=(warm stills clips detect perf)
has() { [[ " ${WANT[*]} " =~ " $1 " ]]; }
util() { ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1 | grep -o '[0-9]*$'; }
# Every engine launch: (1) the GUI session must be able to finish launching an app (2026-09-30: after a WindowServer watchdog restart every Unreal process hung at NSApplication launch, one stuck in the kernel;
# `tools/life/gui_ok.sh` is an 8 s AppKit launch probe, see HANDOFF.md), (2) the GPU lock (max 2 shared slots, a nested call inside a held slot passes through).
GUI="$WT/tools/life/gui_ok.sh"
cap() { if [ -x "$GUI" ] && ! "$GUI"; then echo "GUI session cannot launch apps: no engine started"; exit 75; fi; $G capture --label life -- "$@"; }
mkdir -p "$TMP" "$ROUND/stills"
echo "{\"sp\": $SP, \"maps\": [\"Life_View_S1\", \"Life_View_S2\", \"Life_Street_Clip\", \"Life_Swing_Clip\", \"Life_Signal_Clip\"], \"still_time_s\": 28, \"clip_hold_s\": $HOLD}" > "$ROUND/capture_settings.json"

if has warm; then
  echo "== warm-up render (shader compile, not kept)  GPU $(util) %"
  rm -rf "$TMP/warm"
  cap "$UE_DIR/Scripts/run_game.sh" "$TMP/warm" -map /Game/Tests/Life/Life_View_S1 -res 960x540 -quit 12 -name warm -timeout 2400 | tail -1
fi

if has stills; then
  for V in ${VIEWS:-S1 S2}; do      # VIEWS=S1: only the street view (a crowd-only change does not affect the avenue view)
    for RES in ${RESES:-1920x1080 3840x2160}; do   # RESES=1920x1080: skip the 4K pass (a verification hold)
      TAG=$([ "$RES" = 1920x1080 ] && echo 1080p || echo 4k)
      SHOTS=$([ "$TAG" = 1080p ] && echo 12,16,20,24,28 || echo 28)
      echo "== $V $RES  GPU $(util) %"
      rm -rf "$TMP/${V}_$TAG"
      cap "$UE_DIR/Scripts/run_game.sh" "$TMP/${V}_$TAG" -map /Game/Tests/Life/Life_View_$V -res $RES -shots $SHOTS -name $V -timeout 2400 \
        -exec "r.ScreenPercentage $SP" -- -WHLifeSample=8:30:1 $([ "$V" = S1 ] && echo -WHLifeClearAhead=24 ${S1_EXTRA:-}) | tail -2
      for p in "$TMP/${V}_$TAG/${V}_"*.png; do sips -s format jpeg -s formatOptions 92 "$p" --out "${p%.png}.jpg" > /dev/null; done
      p=$(ls "$TMP/${V}_$TAG/${V}_"*_t028.0.jpg 2>/dev/null | head -1)
      NAME=$([ "$V" = S1 ] && echo S1_street || echo S2_avenue)
      [ -n "$p" ] && cp "$p" "$ROUND/stills/${NAME}_$TAG.jpg"
      grep -E "WH_LIFE" "$TMP/${V}_$TAG/$V.log" | sed 's/^.*LogWHLifeProbe: Display: //' > "$ROUND/probe_${V}_$TAG.txt"
      cp "$UE_DIR/Saved/Logs/life_feet.csv" "$ROUND/feet_${V}_$TAG.csv" 2>/dev/null
    done
  done
fi

# one movie: <name> <map> <clip seconds> <fps extras...>
movie() {
  local NAME="$1" MAP="$2" DUR="$3"; shift 3
  local QUIT; QUIT=$(python3 -c "print($HOLD + $DUR + 0.05)")
  echo "== $NAME clip ($MAP, ${DUR}s + ${HOLD}s hold) 1080p60 movie  GPU $(util) %"
  rm -rf "$TMP/$NAME"
  cap "$UE_DIR/Scripts/run_game.sh" "$TMP/$NAME" -map "$MAP" -res 1920x1080 -quit "$QUIT" -name "$NAME" -movie -timeout 5400 \
    -exec "r.ScreenPercentage $SP" -- -WHLifeSample=$HOLD:$(python3 -c "print($HOLD + $DUR)"):0.5 "$@" | tail -3
  grep -E "WH_LIFE" "$TMP/$NAME/$NAME.log" | sed 's/^.*LogWHLifeProbe: Display: //' > "$ROUND/probe_${NAME}.txt"
  local FR="$TMP/$NAME/${NAME}_frames"; local START=$(python3 -c "print(int(round($HOLD*60))+1)"); local N=$(python3 -c "print(int(round($DUR*60)))")
  local OUTMP4="$ROUND/${NAME}_clip_1080p60.mp4"; [ "$NAME" = street ] && OUTMP4="$ROUND/street_clip_1080p60.mp4"
  ffmpeg -loglevel error -y -framerate 60 -start_number $START -i "$FR/MovieFrame%05d.png" -frames:v $N -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart "$OUTMP4"
  local SZ; SZ=$(stat -f %z "$OUTMP4")
  if [ "$SZ" -gt 15000000 ]; then
    local KBPS; KBPS=$(python3 -c "print(int(13.5e6*8/1000/$DUR))")
    ffmpeg -loglevel error -y -framerate 60 -start_number $START -i "$FR/MovieFrame%05d.png" -frames:v $N -c:v libx264 -preset slow -b:v ${KBPS}k -maxrate ${KBPS}k -bufsize $((KBPS*2))k -pix_fmt yuv420p -movflags +faststart "$OUTMP4"
  fi
  ls -la "$OUTMP4"
}

if has clips || has clip_street || has clip_swing || has clip_signal; then
  if has clips || has clip_street; then
    movie street /Game/Tests/Life/Life_Street_Clip 18 -WHLifeClearParked=238.5:100:243.5:155 -WHLifeFoot=5:17      # the walk is in the curb lane: the parked cars of z 100-155 are left out
    cp "$UE_DIR/Saved/Logs/life_feet.csv" "$ROUND/feet_clip.csv" 2>/dev/null
  fi
  # swing clip (round 03): 22 m up, aimed at the ground 70 m ahead of the camera (constant pitch), 88 deg lens; the rig values are also passed here so a stale map cannot change the shot
  if has clips || has clip_swing; then movie swing /Game/Tests/Life/Life_Swing_Clip 10 -WHLifeRig=250:232:250:-18:2200:250:0:-170:88:2.5:10 -WHLifeAimAhead=70:0; fi
  # signal clip: the pre-roll ends at cycle phase 30.5 (a queue of 3 cars in each southbound lane is standing at the line at clip start), the clip (after the 2.5 s hold) starts at 33 s:
  # avenue red until 40 s (clip t = 7 s), green after; 12.5 s so the queue pulls away and crosses the box on screen. Links 1201 / 1202 = southbound lanes queueing at street 160
  # (the queue depends on the pre-roll: another start phase gives another arrival pattern, phase 33.5 left 1 car in the queue)
  if has clips || has clip_signal; then movie signal /Game/Tests/Life/Life_Signal_Clip 12.5 -WHLifeSignalPhase=30.5 -WHLifeQueue=1201,1202; fi
fi

if has detect; then
  echo "== spec detector (YOLO11x-seg, conf 0.35, imgsz 1920) on stills and clips"
  ( source "$VENV/bin/activate"
    FILES=("$ROUND"/stills/*.jpg)
    for V in S1 S2; do for TAG in 1080p; do FILES+=("$TMP/${V}_$TAG/${V}_"*_t0[12]*.jpg); done; done
    # CPU device: no GPU lock needed (round 03). Full frame (detector.json) and the critic pack's 84 % centre crop (detector_crop84.json)
    python "$WT/tools/life/detect_counts.py" --device cpu --json "$ROUND/detector.json" "${FILES[@]}" "$ROUND"/*_clip_1080p60.mp4 2>&1 | grep -v Warning | tee "$ROUND/detector.txt"
    python "$WT/tools/life/detect_counts.py" --device cpu --crop 0.84 --json "$ROUND/detector_crop84.json" "${FILES[@]}" "$ROUND"/*_clip_1080p60.mp4 2>&1 | grep -v Warning > "$ROUND/detector_crop84.txt" )
fi

if has perf; then
  # exclusive lock (waits for GPU < 15 % for 10 s). Variants: off = -WHLifeOff (no traffic, no crowd), on = default. 4K output with r.ScreenPercentage 67 (TSR upscale).
  # Names / labels of the round tables: tools/life/perf_table.py. More variants: docs/night1/life/perf_variants.sh
  "$HERE/perf_variants.sh" "$ROUND" 3840x2160 off:-WHLifeOff on: crowd_only:-WHTrafficOff traffic_only:-WHCrowdOff
fi
