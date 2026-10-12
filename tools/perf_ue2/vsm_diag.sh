#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: VSM cache diagnostic on the Manhattan route (NOT a perf number; 1920x1080 output, capture slot):
# VSM stats readback (r.Shadow.Virtual.Stats 2 -> CSV columns, AccumulateStats -> Saved/ dump) + on-screen ShowStats stills at t 20/30/40,
# one run with the cache on and one with dynamic-page invalidation skipped (DebugSkipDynamicPageInvalidation) for comparison.
#   gpu_slot.sh capture --label perf -- tools/perf_ue2/vsm_diag.sh <out_dir>
set -uo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"; OUT="$1"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
ROUTE="$WT/docs/night1/manhattan/scripts/route_30s_warmup15.json"
CSV_DIR="$WT/unreal/WebHomage/Saved/Profiling/CSV"
for V in cache1 skipdyn; do
  EX="r.ScreenPercentage 100,r.Shadow.Virtual.Stats 2,r.Shadow.Virtual.ShowStats 1,r.Shadow.Virtual.AccumulateStats 1"
  [ "$V" = skipdyn ] && EX="$EX,r.Shadow.Virtual.Cache.DebugSkipDynamicPageInvalidation 1"
  T0=$(date +%s)
  "$WT/unreal/WebHomage/Scripts/run_game.sh" "$OUT/$V" -map /Game/Maps/Manhattan -res 1920x1080 -shots 20,30,40 -perf 15:45 -name $V -timeout 900 \
    -exec "$EX" -- -benchmark -fps=60 -csvGpuStats -WHTravScript="$ROUTE" | tail -2
  C=$(ls -t "$CSV_DIR"/Profile*.csv 2>/dev/null | head -1); [ -n "$C" ] && [ $(stat -f %m "$C") -ge $T0 ] && mv "$C" "$OUT/$V/csv.csv"
  find "$WT/unreal/WebHomage/Saved" -newermt "@$T0" -type f \( -iname '*vsm*' -o -iname '*virtualshadow*' -o -iname '*shadowstat*' \) -exec cp {} "$OUT/$V/" \; 2>/dev/null
done
ls -R "$OUT" | head -40
