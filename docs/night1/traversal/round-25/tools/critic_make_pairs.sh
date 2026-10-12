#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 25 critic pack (like with like). Round target = the web line readable on every web frame of the swing chain (2-4 px at 1080p),
# so the swing / perch / run pairs keep the FULL 1080p pixel scale on both sides (centre 1440x1080 of ours and of the 1080p reference
# clip; abpack.py centre-crops 84 % and keeps the pixel scale) -- r22-r24 packs were 610x556 crops scaled to 512x466 (a 3 px line became ~1.3 px). Multi-flip and the two
# wall-run pairs keep the r24 610x556 refcuts (unchanged axes). Plus r24 vs r25 on the swing chain and the c perch.
# Refcuts are scratch-only copies (from the private refs), never committed.
set -euo pipefail
R=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-25
R24=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-24
REFS=/Users/midir/spiderman-learnings/refs
C=/Users/midir/sm2-n1/_scratch/critic-P3-r25
X=$C/ours; mkdir -p $X $C/refcuts
cp -n /Users/midir/sm2-n1/_scratch/critic-P3-r24/refcuts/*.mp4 $C/refcuts/ 2>/dev/null || true
# small (r24 style) and full-res cuts
cut() { ffmpeg -loglevel error -y -ss "$3" -i "$2" -t "$4" -an -vf "crop=1186:1080:(iw-1186)/2:0,scale=610:556" -c:v libx264 -crf 18 -pix_fmt yuv420p "$X/$1.mp4"; }
# full pixel scale, centre 1440x1080 of the 1920x1080 frame on both sides (drops the reference HUD corners: minimap, combo pop-ups)
cutf() { ffmpeg -loglevel error -y -ss "$3" -i "$2" -t "$4" -an -vf "scale=1920:1080,crop=1440:1080:240:0" -c:v libx264 -crf 16 -pix_fmt yuv420p "$X/$1.mp4"; }
refcutf() { ffmpeg -loglevel error -y -ss "$3" -i "$2" -t "$4" -an -vf "scale=1920:1080,crop=1440:1080:240:0" -c:v libx264 -crf 16 -pix_fmt yuv420p "$C/refcuts/$1.mp4"; }
refcutf swing_canyon_full $REFS/traversal/clips/swing-canyon-chase__nm_0139-0147.mp4 0 8
refcutf swing_street_full $REFS/traversal/clips/swing-low-street-speed__nm_0416-0424.mp4 0 8
refcutf perch_golden_full $REFS/streets/clips/skyline-perch-golden__nm_0844-0852.mp4 0 3.1
refcutf run_full $REFS/animation/clips/run-toward-camera__dn_0418-0425.mp4 0 7
win() { python3 - "$1" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
s = [float(r['t']) for r in rows if r['sub'] == 'wallRunSide']
t0 = max(0.0, s[0] - 0.5); t1 = s[-1] + 0.45
print(f'{t0:.2f} {t1 - t0:.2f}')
PY
}
pick() { [ -f "$R/$1.mp4" ] && echo "$R/$1.mp4" || echo "$R24/$1.mp4"; }   # r24 file when not re-captured this round
W2=$(pick w2_wallrun_side_zip); read W2S W2D <<< "$(win ${W2%.mp4}_telemetry.csv)"
cutf swing_1 $R/a_swing_chain.mp4 0.5 8.0
cutf swing_2 $R/a_swing_chain.mp4 7.5 8.0
cutf perch_c $R/c_wallrun_perch.mp4 7.4 3.1
cutf run_p1 $R/p1_pawn_run.mp4 2.0 7.0
cut multi_flip $(pick f1_flow_backDouble) 0.9 6.0
cut vertical_w1 $(pick w1_wallrun_tall_zip) 1.0 2.5
cut wallrun_side_w2 $W2 $W2S $W2D
cutf swing_r24 $R24/a_swing_chain.mp4 0.5 8.0
cutf swing_r25 $R/a_swing_chain.mp4 0.5 8.0
cutf perch_r24 $R24/c_wallrun_perch.mp4 7.4 3.1
cutf perch_r25 $R/c_wallrun_perch.mp4 7.4 3.1
cat > $C/pairs.json <<JSON
[
 {"id":"swing-chain-1","x":"$X/swing_1.mp4","y":"$C/refcuts/swing_canyon_full.mp4","note":"fast web-swinging down a street canyon: can you follow the web line from the hand to the frame edge on every frame, over sky, pale stone and dark glass; arc altitude and the poses between webs"},
 {"id":"swing-chain-2","x":"$X/swing_2.mp4","y":"$C/refcuts/swing_street_full.mp4","note":"fast web-swinging down a street: can you follow the web line from the hand to the frame edge on every frame, over sky, pale stone and dark glass; arc altitude and the poses between webs"},
 {"id":"rooftop-perch","x":"$X/perch_c.mp4","y":"$C/refcuts/perch_golden_full.mp4","note":"on a rooftop: the camera framing while the hero stands, zips to a ledge and perches (is he always in frame, does the view jump)"},
 {"id":"street-run","x":"$X/run_p1.mp4","y":"$C/refcuts/run_full.mp4","note":"the hero running down a street: step rhythm, stride, body motion"},
 {"id":"multi-flip","x":"$X/multi_flip.mp4","y":"$C/refcuts/S3_multi.mp4","note":"web release into an airborne pass with several somersaults, then back onto a web"},
 {"id":"wallrun-vertical","x":"$X/vertical_w1.mp4","y":"$C/refcuts/wallrun_glass.mp4","note":"running straight up a building facade"},
 {"id":"wallrun-side","x":"$X/wallrun_side_w2.mp4","y":"$C/refcuts/S3_wallrun_flip.mp4","note":"running sideways along a building facade"},
 {"id":"progress-swing","x":"$X/swing_r25.mp4","y":"$X/swing_r24.mp4","note":"two versions of our game: the same swing chain from the same start -- which web line reads better, which is the better swing"},
 {"id":"progress-perch","x":"$X/perch_r25.mp4","y":"$X/perch_r24.mp4","note":"two versions of our game: the same rooftop turn, zip and perch -- which keeps the hero framed, which view is steadier"}
]
JSON
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py $C/pack $C/pairs.json
