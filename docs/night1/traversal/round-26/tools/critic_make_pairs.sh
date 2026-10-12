#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 26 critic pack (like with like). Round target: the w1 vertical wall run as a sprint (knees, arms, a new pose every 0.3 s) at a
# 4-7 m camera, the original suit in every clip, no regression on rope / perch / pawn run / flips. Every clip pair keeps the FULL 1080p pixel
# scale (centre 1440x1080 of ours and of the 1080p reference clip; abpack.py centre-crops 84 %). Every pair also gets an image pair: a
# <= 2048 px wide contact sheet of each side at the same sample times (the r25 critic could only open contact sheets).
# Progress pairs r25 vs r26: w1, c, a, f4 (the r25 f4 file is round-24's, not re-captured in r25).
# Refcuts are scratch-only copies (from the private refs), never committed.
set -euo pipefail
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
R=$TD/round-26; R25=$TD/round-25; R24=$TD/round-24
REFS=/Users/midir/spiderman-learnings/refs
C=/Users/midir/sm2-n1/_scratch/critic-P3-r26
X=$C/ours; S=$C/sheets; mkdir -p $X $S $C/refcuts
cp -n /Users/midir/sm2-n1/_scratch/critic-P3-r25/refcuts/*.mp4 $C/refcuts/ 2>/dev/null || true
SH="python3 $R/tools/sheets.py clip"
cutf() { ffmpeg -loglevel error -y -ss "$3" -i "$2" -t "$4" -an -vf "scale=1920:1080,crop=1440:1080:240:0" -c:v libx264 -crf 16 -pix_fmt yuv420p "$X/$1.mp4"; }
refcutf() { ffmpeg -loglevel error -y -ss "$3" -i "$2" -t "$4" -an -vf "scale=1920:1080,crop=1440:1080:240:0" -c:v libx264 -crf 16 -pix_fmt yuv420p "$C/refcuts/$1.mp4"; }
refcutf wallrun_glass_full $REFS/traversal/clips/wallrun-glass-midday__dn_0011-0019.mp4 1.7 6.0
refcutf wallrun_tower_full $REFS/traversal/clips/wallrun-glass-tower__nm_0814-0822.mp4 0 6.0
[ -f $C/refcuts/swing_canyon_full.mp4 ] || refcutf swing_canyon_full $REFS/traversal/clips/swing-canyon-chase__nm_0139-0147.mp4 0 8
[ -f $C/refcuts/swing_street_full.mp4 ] || refcutf swing_street_full $REFS/traversal/clips/swing-low-street-speed__nm_0416-0424.mp4 0 8
[ -f $C/refcuts/perch_golden_full.mp4 ] || refcutf perch_golden_full $REFS/streets/clips/skyline-perch-golden__nm_0844-0852.mp4 0 3.1
[ -f $C/refcuts/run_full.mp4 ] || refcutf run_full $REFS/animation/clips/run-toward-camera__dn_0418-0425.mp4 0 7
win() { python3 - "$1" "$2" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
s = [float(r['t']) for r in rows if r['sub'] == sys.argv[2]]
t0 = max(0.0, s[0] - 0.4); t1 = s[-1] + 0.45
print(f'{t0:.2f} {t1 - t0:.2f}')
PY
}
read W2S W2D <<< "$(win $R/w2_wallrun_side_zip_telemetry.csv wallRunSide)"
read CWS CWD <<< "$(win $R/c_wallrun_perch_telemetry.csv wallRun)"
F4OLD=$R24/f4_chain_flips.mp4
cutf vertical_w1 $R/w1_wallrun_tall_zip.mp4 0.75 3.0
cutf vertical_c $R/c_wallrun_perch.mp4 $CWS $CWD
cutf wallrun_side_w2 $R/w2_wallrun_side_zip.mp4 $W2S $W2D
cutf swing_1 $R/a_swing_chain.mp4 0.5 8.0
cutf swing_2 $R/a_swing_chain.mp4 7.5 8.0
cutf perch_c $R/c_wallrun_perch.mp4 7.4 3.1
cutf run_p1 $R/p1_pawn_run.mp4 2.0 7.0
cutf multi_flip $R/f1_flow_backDouble.mp4 0.9 6.0
cutf chain_flips $R/f4_chain_flips.mp4 0.0 13.0
cutf w1_r25 $R25/w1_wallrun_tall_zip.mp4 0.75 3.0
cutf w1_r26 $R/w1_wallrun_tall_zip.mp4 0.75 3.0
cutf perch_r25 $R25/c_wallrun_perch.mp4 7.4 3.1
cutf perch_r26 $R/c_wallrun_perch.mp4 7.4 3.1
cutf swing_r25 $R25/a_swing_chain.mp4 0.5 8.0
cutf swing_r26 $R/a_swing_chain.mp4 0.5 8.0
cutf f4_r25 $F4OLD 0.0 13.0
cutf f4_r26 $R/f4_chain_flips.mp4 0.0 13.0
# contact sheets (same sample times on both sides of a pair; the clip cuts start at 0)
sheet() { $SH "$1" "$S/$2.jpg" 0 "$3" "$4" 5; }
for p in "vertical_w1 2.9 10" "vertical_c 1.5 10" "wallrun_side_w2 2.5 10" "swing_1 7.8 10" "swing_2 7.8 10" "perch_c 3.0 10" "run_p1 6.8 10" \
         "multi_flip 5.8 10" "chain_flips 12.8 15" "w1_r25 2.9 10" "w1_r26 2.9 10" "perch_r25 3.0 10" "perch_r26 3.0 10" "swing_r25 7.8 10" "swing_r26 7.8 10" \
         "f4_r25 12.8 15" "f4_r26 12.8 15"; do set -- $p; sheet $X/$1.mp4 $1 $2 $3; done
for p in "wallrun_glass_full 5.8 10" "wallrun_tower_full 5.8 10" "S3_wallrun_flip 2.5 10" "swing_canyon_full 7.8 10" "swing_street_full 7.8 10" \
         "perch_golden_full 3.0 10" "run_full 6.8 10" "S3_multi 5.8 10"; do set -- $p; sheet $C/refcuts/$1.mp4 ref_$1 $2 $3; done
cat > $C/pairs.json <<JSON
[
 {"id":"wallrun-vertical","x":"$X/vertical_w1.mp4","y":"$C/refcuts/wallrun_glass_full.mp4","note":"running straight up a building facade, seen from below: is it a sprint (knees driving, arms alternating, a new limb pose every few frames) or a climb; how far is the camera"},
 {"id":"wallrun-vertical-sheet","x":"$S/vertical_w1.jpg","y":"$S/ref_wallrun_glass_full.jpg","note":"contact sheet of the same two clips (10 evenly spaced frames, left to right, top to bottom)"},
 {"id":"wallrun-vertical-2","x":"$X/vertical_c.mp4","y":"$C/refcuts/wallrun_tower_full.mp4","note":"running up a building facade from the street"},
 {"id":"wallrun-vertical-2-sheet","x":"$S/vertical_c.jpg","y":"$S/ref_wallrun_tower_full.jpg","note":"contact sheet of the same two clips"},
 {"id":"wallrun-side","x":"$X/wallrun_side_w2.mp4","y":"$C/refcuts/S3_wallrun_flip.mp4","note":"running sideways along a building facade"},
 {"id":"wallrun-side-sheet","x":"$S/wallrun_side_w2.jpg","y":"$S/ref_S3_wallrun_flip.jpg","note":"contact sheet of the same two clips"},
 {"id":"swing-chain-1","x":"$X/swing_1.mp4","y":"$C/refcuts/swing_canyon_full.mp4","note":"fast web-swinging down a street canyon: can you follow the web line from the hand to the frame edge on every frame; arc altitude and the poses between webs"},
 {"id":"swing-chain-1-sheet","x":"$S/swing_1.jpg","y":"$S/ref_swing_canyon_full.jpg","note":"contact sheet of the same two clips"},
 {"id":"swing-chain-2","x":"$X/swing_2.mp4","y":"$C/refcuts/swing_street_full.mp4","note":"fast web-swinging down a street: web line on every frame, arc altitude, poses between webs"},
 {"id":"swing-chain-2-sheet","x":"$S/swing_2.jpg","y":"$S/ref_swing_street_full.jpg","note":"contact sheet of the same two clips"},
 {"id":"rooftop-perch","x":"$X/perch_c.mp4","y":"$C/refcuts/perch_golden_full.mp4","note":"on a rooftop: the camera framing while the hero stands, zips to a ledge and perches (is he always in frame, does the view jump)"},
 {"id":"rooftop-perch-sheet","x":"$S/perch_c.jpg","y":"$S/ref_perch_golden_full.jpg","note":"contact sheet of the same two clips"},
 {"id":"street-run","x":"$X/run_p1.mp4","y":"$C/refcuts/run_full.mp4","note":"the hero running down a street: step rhythm, stride, body motion"},
 {"id":"street-run-sheet","x":"$S/run_p1.jpg","y":"$S/ref_run_full.jpg","note":"contact sheet of the same two clips"},
 {"id":"multi-flip","x":"$X/multi_flip.mp4","y":"$C/refcuts/S3_multi.mp4","note":"web release into an airborne pass with several somersaults, then back onto a web"},
 {"id":"multi-flip-sheet","x":"$S/multi_flip.jpg","y":"$S/ref_S3_multi.jpg","note":"contact sheet of the same two clips"},
 {"id":"progress-wallrun","x":"$X/w1_r26.mp4","y":"$X/w1_r25.mp4","note":"two versions of our game: the same vertical wall run -- which reads as a sprint, which camera distance frames him better"},
 {"id":"progress-wallrun-sheet","x":"$S/w1_r26.jpg","y":"$S/w1_r25.jpg","note":"contact sheet of the same two clips"},
 {"id":"progress-perch","x":"$X/perch_r26.mp4","y":"$X/perch_r25.mp4","note":"two versions of our game: the same rooftop turn, zip and perch -- which keeps the hero framed, which view is steadier"},
 {"id":"progress-perch-sheet","x":"$S/perch_r26.jpg","y":"$S/perch_r25.jpg","note":"contact sheet of the same two clips"},
 {"id":"progress-swing","x":"$X/swing_r26.mp4","y":"$X/swing_r25.mp4","note":"two versions of our game: the same swing chain from the same start -- web line, swing, hero"},
 {"id":"progress-swing-sheet","x":"$S/swing_r26.jpg","y":"$S/swing_r25.jpg","note":"contact sheet of the same two clips"},
 {"id":"progress-flips","x":"$X/f4_r26.mp4","y":"$X/f4_r25.mp4","note":"two versions of our game: the same swing chain with a flip on every release -- flips, catches, hero"},
 {"id":"progress-flips-sheet","x":"$S/f4_r26.jpg","y":"$S/f4_r25.jpg","note":"contact sheet of the same two clips (15 frames)"}
]
JSON
rm -rf $C/pack
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py $C/pack $C/pairs.json
for d in $C/pack/*/; do for f in $d*.jpg; do [ -f "$f" ] || continue; sips -g pixelWidth "$f" | tail -1 | sed "s#^#$(basename $d)/$(basename $f) #"; done; done
du -sh $C/pack
