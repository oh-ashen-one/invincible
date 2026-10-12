#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: 3840x2160 stills of the P1 shot cameras S1 / S2 (C's /Game/Maps/Manhattan_View_<S#>) + S7 (F's local /Game/PerfF/View_S7,
# tools/perf_ue2/make_views.py), all golden, and two route stills
# (mid-swing, t = 20 s and 28 s of the warm-up route = 5 s / 13 s into the swing), for one config = SP + cvar set.
# Run under a CAPTURE slot:  gpu_slot.sh capture --label perf -- tools/perf_ue2/stills.sh <out_dir> <SP> ["cvar=v,cvar=v" | set:<stem>]
set -uo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$1"; SP="$2"; CV="${3:-}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
TMP=/Users/midir/sm2-n1/_scratch/perf/stills_tmp/$(basename "$OUT"); rm -rf "$TMP"; mkdir -p "$TMP"
if [[ "$CV" == set:* ]]; then CV=$(python3 -c "import sys; sys.path.insert(0,'$WT/tools/perf_ue2'); import perf_route as p; print(','.join('%s=%s'%kv for kv in p.read_set('${CV#set:}')))"); fi
EX="r.ScreenPercentage $SP"; DP=()
if [ -n "$CV" ]; then EX="$EX,$(echo "$CV" | tr '=' ' ')"; DP=(-dpcvars="$CV"); fi
echo "{\"sp\": $SP, \"cvars\": \"$CV\"}" > "$OUT/settings.json"
for V in ${SM2_PERF_STILL_VIEWS:-S1 S2 S7}; do
  M=/Game/Maps/Manhattan_View_$V; [ "$V" = S7 ] && M=/Game/PerfF/View_S7
  "$WT/unreal/WebHomage/Scripts/run_game.sh" "$TMP/$V" -map $M -res 3840x2160 -shots 14 -name view_$V -timeout 900 \
    -exec "$EX" -- "${DP[@]+"${DP[@]}"}" | tail -1
  p=$(ls "$TMP/$V/view_${V}_00_"*.png 2>/dev/null | head -1); [ -n "$p" ] && cp "$p" "$OUT/view_$V.png"
done
"$WT/unreal/WebHomage/Scripts/run_game.sh" "$TMP/route" -map /Game/Maps/Manhattan -res 3840x2160 -shots 20,28 -name route -timeout 1500 \
  -exec "$EX" -- -benchmark -fps=60 -WHTravScript="$WT/docs/night1/manhattan/scripts/route_30s_warmup15.json" "${DP[@]+"${DP[@]}"}" | tail -1
I=0; for T in 20 28; do p=$(ls "$TMP/route/route_0${I}_"*.png 2>/dev/null | head -1); [ -n "$p" ] && cp "$p" "$OUT/route_t$T.png"; I=$((I+1)); done
ls "$OUT"
