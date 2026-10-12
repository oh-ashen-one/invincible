#!/bin/zsh
# (r10) MPC / atmosphere sweep inside ONE gpu_slot hold: for each "tag:KEY=V,KEY=V" set the MPC defaults (headless commandlet), then capture the listed views at 1080p.
# Strictly sequential, one Unreal process at a time; refuses to start while an UnrealEditor is stuck exiting.
# usage: gpu_slot.sh capture --label city -- zsh tools/export/mpc_sweep.sh <out_dir> "<view ids space separated>" tag:KEY=V,KEY=V [tag2:...]
#   (a variant map id such as S4ve10 is a view id too; the MPC is global, the map atmosphere is per map)
set -u
OUT=$1; VIEWS=(${=2}); shift 2
HERE=${0:A:h}; WT=${HERE:h:h}
mkdir -p "$OUT"
sick() { ps -axo stat=,comm= | awk '$1 ~ /[ZE]/ && $2 ~ /UnrealEditor/ && $2 !~ /Services/ {f=1} END {exit !f}'; }
waitengine() { while pgrep -f "MacOS/UnrealEditor .*${WT}/unreal" >/dev/null; do sleep 3; done; }
sick && { echo "ABORT: an UnrealEditor is stuck exiting"; exit 6; }
for spec in "$@"; do
  TAG=${spec%%:*}; KV=${spec#*:}; ARGS=(${(s:,:)KV})
  $HERE/ue/run_commandlet.sh $HERE/ue/set_mpc.py $ARGS > $OUT/set_$TAG.txt 2>&1
  RC=$?; echo "set_mpc $TAG ($KV) rc=$RC"; [ $RC -ne 0 ] && { echo "SET_MPC FAILED"; exit 5; }
  waitengine
  for id in $VIEWS; do
    sick && { echo "ABORT: engine stuck exiting before $TAG $id"; exit 7; }
    $HERE/capture_one.sh $OUT/$TAG $id 1920x1080 > $OUT/cap_${TAG}_${id}.txt 2>&1
    echo "capture $TAG $id rc=$?"
    waitengine; sleep 5
  done
done
echo SWEEP_DONE
