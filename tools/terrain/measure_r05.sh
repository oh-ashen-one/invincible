#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# r05 numbers for one round dir (CPU only): tools/terrain/measure_r05.sh docs/night1/terrain/round-05
#  (1)(2)(3) crown_stats.py on the 24 p1 crown crops (sigma-3 SD, saturation) + the p10 silhouette (E9c)   (4) shadow_ratio.py on <round>/shadow_boxes.json (p4 isolated trees)
#  (5) E1 reconciled: lawn_stats.py on the p10 critic crop + guard (sigma-6 >= 8, R / G 0.85-0.95) and the p4 critic crop (sigma-6 <= 5); the p4 / p9 guard boxes as information
#  E10 guards: (b) saturation of the lawn crops, (c) flat quads in t4, (d) t5 last 5 s ground sigma-3; shore audit / HLSL via measure_round.sh
set -uo pipefail
R="$(cd "$1" && pwd)"; REPO="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$REPO"
S=$R/stills
python3 tools/terrain/lawn_stats.py "$R/lawn_stats.json" "$S/p10_lawn_eye.jpg:1300,1700,512,460:critic p10_lawn_eye (eye level, >= 8, R/G 0.85-0.95)" "$S/p10_lawn_eye.jpg:2240,1856,512,512:guard p10 (eye level, >= 8)" \
  "$S/p4_greatlawn.jpg:1700,1000,512,400:critic p4_greatlawn (aerial, <= 5)" "$S/p4_greatlawn.jpg:3520,1856,512,512:guard p4 (aerial, info)" "$S/p9_park_panorama.jpg:512,1856,512,512:guard p9 (aerial, info)" | tee "$R/lawn_stats.txt"
python3 - "$R/lawn_stats.json" <<'PY' | tee -a "$R/lawn_stats.txt"
import json, sys
d = json.load(open(sys.argv[1]))['crops']
for c in d:
    r, g, b = c['mean_rgb']; c['r_over_g'] = round(r / max(g, 1e-3), 3)
    print('%-44s hp6 %5.2f  R/G %.3f  sat %.3f' % (c['label'], c['hp6_sd'], c['r_over_g'], c['mean_hsv_sat']))
ok = d[0]['hp6_sd'] >= 8 and d[1]['hp6_sd'] >= 8 and 0.85 <= d[0]['r_over_g'] <= 0.95 and d[2]['hp6_sd'] <= 5
print('E1 reconciled (r05 target 5):', 'PASS' if ok else 'FAIL')
json.dump({'crops': d, 'pass_e1_reconciled': ok}, open(sys.argv[1], 'w'), indent=1)
PY
[ -f "$R/crops.json" ] && python3 tools/terrain/crown_stats.py "$S" "$R/crops.json" "$R/crown_stats.json" --preview "$R/crowns_preview.png" --flat "$S/p1_south.jpg" "$S/p10_lawn_eye.jpg" --silhouette "$S/p10_lawn_eye.jpg" "$S/p1_south.jpg" | tee "$R/crown_stats.txt"
[ -f "$R/shadow_boxes.json" ] && python3 tools/terrain/shadow_ratio.py "$S" "$R/shadow_boxes.json" "$R/shadow_ratio.json" | tee "$R/shadow_ratio.txt"
[ -f "$R/t4_lawn_sprint.mp4" ] && python3 tools/terrain/flatquad_check.py "$R/t4_lawn_sprint.mp4" "$R/flatquad_t4.json" | tee "$R/flatquad_t4.txt"
[ -f "$R/t5_avenue_to_park.mp4" ] && python3 tools/terrain/t5_ground_sd.py "$R/t5_avenue_to_park.mp4" "$R/t5_avenue_to_park_telemetry.csv" "$R/t5_ground_sd.json" | tee "$R/t5_ground_sd.txt"
[ -f "$R/t5_avenue_to_park_telemetry.csv" ] && python3 tools/terrain/t5_score.py "$R" "$R/t5_score.json" 2>/dev/null | grep t5_avenue > "$R/t5_score.txt"
exit 0
