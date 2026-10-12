#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 23 critic pack (like with like): our VERTICAL wall runs (w2 1.0-2.8 s on the sunlit tower, c 2.65-4.15 s on the loft) vs the
# reference vertical runs (wallrun_glass, wallrun_empire), the w2 side run vs S3_wallrun_flip (gate), swing / flips for the other axes,
# and r22 vs r23 progress on the w2 vertical run. Refcuts are scratch-only copies (from the private refs), never committed.
set -euo pipefail
R=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-23
R22=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-22
C=/Users/midir/sm2-n1/_scratch/critic-P3-r23
X=$C/ours; mkdir -p $X $C/refcuts
cp -n /Users/midir/sm2-n1/_scratch/critic-P3-r22/refcuts/*.mp4 $C/refcuts/ 2>/dev/null || true
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
cut vertical_w2 $R/w2_wallrun_side_zip.mp4 0.9 2.0
cut vertical_c $R/c_wallrun_perch.mp4 2.55 1.7
cut wallrun_side_w2 $R/w2_wallrun_side_zip.mp4 $W2S $W2D
cut swing $R/a_swing_chain.mp4 0.5 8.0
cut multi_flip $R/f1_flow_backDouble.mp4 0.9 6.0
cut vertical_r22 $R22/w2_wallrun_side_zip.mp4 0.9 2.0
cut vertical_r23 $R/w2_wallrun_side_zip.mp4 0.9 2.0
cat > $C/pairs.json <<JSON
[
 {"id":"wallrun-vertical-1","x":"$X/vertical_w2.mp4","y":"$C/refcuts/wallrun_glass.mp4","note":"running straight up a building facade, seen from below"},
 {"id":"wallrun-vertical-2","x":"$X/vertical_c.mp4","y":"$C/refcuts/wallrun_empire.mp4","note":"running straight up a building facade, seen from below"},
 {"id":"wallrun-side","x":"$X/wallrun_side_w2.mp4","y":"$C/refcuts/S3_wallrun_flip.mp4","note":"running sideways along a building facade"},
 {"id":"swing-chain","x":"$X/swing.mp4","y":"$C/refcuts/swing_chase.mp4","note":"fast web-swinging down a street canyon: the swing arc, the release and the airborne poses between webs"},
 {"id":"multi-flip","x":"$X/multi_flip.mp4","y":"$C/refcuts/S3_multi.mp4","note":"web release into an airborne pass with several somersaults, then back onto a web"},
 {"id":"progress-vertical","x":"$X/vertical_r23.mp4","y":"$X/vertical_r22.mp4","note":"two versions of our game: the same run straight up a facade"}
]
JSON
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py $C/pack $C/pairs.json
