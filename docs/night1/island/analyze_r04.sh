#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r04: every committed checker on the round-04 captures (CPU only, no engine). Writes round-04/*.json.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; WT="$(cd "$HERE/../../.." && pwd)"; T="$WT/tools/export"
R="$HERE/round-04"; E=/Users/midir/sm2-n1/_scratch/island/export/island; S=/Users/midir/sm2-n1/_scratch/island/r04
cd "$WT"
for n in r1_north_avenue r2_south_avenue r3_crosstown_east r4_wallrun_roofs r5_m2_avenue r5_m2_avenue_alt0; do
  c="$R/${n}_telemetry.csv"; [ -f "$c" ] || { echo "missing $c"; continue; }
  python3 "$T/island_route_check.py" "$E" "$c" --out "$R/route_check_${n}.json" > /dev/null
  python3 "$T/island_rope_canopy.py" "$E" "$c" "$R/rope_canopy_${n}.json" | tail -1 | cut -c1-200
  [ -f "$R/$n.mp4" ] && python3 "$T/island_foliage_check.py" "$R/$n.mp4" "$R/foliage_${n}.json"
done
python3 "$T/island_fe_check.py" "$R/r3_crosstown_east_telemetry.csv" "$R/r3_fe_check.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print('r3 fire escape', d['pass'], d['stuck_spans_t'], d['topout_events'])"
for n in r5_m2_avenue r5_m2_avenue_alt0; do
  [ -f "$R/${n}_telemetry.csv" ] || continue
  python3 "$T/island_m2_check.py" "$E" "$R/${n}_telemetry.csv" --out "$R/${n}_check.json" --stills $(ls "$R"/stills/${n}_t*s_1920x1080.jpg 2>/dev/null) | tail -2
done
for n in r1_north_avenue r2_south_avenue r3_crosstown_east r4_wallrun_roofs r5_m2_avenue; do
  m="$S/sim_merge/$n/${n}_telemetry.csv"; [ "$n" = r3_crosstown_east ] && m="$S/sim_base/$n/${n}_telemetry.csv"
  [ -f "$m" ] && python3 "$T/island_traj_diff.py" "$m" "$R/${n}_telemetry.csv" "${n}: merge-only sim vs r04 capture"
  python3 "$T/island_traj_diff.py" "$HERE/round-03/${n}_telemetry.csv" "$R/${n}_telemetry.csv" "${n}: r03 capture vs r04 capture"
done > "$R/trajectory_diffs.jsonl"
IP_GATE_OUT="$R/ip_gate.json" python3 "$HERE/ip_gate_r04.py" "$R/stills" | tail -1
echo "analysis done"
