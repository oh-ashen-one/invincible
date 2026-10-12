#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: 3840x2160 stills for ONE config given in perf_route.py's spec syntax  name@SP[+set:<stem>][+cvar=value][+flag:-Flag][+variant:Cl15]
# (variant = the local map copies of make_variants.py under /Game/PerfF/<tag>/). Views default "S1 S2"; S7 = F's /Game/PerfF/View_S7; "route" = the two
# route stills (game t = 20 s / 28 s, -benchmark fixed step, 4K). Every view is a separate game launch (one Unreal process at a time).
#   gpu_slot.sh capture --label perf -- tools/perf_ue2/stills2.sh <out_dir> "<spec>" ["S1 S2 route"]
# env SM2_PERF_STILL_TWICE=1: launch each view twice and keep the second (first launch builds mesh distance fields / shaders into the DDC).
set -uo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$1"; SPEC="$2"; VIEWS="${3:-S1 S2}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
TMP=/Users/midir/sm2-n1/_scratch/perf/stills_tmp/$(basename "$OUT"); case "$TMP" in /Users/midir/sm2-n1/_scratch/perf/*) ;; *) exit 1;; esac
rm -rf "$TMP"; mkdir -p "$TMP"
eval "$(python3 - "$SPEC" "$WT" <<'PY'
import sys, shlex; sys.path.insert(0, sys.argv[2] + '/tools/perf_ue2'); import perf_route as p
name, sp, cv = p.parse_cfg(sys.argv[1])
flags = [k[5:] for k, v in cv if k.startswith('flag:')]; var = [k[8:] for k, v in cv if k.startswith('variant:')]
cvs = [(k, v) for k, v in cv if not k.startswith(('flag:', 'map:', 'variant:'))]
ex = ','.join(([] if sp == 'ini' else ['r.ScreenPercentage %s' % sp]) + ['%s %s' % kv for kv in cvs])
print('NAME=%s; SP=%s; EX=%s; DP=%s; VAR=%s; FLAGS=(%s)' % (shlex.quote(name), sp, shlex.quote(ex), shlex.quote(','.join('%s=%s' % kv for kv in cvs)), shlex.quote(var[-1] if var else ''), ' '.join(shlex.quote(f) for f in flags)))
PY
)"
DPA=(); [ -n "$DP" ] && DPA=(-dpcvars="$DP")
echo "{\"spec\": \"$SPEC\", \"sp\": \"$SP\", \"cvars\": \"$DP\", \"variant\": \"$VAR\"}" > "$OUT/settings.json"
PFX=/Game/Maps; VP=/Game/PerfF; [ -n "$VAR" ] && { PFX=/Game/PerfF/$VAR; VP=/Game/PerfF/$VAR; }
REPS=1; [ "${SM2_PERF_STILL_TWICE:-0}" = 1 ] && REPS=2
for V in $VIEWS; do
  if [ "$V" = route ]; then
    for R in $(seq 1 $REPS); do
      rm -rf "$TMP/route"
      "$WT/unreal/WebHomage/Scripts/run_game.sh" "$TMP/route" -map $PFX/Manhattan -res 3840x2160 -shots ${SM2_PERF_ROUTE_SHOTS:-20,28} -name route -timeout 1500 \
        -exec "$EX" -- -notraceserver -benchmark -fps=60 -WHTravScript="$WT/docs/night1/manhattan/scripts/route_30s_warmup15.json" "${DPA[@]+"${DPA[@]}"}" "${FLAGS[@]+"${FLAGS[@]}"}" | tail -1
    done
    I=0; for T in $(echo "${SM2_PERF_ROUTE_SHOTS:-20,28}" | tr ',' ' '); do p=$(ls "$TMP/route/route_0${I}_"*.png 2>/dev/null | head -1); [ -n "$p" ] && cp "$p" "$OUT/route_t$T.png"; I=$((I+1)); done
    continue
  fi
  M=$PFX/Manhattan_View_$V; [ "$V" = S7 ] && M=$VP/View_S7
  for R in $(seq 1 $REPS); do
    rm -rf "$TMP/$V"
    "$WT/unreal/WebHomage/Scripts/run_game.sh" "$TMP/$V" -map $M -res 3840x2160 -shots ${SM2_PERF_SHOT_T:-14} -name view_$V -timeout 900 \
      -exec "$EX" -- -notraceserver "${DPA[@]+"${DPA[@]}"}" "${FLAGS[@]+"${FLAGS[@]}"}" | tail -1
  done
  p=$(ls "$TMP/$V/view_${V}_00_"*.png 2>/dev/null | head -1); [ -n "$p" ] && cp "$p" "$OUT/view_$V.png"
done
ls "$OUT"
