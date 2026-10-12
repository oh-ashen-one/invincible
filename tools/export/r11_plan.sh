#!/bin/zsh
# (r11) Run a PLAN FILE inside ONE gpu_slot hold: strictly sequential, one Unreal process at a time, refuses to launch while an UnrealEditor is stuck exiting.
#   usage: gpu_slot.sh capture --label city -- zsh tools/export/r11_plan.sh <out_dir> <plan_file>
# plan lines (blank lines and # comments ignored):
#   build <steps>                      build_city.py steps=<steps>  (headless -nullrhi commandlet)
#   mpc <tag> KEY=V [KEY=V ...]        set MPC_City defaults (saved in the asset; the next captures use them)
#   variants k=v [k=v ...]             tools/export/ue/view_variants.py (scratch atmosphere / exposure copies of a view map, e.g. names=a,b fog_a=0.001 fogc_a=0.6,0.62,0.65)
#   cap <dir_tag> <map id> [WxH] [sp]  single frame pair at t = 34 and 38 s (settle pair; the first rendered frame of a cold start can arrive at t = 27 s, see HANDOFF gotcha 36) into <out_dir>/<dir_tag>/; sp=100 passes -exec "r.ScreenPercentage 100" (native internal resolution)
#   score <dir_tag> <map id>           s4_score.py on the t=28 frame of that map (S4 and its variants), appended to <out_dir>/scores.txt
# The plan stops at the first failing step (exit 5/6/7).
set -u
OUT=$1; PLAN=$2
HERE=${0:A:h}; WT=${HERE:h:h}
mkdir -p "$OUT"
T0=$SECONDS; NV=0
sick() { ps -axo stat=,comm= | awk '$1 ~ /[ZE]/ && $2 ~ /UnrealEditor/ && $2 !~ /Services/ {f=1} END {exit !f}'; }
waitengine() { while pgrep -f "MacOS/UnrealEditor .*${WT}/unreal" >/dev/null; do sleep 3; done; }
sick && { echo "ABORT: an UnrealEditor is stuck exiting"; exit 6; }
while IFS= read -r line; do
  [[ -z "${line// }" || "$line" == \#* ]] && continue
  words=(${=line}); cmd=$words[1]; args=(${words[2,-1]})
  case $cmd in
    build)
      $HERE/ue/run_commandlet.sh $WT/unreal/WebHomage/Scripts/build_city.py steps=$args[1] > $OUT/build_$args[1].txt 2>&1
      RC=$?; echo "build $args[1] rc=$RC t=$((SECONDS-T0))"; [ $RC -ne 0 ] && { echo "BUILD FAILED"; exit 5; }; waitengine;;
    mpc)
      tag=$args[1]; kv=(${args[2,-1]})
      $HERE/ue/run_commandlet.sh $WT/tools/export/ue/set_mpc.py $kv > $OUT/set_$tag.txt 2>&1
      RC=$?; echo "mpc $tag $kv rc=$RC t=$((SECONDS-T0))"; [ $RC -ne 0 ] && { echo "SET_MPC FAILED"; exit 5; }; waitengine;;
    variants)
      $HERE/ue/run_commandlet.sh $WT/tools/export/ue/view_variants.py $args > $OUT/variants_$((++NV)).txt 2>&1
      RC=$?; echo "variants $args rc=$RC t=$((SECONDS-T0))"; [ $RC -ne 0 ] && { echo "VARIANTS FAILED"; exit 5; }; waitengine;;
    cap)
      tag=$args[1]; id=$args[2]; res=${args[3]:-1920x1080}; sp=${args[4]:-}
      sick && { echo "ABORT: engine stuck exiting before $tag $id"; exit 7; }
      mkdir -p $OUT/$tag
      $HERE/ue/wait_slot.sh
      extra=(); [ "$sp" = 100 ] && extra=(-exec "r.ScreenPercentage 100")
      GPU=$(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1 | grep -o '[0-9]*$')
      echo "{\"id\":\"${id}\",\"res\":\"${res}\",\"sp\":\"${sp:-auto}\",\"gpu_util_before_pct\":${GPU:-null}}" > $OUT/$tag/${id}_${res}_gpu.json
      ( sleep 720; echo "r11_plan: watchdog stop of $tag $id"; /Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "[/]Users/midir/sm2-n1/city/unreal/WebHomage" ) &
      WD=$!
      ( cd $WT/unreal/WebHomage && ${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh} capture --label city -- Scripts/run_game.sh $OUT/$tag -map /Game/Tests/City/City_View_$id -res $res -shots 34,38 -perf 26:38 -quit 40 -name ${id}_${res} -timeout 7200 $extra > $OUT/$tag/cap_$id.txt 2>&1 )
      RC=$?; kill $WD 2>/dev/null; wait $WD 2>/dev/null
      echo "cap $tag $id $res sp=$sp rc=$RC t=$((SECONDS-T0))"; waitengine; sleep 5
      sick && { echo "ABORT: an UnrealEditor is stuck exiting after $tag $id"; exit 7; };;
    score)
      f=$(ls $OUT/$args[1]/${args[2]}_1920x1080_01_t*.png 2>/dev/null | head -1)
      echo "$args[1] $args[2] $(python3 $HERE/s4_score.py $f 2>/dev/null)" | tee -a $OUT/scores.txt;;
    *) echo "unknown plan command: $line";;
  esac
done < "$PLAN"
echo PLAN_DONE t=$((SECONDS-T0))
