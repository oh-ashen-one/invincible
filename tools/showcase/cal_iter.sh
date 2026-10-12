#!/bin/bash
# one calibration iteration: rebuild the look rigs (one commandlet), then one matched-camera capture, then the pair stats. usage: cal_iter.sh <run-name>
set -e
cd "$(dirname "$0")/../.."
source tools/m5/env.sh
R=$HOME/sm2-n1/_scratch/showcase/runs
SM2_GPU_WAIT_TIMEOUT=3600 python3 unreal/WebHomage/Scripts/build_manhattan.py --steps look > $SM2_MANHATTAN_SCR/logs/cal_$1.out 2>&1
SM2_COEXIST_HOLDER=${SM2_COEXIST_HOLDER:?} python3 tools/showcase/play.py --map showcase-night --profile fidelity --capture $R/$1 --shot-cams $HOME/sm2-n1/_scratch/night/ref/shot_cams.json --name night --launch > $R/$1.out 2>&1
python3 tools/showcase/pairs.py $R/$1 --name night
