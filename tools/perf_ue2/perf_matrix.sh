#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: content-variant A/B driver. Cumulatively applies perf_apply.py steps to the LOCAL city content one step at a time and measures the
# route after each one in its own exclusive perf session (perf_queue.py). Never runs while another of MY game processes exists.
#   perf_matrix.sh <out_dir> "<config list>" step1 step2 ...
#   e.g. perf_matrix.sh _scratch/perf/r03 "base50@50" static far_rt far_plain kit_plain tree_rt tree_lumen
# Result of variant k (steps 1..k applied): <out>/v<k>_<step>/p*/<config>/result.json ; <out>/matrix.log
set -uo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$1"; CFGS="$2"; shift 2
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
k=0
for S in "$@"; do
  k=$((k+1)); D="$OUT/v${k}_${S}"; mkdir -p "$D"
  echo "$(date +%H:%M:%S) variant $k: apply $S" | tee -a "$OUT/matrix.log"
  "$WT/tools/perf_ue2/perf_content.sh" apply "$S" 2>&1 | tail -2 | tee -a "$OUT/matrix.log"
  cp /Users/midir/sm2-n1/_scratch/perf/apply.json "$D/apply.json" 2>/dev/null
  python3 "$WT/tools/perf_ue2/perf_queue.py" --out "$D" --configs "$CFGS" --tag p 2>&1 | grep -E "sp [0-9]+ +avg|rc |queue done|giving up|no progress" | tee -a "$OUT/matrix.log"
done
echo "$(date +%H:%M:%S) matrix done" | tee -a "$OUT/matrix.log"
