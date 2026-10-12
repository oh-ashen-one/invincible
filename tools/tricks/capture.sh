#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C capture driver: replays docs/night1/tricks/scripts/<seq>.json in the REAL game (-game, offscreen, lit /Game/Maps/Manhattan) through
# the GPU lock and writes per sequence:
#   <round>/<seq>.mp4             1920x1080 60 fps (fixed 1/60 s step, every frame dumped, r.ScreenPercentage 100 = native internal), <= 15 MB
#   <round>/<seq>_telemetry.csv   per-frame traversal telemetry (WebTravCharacter)
#   <round>/<seq>_pose.csv.gz     rendered-bone log of the same run (-WHTrickPose, WebTravFlips.cpp)
# usage: tools/tricks/capture.sh <round dir> <seq> [<seq> ...]
#   env QUIT_<seq>=s (default 60.5); EXTRA_ARGS="-WHTrickTempo=0 ..."; NOHOLD=1 = the caller already holds a capture slot
#   env SEGS="0:20,20:40,40:60.5" renders the sequence as frame-dump WINDOWS of the same deterministic run (one engine run per window, each
#       its own gpu_slot hold; -WHTrickDumpFrom/To in WebTravFlips.cpp): r01 found background-priority movie dumps at ~1 frame/s, so 60 s
#       does not fit one 40-min hold. SEG_ONLY=k renders only window k (0-based) and stops; the merge runs once every window has frames.
set -uo pipefail
ROUND="$(mkdir -p "$1" && cd "$1" && pwd)"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
WT="$(cd "$HERE/../.." && pwd)"
UE_DIR="$WT/unreal/WebHomage"
SCR="$WT/docs/night1/tricks/scripts"
TMP=/Users/midir/sm2-n1/_scratch/tricks/capture
MAP="${TRICK_MAP:-/Game/Maps/Manhattan}"
GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
PRE=0.8
mkdir -p "$TMP"
RUNG() { if [ -n "${NOHOLD:-}" ]; then "$UE_DIR/Scripts/run_game.sh" "$@"; else "$GPU" capture --label tricks -- "$UE_DIR/Scripts/run_game.sh" "$@"; fi; }
for NAME in "$@"; do
  Q=$(eval echo "\${QUIT_${NAME}:-60.5}")
  SEGL="${SEGS:-0:$Q}"
  IFS=',' read -r -a SEGA <<< "$SEGL"
  K=0
  for SG in "${SEGA[@]}"; do
    if [ -n "${SEG_ONLY:-}" ] && [ "$SEG_ONLY" != "$K" ]; then K=$((K+1)); continue; fi
    A="${SG%%:*}"; B="${SG##*:}"
    D="$TMP/$NAME/seg$K"
    case "$D" in /Users/midir/sm2-n1/_scratch/tricks/*) rm -rf "$D";; *) echo "bad tmp $D"; exit 1;; esac
    mkdir -p "$D"
    QUITP=$(python3 -c "print(round(min($Q, $B + 0.1) + $PRE, 3))")
    echo "== $NAME seg $K [$A, $B) quit $QUITP  (GPU $(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1))  $(date +%T)"
    RUNG "$D" -map "$MAP" -res 1920x1080 -quit "$QUITP" -name "$NAME" -movie -timeout 3000 \
      -exec "r.ScreenPercentage 100" -- -WHTravScript="$SCR/$NAME.json" -WHTravPreroll=$PRE -WHTravMask -WHTrickPose="$D/${NAME}_pose.csv" \
      -WHTrickDumpFrom=$A -WHTrickDumpTo=$B ${EXTRA_ARGS:-} | tail -3
    echo "seg $K done $(date +%T): $(ls "$D/${NAME}_frames" 2>/dev/null | wc -l | tr -d ' ') frames; $(grep -o 'WH_TRICK_DUMP.*' "$D/$NAME.log" | tr '\n' ' ')"
    K=$((K+1))
  done
  # ---- merge (every window must have frames)
  NSEG=${#SEGA[@]}; OK=1
  for ((K=0; K<NSEG; K++)); do [ -d "$TMP/$NAME/seg$K/${NAME}_frames" ] || OK=0; done
  if [ $OK = 0 ]; then echo "merge of $NAME waits for every window ($NSEG)"; continue; fi
  M="$TMP/$NAME/merged"; rm -rf "$M"; mkdir -p "$M"
  # stitch by SEQUENCE frame: in a window starting at A s, dumped frame j shows sequence frame round(A*60) - 3 + j (render readback latency;
  # r01: window 1's frames 0-1 were stale, its frame 2 matched the earlier run's frame for 24.983 s pixel for pixel). A window dir holding
  # ALIGNED (window 0 rebuilt from an earlier run) maps j -> j. Frames already covered by the previous window are skipped.
  N=$(python3 - "$TMP/$NAME" "$NAME" "$M" "$SEGL" <<'PY'
import os, sys
d, name, m, segl = sys.argv[1:5]
last, n = -1, 0
for k, sg in enumerate(segl.split(',')):
    a = float(sg.split(':')[0]); fr = os.path.join(d, 'seg%d' % k, name + '_frames')
    files = sorted(os.listdir(fr))
    aligned = os.path.exists(os.path.join(d, 'seg%d' % k, 'ALIGNED'))
    for j, f in enumerate(files):
        q = j if aligned else int(round(a * 60)) - 3 + j
        if (not aligned and j < 2) or q <= last: continue
        if q != last + 1: print('GAP before sequence frame %d (window %d)' % (q, k), file=sys.stderr)
        os.link(os.path.join(fr, f), os.path.join(m, 'F%05d.png' % n)); n += 1; last = q
    print('window %d: last sequence frame %d' % (k, last), file=sys.stderr)
print(n)
PY
)
  LAST=$((NSEG-1))
  # determinism: the telemetry of every window's run must match the last one (same frames, same positions)
  python3 - "$TMP/$NAME" $NSEG "$NAME" <<'PY'
import csv, sys
d, n, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]
ref = list(csv.DictReader(open('%s/seg%d/%s_telemetry.csv' % (d, n - 1, name))))
for k in range(n - 1):
    T = list(csv.DictReader(open('%s/seg%d/%s_telemetry.csv' % (d, k, name))))
    m = min(len(T), len(ref))
    bad = sum(1 for a, b in zip(T[:m], ref[:m]) if (a['x_m'], a['y_m'], a['z_m'], a['flip_prog'], a['flip_t']) != (b['x_m'], b['y_m'], b['z_m'], b['flip_prog'], b['flip_t']))
    print('determinism: seg%d vs seg%d over %d common rows: %d rows differ (position / flip state)' % (k, n - 1, m, bad))
PY
  NT=$(( $(wc -l < "$TMP/$NAME/seg$LAST/${NAME}_telemetry.csv") - 1 ))
  echo "merged frames $N, telemetry rows $NT"
  ffmpeg -loglevel error -y -framerate 60 -i "$M/F%05d.png" -c:v libx264 -pix_fmt yuv420p -crf 16 -movflags +faststart "$TMP/$NAME/${NAME}_hq.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/$NAME/${NAME}_hq.mp4")
  KBPS=$(python3 -c "print(min(12000, int(13.8e6*8/1000/float('$DUR'))))")
  ffmpeg -loglevel error -y -i "$TMP/$NAME/${NAME}_hq.mp4" -c:v libx264 -preset slow -b:v ${KBPS}k -maxrate $((KBPS*3/2))k -bufsize $((KBPS*2))k \
    -pix_fmt yuv420p -movflags +faststart "$ROUND/$NAME.mp4"
  cp "$TMP/$NAME/seg$LAST/${NAME}_telemetry.csv" "$ROUND/"
  gzip -c "$TMP/$NAME/seg$LAST/${NAME}_pose.csv" > "$ROUND/${NAME}_pose.csv.gz"
  echo "movie: $ROUND/$NAME.mp4 $(stat -f %z "$ROUND/$NAME.mp4") bytes, ${DUR}s"
done
