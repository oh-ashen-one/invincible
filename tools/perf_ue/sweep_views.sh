#!/bin/zsh
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Perf of every city view (static shot cameras) under one preset at 3840x2160, TSR 50 %: finds the heaviest view.
# usage: tools/perf_ue/sweep_views.sh <out dir> [preset] [passes]   (passes = how many times the whole sweep is repeated; the minimum per view is kept by the reader)
OUT=$1; P=${2:-midday}; N=${3:-1}
cd "$(dirname "$0")/../.."
for k in $(seq 1 $N); do
  for S in S1 S2 S3 S4 S5 S6 S7 S8; do
    python3 tools/perf_ue/run_perf.py --out $OUT/pass$k/$S --map /Game/Tests/Look/Look_View_${P}_$S --script none --configs tsr50 --window 14:24 | grep -E "^tsr50"
  done
done
