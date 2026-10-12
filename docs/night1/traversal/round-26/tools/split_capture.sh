#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r26 split movie capture (the shared GPU / CPU ran this round's 1080p movies at ~0.25-0.3 frames/s: a 984-frame clip does not fit in one
# 2400 s GPU hold). The replay is deterministic (fixed 1/60 s step), so a clip is rendered in two runs, each inside its own hold:
#   A  <clip> <tm>   the normal movie run, quitting at sequence time tm + 0.5 s (0.5 s overlap)       -> $TMP/<clip>_A
#   B  <clip> <tm>   the whole clip again with -WHMovieFrom=tm: frames are written only from tm on    -> $TMP/<clip>_B (+ telemetry)
#   merge <clip> <tm> <round dir>   A frames before tm + B frames; the 0.5 s overlap is compared pixel for pixel (OVERLAP.txt) before the
#                    movie is encoded like capture_round.sh (trim = frames - telemetry rows, H.264, <= 15 MB); telemetry = run B's
# Runs INSIDE a gpu_slot hold (called by hold.sh). Same arguments as capture_round.sh (map, 1920x1080, r.ScreenPercentage 100, pre-roll 0.8 s, mask).
set -uo pipefail
MODE=$1; NAME=$2; TM=$3
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SCR=$TD/scripts/city; TMP=/Users/midir/sm2-n1/_scratch/traversal/capture; MAP=/Game/Maps/Manhattan; PRE=0.8
case $NAME in
  a_swing_chain) Q=15.6;; c_wallrun_perch) Q=10.5;; f1_flow_backDouble) Q=9.0;; f4_chain_flips) Q=13.3;; w1_wallrun_tall_zip) Q=7.5;;
  w2_wallrun_side_zip) Q=7;; r1_roofrun_zip) Q=9.5;; s1_high_swing) Q=6.0;; x1_rmb_cancel_flip) Q=4.0;; x2_rmb_cancel_wall) Q=5.0;;
  m1_mouse_swing) Q=6.0;; p1_pawn_run) Q=12.0;; *) echo "unknown clip $NAME"; exit 2;;
esac
SPECIAL=""; [ "$NAME" = m1_mouse_swing ] && SPECIAL="-WHTravInputTest=mouseLook -WHMouseTestPx=40"
run() {   # out quit extra...
  local O=$1 QQ=$2; shift 2
  rm -rf "$O"
  "$UE/Scripts/run_game.sh" "$O" -map "$MAP" -res 1920x1080 -quit "$QQ" -name "$NAME" -movie -timeout 2300 -exec "r.ScreenPercentage 100" \
    -- -WHTravScript="$SCR/$NAME.json" -WHTravPreroll=$PRE -WHTravMask $SPECIAL ${EXTRA_ARGS:-} -WHMovieAsync "$@" < /dev/null | tail -3
  rm -f "$O/$NAME.mp4"   # run_game's untrimmed preview movie
}
case $MODE in
  A) run $TMP/${NAME}_A $(python3 -c "print(round($TM + 0.5 + $PRE, 3))") ;;
  B) run $TMP/${NAME}_B $(python3 -c "print(round($Q + $PRE, 3))") -WHMovieFrom=$TM
     grep -h "WH_TRAV movie dump" $TMP/${NAME}_B/$NAME.log | sed 's/^.*Display: //' ;;
  merge)
    RD=$4; A=$TMP/${NAME}_A; B=$TMP/${NAME}_B; M=$TMP/${NAME}_M; rm -rf $M; mkdir -p $M/f
    python3 - "$A" "$B" "$M" "$NAME" "$TM" <<'PY' || exit 1
