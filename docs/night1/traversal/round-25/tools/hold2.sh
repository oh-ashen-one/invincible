#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r25 hold (run INSIDE one `gpu_slot.sh capture --label traversal -- <this>`): content (M_TravWeb, -nullrhi commandlet) -> -nullrhi
# probes (c gate, pawn run, the other clips' path/camera vs round 24) -> a capture WORKER that pops clip names from $R/queue_$TAG.txt and sources
# $R/tune.env (EXTRA_ARGS) before each capture, so the queue / rope tuning can be edited live from outside. Time-guarded under the 2400 s max hold.
# usage: hold2.sh <tag> (queue: $R/queue_<tag>.txt; waits for an earlier hold of mine to end)      (state + logs in /Users/midir/sm2-n1/_scratch/traversal/r25)
TAG=${1:-h}
R=/Users/midir/sm2-n1/_scratch/traversal/r25
WT=/Users/midir/sm2-n1/traversal
UE=$WT/unreal/WebHomage
UEB="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
SC=$WT/docs/night1/traversal/scripts/city
TD=$WT/docs/night1/traversal
RD=$TD/round-25
OUT=$R/probe_$TAG
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
echo "== hold $TAG acquired $(date +%T)"
# a previous hold of mine still running (queued early): wait up to 600 s for it to end (never two engines of mine at once)
for i in $(seq 1 90); do ls $R/hold_*.running 2>/dev/null | grep -qv "hold_$TAG.running" || break; [ $i = 1 ] && echo "== waiting for my previous hold to end"; sleep 10; done
ls $R/hold_*.running 2>/dev/null | grep -qv "hold_$TAG.running" && { echo "== previous hold still running: exit"; rm -f $R/hold_$TAG.running; exit 0; }
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine still running: wait 60 s"; sleep 60; }
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine STILL running: exit"; rm -f $R/hold_$TAG.running; exit 0; }
echo $$ > $R/hold_$TAG.running   # (el() counts from the acquisition: the max-hold clock includes any wait above)
cd $WT
# 1. content: M_TravWeb (once)
if [ ! -f $R/WEBMAT_DONE ]; then
  echo "== content M_TravWeb at $(el) s"
  "$UEB" "$UE/WebHomage.uproject" -run=pythonscript -script="$UE/Scripts/build_traversal_web.py" -unattended -nullrhi -NoSound \
     -abslog="$R/webmat_$TAG.log" > /dev/null 2>&1
  echo "   rc $? at $(el) s: $(grep -o 'TRAVWEB: built.*' $R/webmat_$TAG.log | head -1)"
  grep -E "TRAVWEB|Error" $R/webmat_$TAG.log | grep -v "^.*LogInit" | head -12
  ls -la $UE/Content/Traversal/Materials/M_TravWeb.uasset && touch $R/WEBMAT_DONE
fi
# 2. probes (once per tag unless NOPROBE)
if [ ! -f $R/NOPROBE ]; then
  mkdir -p $OUT
  for spec in c_wallrun_perch:10.5 p1_pawn_run:12 p1b_pawn_run:12 w1_wallrun_tall_zip:7.5 w2_wallrun_side_zip:7 r1_roofrun_zip:9.5 x2_rmb_cancel_wall:5 s1_high_swing:6 m1_mouse_swing:6 a_swing_chain:15.6; do
    n=${spec%%:*}; q=${spec#*:}
    [ $(el) -gt 700 ] && { echo "== probe time guard at $n"; break; }
    rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
    MT=""; [ "$n" = m1_mouse_swing ] && MT="-WHTravInputTest=mouseLook -WHMouseTestPx=40"
    "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
       -WHTravScript="$SC/$n.json" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" $MT | tail -1
    [ -f $RD/../round-24/${n}_telemetry.csv ] && echo "   $n vs round-24 capture: $(python3 $TD/round-24/tools/same.py $OUT/$n/${n}_telemetry.csv $TD/round-24/${n}_telemetry.csv)"
  done
  python3 $TD/r25_checks.py $OUT
fi
# 3. capture worker
# watchdog: never let the 2400 s max hold SIGKILL a rendering engine -- at 2280 s stop my own engine the safe way (SIGTERM, wait)
( while [ $(el) -lt 2280 ]; do sleep 5; [ -f $R/hold_$TAG.done ] && exit 0; done
  pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== WATCHDOG: stopping my engine at $(el) s"; \
    /Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "sm2-n1/traversal/unreal/WebHomage/WebHomage.uproject"; } ) &
mkdir -p $RD
# r25 hold A: ~0.85 rendered frames/s under the shared background-priority GPU (4 renders) -> estimate = frames x 1.3 s + 150 s start / encode
est() { case "$1" in a_swing_chain) echo 1370;; f4_chain_flips) echo 1200;; c_wallrun_perch) echo 970;; p1_pawn_run) echo 1090;; r1_roofrun_zip) echo 890;; f1_flow_backDouble) echo 850;;
        w1_wallrun_tall_zip) echo 740;; w2_wallrun_side_zip) echo 700;; s1_high_swing|m1_mouse_swing) echo 620;; x2_rmb_cancel_wall) echo 540;; x1_rmb_cancel_flip) echo 470;; *) echo 900;; esac; }
WARMED=0
while true; do
  s=$(head -1 $R/queue_$TAG.txt 2>/dev/null | tr -d ' ')
  [ -z "$s" ] && { echo "== queue empty at $(el) s"; break; }
  if [ $(( $(el) + $(est $s) )) -gt 2150 ]; then echo "== time guard: $s left at $(el) s"; break; fi
  tail -n +2 $R/queue_$TAG.txt > $R/queue_$TAG.tmp && mv $R/queue_$TAG.tmp $R/queue_$TAG.txt
  EXTRA_ARGS=""; P1JSON=p1_pawn_run.json; [ -f $R/tune.env ] && . $R/tune.env
  if [ $WARMED = 0 ] && [ ! -f $R/WARM_DONE ]; then
    echo "== warm-up (M_TravWeb shaders) at $(el) s"
    GPU_OUTER=1 NO_STILLS=1 WARM_QUIT=4 EXTRA_ARGS="$EXTRA_ARGS" P1JSON=$P1JSON docs/night1/traversal/capture_round.sh $R/warm_dummy none_xyz 2>&1 | tail -2
    touch $R/WARM_DONE
  fi
  WARMED=1
  echo "== capture $s at $(el) s (EXTRA_ARGS='$EXTRA_ARGS' P1JSON=$P1JSON) $(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1)"
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 EXTRA_ARGS="$EXTRA_ARGS" P1JSON=$P1JSON docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
  echo "$s $(date +%T) $EXTRA_ARGS" >> $R/captured.txt
done
echo "== hold $TAG done $(date +%T) at $(el) s, queue left: $(tr '\n' ' ' < $R/queue_$TAG.txt)"
touch $R/hold_$TAG.done; rm -f $R/hold_$TAG.running
exit 0
