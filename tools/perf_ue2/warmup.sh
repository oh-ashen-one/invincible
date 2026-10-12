#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: shader / DDC / PSO warm-up of the Manhattan route at 960x540 (NOT measured) for each cvar set given, so that
# perf runs do not compile shaders inside the measured window. Run it under a CAPTURE slot:
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label perf -- tools/perf_ue2/warmup.sh "" "r.Lumen.HardwareRayTracing=0" ...
set -uo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT=/Users/midir/sm2-n1/_scratch/perf/warmup
ROUTE="$WT/docs/night1/manhattan/scripts/route_30s_warmup15.json"
i=0
for CV in "$@"; do
  D="$OUT/w$i"; rm -rf "$D"; mkdir -p "$D"
  EX="r.ScreenPercentage 67${WARM_PRINT:+,$WARM_PRINT}"; DP=()   # WARM_PRINT="r.A,r.B": bare cvar names = print their values to the log
  if [ -n "$CV" ]; then EX="$EX,$(echo "$CV" | tr '=' ' ')"; DP=(-dpcvars="$CV"); fi
  echo "warmup $i: ${CV:-<base>}"
  "$WT/unreal/WebHomage/Scripts/run_game.sh" "$D" -map /Game/Maps/Manhattan -res 960x540 -quit 46 -name warm -timeout 1500 -exec "$EX" \
    -- -notraceserver -benchmark -fps=60 -WHTravScript="$ROUTE" "${DP[@]+"${DP[@]}"}" | tail -1
  i=$((i + 1))
done
