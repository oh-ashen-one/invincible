#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 perf bisect: S1 view, one GPU-locked exclusive run (gpu_slot.sh perf) per variant, 30 s window.
#   docs/night1/life/perf_variants.sh <round dir> <WxH> <name>:<extra game args> [...]      e.g.  ... 3840x2160 off:-WHLifeOff on:     (env SPV = r.ScreenPercentage, default 67 = TSR 67 %)
set -uo pipefail
ROUND="$(mkdir -p "$1" && cd "$1" && pwd)"; RES="$2"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"; UE_DIR="$(cd "$HERE/../../../unreal/WebHomage" && pwd)"
G=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh; TMP=/Users/midir/sm2-n1/_scratch/life/capture
TAG=$([ "$RES" = 1920x1080 ] && echo 1080p || echo 4k)
for V in "$@"; do
  NAME="${V%%:*}"; ARGS="${V#*:}"
  rm -rf "$TMP/pv_${TAG}_$NAME"
  echo "== variant $NAME ($ARGS) $RES"
  $G perf --label life --json "$ROUND/perf_gpu_${TAG}_$NAME.json" -- "$UE_DIR/Scripts/run_game.sh" "$TMP/pv_${TAG}_$NAME" -map /Game/Tests/Life/Life_View_S1 -res $RES \
    -perf 22:52 -name perf -timeout 2400 -exec "r.ScreenPercentage ${SPV:-67}" -- -WHLifeStats=10 $ARGS | grep -E "WH_PERF frames"
  cp "$TMP/pv_${TAG}_$NAME/perf_perf.json" "$ROUND/perf_${TAG}_$NAME.json" 2>/dev/null
  $G summary "$ROUND/perf_gpu_${TAG}_$NAME.json" 2>/dev/null | head -1
done
