#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 22 critic pack (like with like): our upright side runs (w1, w2, sunlit facade) vs the reference side run (S3_wallrun_flip),
# our vertical run (c) vs wallrun_glass, swing / flip pairs for the other axes, and r21 vs r22 progress on the w2 side run.
# Refcuts are scratch-only copies (from the private refs), never committed.
set -euo pipefail
R=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-22
R21=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-21
C=/Users/midir/sm2-n1/_scratch/critic-P3-r22
X=$C/ours; mkdir -p $X $C/refcuts
cp -n /Users/midir/sm2-n1/_scratch/critic-P3-r21/refcuts/*.mp4 $C/refcuts/ 2>/dev/null || true
cut() { ffmpeg -loglevel error -y -ss "$3" -i "$2" -t "$4" -an -vf "crop=1186:1080:(iw-1186)/2:0,scale=610:556" -c:v libx264 -crf 18 -pix_fmt yuv420p "$X/$1.mp4"; }
# side-run windows from the telemetry (0.5 s lead-in, through the zip fire)
win() { python3 - "$1" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
s = [float(r['t']) for r in rows if r['sub'] == 'wallRunSide']
t0 = max(0.0, s[0] - 0.5); t1 = s[-1] + 0.45
print(f'{t0:.2f} {t1 - t0:.2f}')
PY
}
read W1S W1D <<< "$(win $R/w1_wallrun_tall_zip_telemetry.csv)"
read W2S W2D <<< "$(win $R/w2_wallrun_side_zip_telemetry.csv)"
read O2S O2D <<< "$(win $R21/w2_wallrun_side_zip_telemetry.csv)"
cut wallrun_vertical $R/c_wallrun_perch.mp4 2.4 2.0
cut wallrun_side_w1 $R/w1_wallrun_tall_zip.mp4 $W1S $W1D
cut wallrun_side_w2 $R/w2_wallrun_side_zip.mp4 $W2S $W2D
cut swing $R/a_swing_chain.mp4 0.5 8.0
cut multi_flip $R/f1_flow_backDouble.mp4 0.9 6.0
cut chain_flips $R/f4_chain_flips.mp4 0.9 11.5
cut side_r21 $R21/w2_wallrun_side_zip.mp4 $O2S $O2D
cut side_r22 $R/w2_wallrun_side_zip.mp4 $W2S $W2D
cat > $C/pairs.json <<JSON
[
 {"id":"wallrun-side-1","x":"$X/wallrun_side_w1.mp4","y":"$C/refcuts/S3_wallrun_flip.mp4","note":"running sideways along a building facade"},
 {"id":"wallrun-side-2","x":"$X/wallrun_side_w2.mp4","y":"$C/refcuts/S3_wallrun_flip.mp4","note":"running sideways along a building facade"},
 {"id":"wallrun-vertical","x":"$X/wallrun_vertical.mp4","y":"$C/refcuts/wallrun_glass.mp4","note":"running straight up a building facade"},
 {"id":"swing-chain","x":"$X/swing.mp4","y":"$C/refcuts/swing_chase.mp4","note":"fast web-swinging down a street canyon: the swing arc, the release and the airborne poses between webs"},
 {"id":"multi-flip","x":"$X/multi_flip.mp4","y":"$C/refcuts/S3_multi.mp4","note":"web release into an airborne pass with several somersaults, then back onto a web"},
 {"id":"chain-flips","x":"$X/chain_flips.mp4","y":"$C/refcuts/S45_chain.mp4","note":"consecutive swings with flips between the webs"},
 {"id":"progress-wallrun","x":"$X/side_r22.mp4","y":"$X/side_r21.mp4","note":"two versions of our game: the same sideways run along a facade"}
]
JSON
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py $C/pack $C/pairs.json
