#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r04, ONE GPU-lock hold (run as: gpu_slot.sh capture --label island -- docs/night1/island/hold_r04a.sh), one engine at a time:
#   1. merge-only baselines: telemetry sims of r1 r4 r5 r2 on the round-03 map + merged C++ (tiles -2_2 / -1_2 / 0_2 kit patched; r1 / r4 / r5
#      never enter them, r2 does from t = 9.58 s)
#   2. fepatch of the r3 tiles with the current export kit (SM2_ISLAND_FE_TILES), then the r3 sim -> $FE_OUT
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; WT="$(cd "$HERE/../../.." && pwd)"
S=/Users/midir/sm2-n1/_scratch/island/r04
export ISLAND_IN_LOCK=1
name() { case "$1" in r1) echo r1_north_avenue;; r2) echo r2_south_avenue;; r3) echo r3_crosstown_east;; r4) echo r4_wallrun_roofs;; r5) echo r5_m2_avenue;; esac; }
mine() { pgrep -f "$WT/unreal/WebHomage/WebHomage.uproject" >/dev/null; }
for r in ${MERGE_SIMS:-}; do
  while mine; do sleep 5; done
  echo "== merge-only sim $r $(date +%T)"; "$HERE/sim_route.sh" "$S/sim_merge" "$HERE/scripts/$(name $r).json" 2>&1 | tail -2
done
if [ -n "${FE_OUT:-}" ]; then
  while mine; do sleep 5; done
  [ -n "${KIT_LOG:-}" ] && while ! grep -q "^real" "$KIT_LOG"; do sleep 5; done   # the export kit regenerated first
  echo "== fepatch ${SM2_ISLAND_FE_TILES:-} $(date +%T)"
  ( cd "$WT" && SM2_ISLAND_GPU_SLOT=0 python3 unreal/WebHomage/Scripts/build_manhattan.py --steps fepatch 2>&1 | grep -E "removed|commandlet|done|failed|error" )
  while mine; do sleep 5; done
  echo "== r3 sim -> $FE_OUT $(date +%T)"; "$HERE/sim_route.sh" "$FE_OUT" "$HERE/scripts/r3_crosstown_east.json" 2>&1 | tail -2
fi
for j in ${EXTRA_SIMS:-}; do   # extra route scripts (file names under scripts/) -> $S/sim_extra
  while mine; do sleep 5; done
  echo "== extra sim $j $(date +%T)"; "$HERE/sim_route.sh" "$S/sim_extra" "$HERE/scripts/$j" 2>&1 | tail -2
done
echo "hold done $(date +%T)"