import csv, os, sys, shutil
import numpy as np
from PIL import Image
A, B, M, name, tm = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
fa = sorted(os.listdir(f'{A}/{name}_frames')); fb = sorted(os.listdir(f'{B}/{name}_frames'))
ra = list(csv.DictReader(open(f'{A}/{name}_telemetry.csv'))); rb = list(csv.DictReader(open(f'{B}/{name}_telemetry.csv')))
skip_a = len(fa) - len(ra)
jb = next(i for i, r in enumerate(rb) if float(r['t']) >= tm - 1e-6)
# the A rows must equal the B rows (deterministic replay)
dmax = max(abs(float(x[k]) - float(y[k])) for x, y in zip(ra, rb) for k in ('x_m', 'y_m', 'z_m', 'cam_x', 'cam_y', 'cam_z'))
over = []
for k in range(0, min(len(fa) - (skip_a + jb), len(fb)), 6):
    ia = np.asarray(Image.open(f'{A}/{name}_frames/{fa[skip_a + jb + k]}').convert('RGB'), dtype=np.int16)
    ib = np.asarray(Image.open(f'{B}/{name}_frames/{fb[k]}').convert('RGB'), dtype=np.int16)
    over.append((k, float(np.abs(ia - ib).mean()), float((np.abs(ia - ib).max(axis=2) > 24).mean())))
seq = [f'{A}/{name}_frames/{f}' for f in fa[:skip_a + jb]] + [f'{B}/{name}_frames/{f}' for f in fb]
for i, p in enumerate(seq): os.link(p, f'{M}/f/MovieFrame{i:05d}.png')
shutil.copy(f'{B}/{name}_telemetry.csv', f'{M}/{name}_telemetry.csv')
rep = [f'# split capture {name} at t={tm}: A {len(fa)} frames / {len(ra)} rows (skip {skip_a}), B {len(fb)} frames / {len(rb)} rows, first B row {jb} (t={rb[jb]["t"]})',
       f'  telemetry A vs B over {min(len(ra), len(rb))} rows: max |pos / cam| diff {dmax:.4f} m -> ' + ('SAME' if dmax < 0.01 else 'DIFF'),
       f'  overlap frames (A row {jb}+k vs B frame k): ' + ', '.join(f'k{k}: mean {m:.2f}/255, px>24 {p * 100:.2f} %' for k, m, p in over),
       f'  merged {len(seq)} frames, telemetry rows {len(rb)} -> trim {len(seq) - len(rb)}']
open(f'{M}/OVERLAP.txt', 'w').write('\n'.join(rep) + '\n'); print('\n'.join(rep))
ok = dmax < 0.01 and over and max(m for _, m, _ in over) < 3.0
sys.exit(0 if ok else 1)
PY
    RC=$?
    NF=$(ls $M/f | wc -l | tr -d ' '); NT=$(( $(wc -l < $M/${NAME}_telemetry.csv) - 1 )); SKIP=$(( NF - NT ))
    ffmpeg -loglevel error -y -framerate 60 -start_number $SKIP -i "$M/f/MovieFrame%05d.png" -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart "$RD/$NAME.mp4"
    DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RD/$NAME.mp4")
    if [ "$(stat -f %z "$RD/$NAME.mp4")" -gt 15000000 ]; then
      KBPS=$(python3 -c "print(int(13.5e6*8/1000/float('$DUR')))")
      ffmpeg -loglevel error -y -framerate 60 -start_number $SKIP -i "$M/f/MovieFrame%05d.png" -c:v libx264 -preset slow -b:v ${KBPS}k -maxrate ${KBPS}k -bufsize $((KBPS*2))k -pix_fmt yuv420p -movflags +faststart "$RD/$NAME.mp4"
    fi
    cp $M/${NAME}_telemetry.csv "$RD/"; mkdir -p "$RD/split"; cp $M/OVERLAP.txt "$RD/split/${NAME}_OVERLAP.txt"
    echo "movie: $RD/$NAME.mp4 $(stat -f %z "$RD/$NAME.mp4") bytes, ${DUR}s (overlap check rc $RC)" ;;
esac
