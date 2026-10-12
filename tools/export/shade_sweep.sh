#!/bin/zsh
# (r09) ShadeFill / GlassSky sweep inside ONE gpu_slot hold: [optional material rebuild] then, per "fill:glass" pair, set the MPC defaults (headless commandlet) and capture S1 / S3 / S7 at 1080p,
# then run shade_check.py on each set. Strictly sequential: one Unreal process at a time.
# usage: gpu_slot.sh capture --label city -- zsh tools/export/shade_sweep.sh <out_dir> <build:0|1> <fill:glass> [<fill:glass> ...]
set -u
OUT=$1; BUILD=$2; shift 2
HERE=${0:A:h}; WT=${HERE:h:h}
mkdir -p "$OUT"
waitengine() { while pgrep -f "MacOS/UnrealEditor .*${WT}/unreal" >/dev/null; do sleep 3; done; }
if [ "$BUILD" = 1 ]; then
  $HERE/ue/run_commandlet.sh $WT/unreal/WebHomage/Scripts/build_city.py steps=mat > $OUT/build_mat.txt 2>&1
  RC=$?; echo "build mat rc=$RC"; [ $RC -ne 0 ] && { echo "BUILD FAILED"; exit 5; }
  waitengine
fi
for pair in "$@"; do
  F=${pair%%:*}; G=${pair##*:}; TAG=f${F}_g${G}
  $HERE/ue/run_commandlet.sh $WT/tools/export/ue/set_mpc.py ShadeFill=$F GlassSky=$G > $OUT/set_$TAG.txt 2>&1
  RC=$?; echo "set_mpc $TAG rc=$RC"; [ $RC -ne 0 ] && { echo "SET_MPC FAILED"; exit 5; }
  waitengine
  for id in S1_avenue_street S3_rooftop_watertower S7_sunset_crosstown; do
    $HERE/capture_one.sh $OUT/$TAG $id 1920x1080 > $OUT/cap_${TAG}_${id}.txt 2>&1
    echo "capture $TAG $id rc=$?"
    waitengine
  done
  python3 $HERE/shade_check.py $OUT/$TAG --json $OUT/$TAG/check.json > $OUT/$TAG/check.txt 2>&1
  head -8 $OUT/$TAG/check.txt
done
echo SWEEP_DONE
