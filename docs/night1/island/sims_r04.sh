#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r04: telemetry-only route sims (sim_route.sh: -nullrhi, fixed 1/60 s step, each its own GPU-lock hold), one engine at a time.
# usage: docs/night1/island/sims_r04.sh <out_dir> r1 r3 ...   (routes: r1 r2 r3 r4 r5)
set -uo pipefail
OUT="$1"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
name() { case "$1" in r1) echo r1_north_avenue;; r2) echo r2_south_avenue;; r3) echo r3_crosstown_east;; r4) echo r4_wallrun_roofs;; r5) echo r5_m2_avenue;; esac; }
for r in "$@"; do
  while pgrep -f "sm2-n1/island/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 15; done   # never two engines of mine
  echo "== sim $r $(date +%T)"
  "$HERE/sim_route.sh" "$OUT" "$HERE/scripts/$(name $r).json" 2>&1 | grep -v "wait phase" | tail -4
done
echo "sims done $(date +%T)"
