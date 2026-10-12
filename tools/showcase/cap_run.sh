#!/bin/bash
# matched-camera capture + pair stats. usage: cap_run.sh <run-name> [play.py --exec args...]   (needs SM2_COEXIST_HOLDER; no rebuild)
set -e
cd "$(dirname "$0")/../.."
source tools/m5/env.sh
R=$HOME/sm2-n1/_scratch/showcase/runs
CAMS=${CAMS:-$HOME/sm2-n1/_scratch/night/ref/shot_cams.json}
N=$1; shift
tools/showcase/with_holder.sh python3 tools/showcase/play.py --map showcase-night --profile fidelity --capture $R/$N --shot-cams $CAMS --name night "$@" --launch > $R/$N.out 2>&1
python3 tools/showcase/pairs.py $R/$N --name night
