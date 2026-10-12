#!/bin/bash
# usage: route_run.sh <run name> <showcase|showcase-night> <fidelity|playable> [extra play.py args]
# the warm-up route (15 s standing + the 30 s route), shots every 3 s over the route, perf window 15:45, t.MaxFPS 0, no vsync, wh.CityLights.Debug 1 (log only).
set -e
cd "$(dirname "$0")/../.."
source tools/m5/env.sh
R=$HOME/sm2-n1/_scratch/showcase/runs
N=$1; MAP=$2; PROF=$3; shift 3
mkdir -p $R/$N
echo "holders at launch: $(ls ~/.cache/gpu-slot/holders | tr '\n' ' ')" > $R/$N.holders.txt
tools/showcase/with_holder.sh python3 tools/showcase/play.py --map $MAP --profile $PROF --capture $R/$N --name route --script docs/night1/manhattan/scripts/route_30s_warmup15.json \
  --shots 18,21,24,27,30,33,36,39,42,45 --perf 15:45 --quit 47 --exec "wh.CityLights.Debug 1" "$@" --launch > $R/$N.out 2>&1
echo "holders after: $(ls ~/.cache/gpu-slot/holders | tr '\n' ' ')" >> $R/$N.holders.txt
python3 tools/showcase/perf_report.py $R/$N --holder "$(grep -o '[0-9]*\.json' $R/$N.holders.txt | head -1 | tr -d '.json')" > /dev/null
