#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round-07 measurements on a capture directory (pixels + telemetry), written to <evidence_dir>.   tools/ue_char/analyze_r7.sh <captures_dir> <evidence_dir> [<round06_captures_dir>]
#   telemetry_check.py  3D separation of every walker pair per rendered frame (engine telemetry)
#   key_check_r7.py     stencil-keyed stills: green inside citizens, enclosed key components (+ 3x montages), detached polygons;   spike_key.py: silhouette spikes
#   id_overlap.py       per-walker silhouettes of the id movie (only if <captures>/segD_frames exists)
#   analyze_r5.sh       YOLO counts / video checks (CPU: YOLO_DEVICE=cpu)
set -u
WT="$(cd "$(dirname "$0")/../.." && pwd)"
CAP=${1:?captures}; EV=${2:?evidence}; R6=${3:-}
mkdir -p "$EV/telemetry" "$EV/keycheck"
for c in "$CAP"/telemetry/*_walkers.csv "$CAP"/crowd_walkers.csv; do
  [ -f "$c" ] && python3 "$WT/tools/ue_char/crowd/telemetry_check.py" "$c" --out "$EV/telemetry" >/dev/null
done
KEYS=$(ls "$CAP"/crowd_key_*_4k.png 2>/dev/null)
if [ -n "$KEYS" ]; then
  python3 "$WT/tools/ue_char/eval/key_check_r7.py" $KEYS --out "$EV/keycheck" --tol 8 > "$EV/keycheck/summary.jsonl"
  python3 "$WT/tools/ue_char/eval/spike_key.py" $KEYS > "$EV/keycheck/spikes.jsonl" 2>&1
  for k in $KEYS; do b=$(basename "${k%.png}"); python3 "$WT/tools/ue_char/eval/key_components_r7.py" "$k" "$EV/keycheck/${b}_check.json" "$EV/keycheck/${b}_components.jpg" --min-px 50 --pad 40; done
fi
[ -d "$CAP/segD_frames" ] && python3 "$WT/tools/ue_char/crowd/id_overlap.py" "$CAP/segD_frames" "$EV/id_overlap_crowd_tracking.json" | tee "$EV/id_overlap_summary.json"
YOLO_DEVICE=cpu OMP_NUM_THREADS=4 "$WT/tools/ue_char/analyze_r5.sh" "$CAP" "$EV" > "$EV/analyze_r5.log" 2>&1 || true
echo "analyze_r7 done -> $EV"
