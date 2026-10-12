#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 24 critic pack (like with like): the swing chain (round target T7 / T3: altitude, rope time) vs the two reference chase chains,
# the c roof camera turn (hard gate), the vertical / side wall runs and the flips for the other axes, and r23 vs r24 on the same swing
# chain window. Refcuts are scratch-only copies (from the private refs), never committed.
set -euo pipefail
R=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-24
R23=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-23
C=/Users/midir/sm2-n1/_scratch/critic-P3-r24
X=$C/ours; mkdir -p $X $C/refcuts
cp -n /Users/midir/sm2-n1/_scratch/critic-P3-r23/refcuts/*.mp4 $C/refcuts/ 2>/dev/null || true
cut() { ffmpeg -loglevel error -y -ss "$3" -i "$2" -t "$4" -an -vf "crop=1186:1080:(iw-1186)/2:0,scale=610:556" -c:v libx264 -crf 18 -pix_fmt yuv420p "$X/$1.mp4"; }
win() { python3 - "$1" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
s = [float(r['t']) for r in rows if r['sub'] == 'wallRunSide']
t0 = max(0.0, s[0] - 0.5); t1 = s[-1] + 0.45
print(f'{t0:.2f} {t1 - t0:.2f}')
PY
}
read W2S W2D <<< "$(win $R/w2_wallrun_side_zip_telemetry.csv)"
cut swing_1 $R/a_swing_chain.mp4 0.5 8.0
cut swing_2 $R/a_swing_chain.mp4 7.5 8.0
cut vertical_w2 $R/w2_wallrun_side_zip.mp4 0.9 2.0
cut wallrun_side_w2 $R/w2_wallrun_side_zip.mp4 $W2S $W2D
cut multi_flip $R/f1_flow_backDouble.mp4 0.9 6.0
cut swing_r23 $R23/a_swing_chain.mp4 0.5 8.0
cut swing_r24 $R/a_swing_chain.mp4 0.5 8.0
cat > $C/pairs.json <<JSON
[
 {"id":"swing-chain-1","x":"$X/swing_1.mp4","y":"$C/refcuts/swing_chase.mp4","note":"fast web-swinging down a street canyon: altitude of each arc (roofline to street and back), rope time vs airborne time, the poses between webs"},
 {"id":"swing-chain-2","x":"$X/swing_2.mp4","y":"$C/refcuts/S45_chain.mp4","note":"fast web-swinging down a street canyon: altitude of each arc (roofline to street and back), rope time vs airborne time, the poses between webs"},
 {"id":"wallrun-vertical","x":"$X/vertical_w2.mp4","y":"$C/refcuts/wallrun_glass.mp4","note":"running straight up a building facade, seen from below"},
 {"id":"wallrun-side","x":"$X/wallrun_side_w2.mp4","y":"$C/refcuts/S3_wallrun_flip.mp4","note":"running sideways along a building facade"},
 {"id":"multi-flip","x":"$X/multi_flip.mp4","y":"$C/refcuts/S3_multi.mp4","note":"web release into an airborne pass with several somersaults, then back onto a web"},
 {"id":"progress-swing","x":"$X/swing_r24.mp4","y":"$X/swing_r23.mp4","note":"two versions of our game: the same swing chain from the same start"}
]
JSON
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py $C/pack $C/pairs.json
