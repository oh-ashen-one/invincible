#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# r04 numbers for one round dir (CPU only): tools/terrain/measure_r04.sh docs/night1/terrain/round-04
# (a) E1 sigma-6 high-pass SD + (b) mean HSV saturation on the critic's lawn crops and the like-for-like guard boxes, with the reference frames measured by the same tool beside them
# (c) flat quads > 100 px in t4_lawn_sprint at 4 fps  (t5) sigma-3 SD of the park ground in the last 5 s of t5_avenue_to_park  (d) the r03 canopy checks via measure_round.sh
set -uo pipefail
R="$(cd "$1" && pwd)"; REPO="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$REPO"; REF=/Users/midir/spiderman-learnings/refs/streets
S=$R/stills
cp /Users/midir/sm2-n1/_scratch/terrain/prep/lawn_stats.json "$R/lawn_prep_stats.json" 2>/dev/null && echo "grass scatter stats -> $R/lawn_prep_stats.json"
python3 tools/terrain/lawn_stats.py "$R/lawn_stats.json" "$S/p4_greatlawn.jpg:1700,1000,512,400:critic p4_greatlawn" "$S/p10_lawn_eye.jpg:1300,1700,512,460:critic p10_lawn_eye" \
  "$S/p10_lawn_eye.jpg:2240,1856,512,512:guard p10" "$S/p4_greatlawn.jpg:3520,1856,512,512:guard p4" "$S/p9_park_panorama.jpg:512,1856,512,512:guard p9" | tee "$R/lawn_stats.txt"
# references, same tool: native 1920x1080 and put on the 4K output grid (x2); lawn windows picked by eye on the frames (no character, no sky)
python3 tools/terrain/lawn_stats.py "$R/ref_lawn_native.json" "$REF/centralpark-meadow-skyline__cp_0605.jpg:100,660,512,400:meadow-skyline lawn L" "$REF/centralpark-meadow-skyline__cp_0605.jpg:1100,680,512,380:meadow-skyline lawn R" \
  "$REF/centralpark-aerial-ballfields__cp_0554.jpg:450,560,400,300:aerial-ballfields lawn" "$REF/centralpark-aerial-ballfields__cp_0554.jpg:60,880,400,200:aerial-ballfields lawn 2" | tee "$R/ref_lawn_native.txt"
python3 tools/terrain/lawn_stats.py "$R/ref_lawn_x2.json" --scale 2 "$REF/centralpark-meadow-skyline__cp_0605.jpg:200,1320,512,400:meadow-skyline lawn L" "$REF/centralpark-meadow-skyline__cp_0605.jpg:2200,1360,512,460:meadow-skyline lawn R" \
  "$REF/centralpark-meadow-skyline__cp_0605.jpg:200,1700,512,400:meadow-skyline lawn low" "$REF/centralpark-aerial-ballfields__cp_0554.jpg:900,1120,512,400:aerial-ballfields lawn" "$REF/centralpark-aerial-ballfields__cp_0554.jpg:120,1760,512,400:aerial-ballfields lawn 2" | tee "$R/ref_lawn_x2.txt"
[ -f "$R/t4_lawn_sprint.mp4" ] && python3 tools/terrain/flatquad_check.py "$R/t4_lawn_sprint.mp4" "$R/flatquad_t4.json" | tee "$R/flatquad_t4.txt"
[ -f "$R/t5_avenue_to_park.mp4" ] && python3 tools/terrain/t5_ground_sd.py "$R/t5_avenue_to_park.mp4" "$R/t5_avenue_to_park_telemetry.csv" "$R/t5_ground_sd.json" | tee "$R/t5_ground_sd.txt"
[ -f "$R/t5_avenue_to_park_telemetry.csv" ] && python3 tools/terrain/t5_score.py "$R" "$R/t5_score.json" 2>/dev/null | grep t5_avenue > "$R/t5_score.txt"
tools/terrain/measure_round.sh "$R"
