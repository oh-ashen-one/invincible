#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r26 hold (run INSIDE one `gpu_slot.sh capture --label traversal -- <this> <tag>`; queue it from your own shell, never inside a hold):
#   1. content: the original hero suits (round-26/tools/build_suits_p3.py, -nullrhi commandlet) when $R/SUITS_DONE is missing and the CPU maps exist
#   2. -nullrhi probes listed in $R/probes_<tag>.txt ("<name> <script path> <quit> [extra UE args...]" per line), telemetry -> $R/probe_<tag>/<name>/
#   3. a worker popping $R/queue_<tag>.txt: "<clip>" = capture_round.sh into round-26 (NO_STILLS, SKIP_WARM),
#      "warm" = the 960x540 warm-up render, "default" = a DEFAULT launch (Manhattan, no script, no suit args) with 1080p stills at 3 / 5 s
# Time-guarded under the 2400 s max hold; a watchdog stops MY engine the safe way (stop_ue.sh: SIGTERM, wait) at 2280 s.
TAG=${1:-h}
R=/Users/midir/sm2-n1/_scratch/traversal/r26
WT=/Users/midir/sm2-n1/traversal
UE=$WT/unreal/WebHomage
UEB="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
SC=$WT/docs/night1/traversal/scripts/city
TD=$WT/docs/night1/traversal
RD=$TD/round-26
OUT=$R/probe_$TAG
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
echo "== hold $TAG acquired $(date +%T)"
for i in $(seq 1 60); do ls $R/hold_*.running 2>/dev/null | grep -qv "hold_$TAG.running" || break; [ $i = 1 ] && echo "== waiting for my previous hold to end"; sleep 10; done
ls $R/hold_*.running 2>/dev/null | grep -qv "hold_$TAG.running" && { echo "== previous hold still running: exit"; exit 0; }
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine still running: wait 60 s"; sleep 60; }
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine STILL running: exit"; exit 0; }
echo $$ > $R/hold_$TAG.running
cd $WT
( while [ $(el) -lt 2280 ]; do sleep 5; [ -f $R/hold_$TAG.done ] && exit 0; done
  pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== WATCHDOG: stopping my engine at $(el) s"; \
    /Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/traversal"; } ) &
if [ -f $R/NEED_BUILD ]; then   # C++ changed since the last build (no engine of mine runs at this point)
  echo "== C++ build at $(el) s"; $TD/build_p3.sh 2>&1 | tail -3
  grep -q "Result: Succeeded" $UE/Saved/build_last.log && rm -f $R/NEED_BUILD || { echo "== BUILD FAILED: no engine run in this hold"; touch $R/hold_$TAG.done; rm -f $R/hold_$TAG.running; exit 0; }
fi
if [ ! -f $R/SUITS_DONE ] && [ -f $WT/art/night1/characters/hero/tex/suit_orm_r8.png ]; then
  echo "== content: original hero suits at $(el) s"
  "$UEB" "$UE/WebHomage.uproject" -run=pythonscript -script="$RD/tools/build_suits_p3.py" -unattended -nullrhi -NoSound \
     -abslog="$R/suits_$TAG.log" > /dev/null 2>&1
  echo "   rc $? at $(el) s"
  grep -E "P3SUITS|skins: suit|skins ok|Error" $R/suits_$TAG.log | grep -v LogInit | sed 's/^.*LogPython: //' | head -24
  grep -q "P3SUITS: done, DA_HeroSuits suits=8" $R/suits_$TAG.log && touch $R/SUITS_DONE
fi
if [ -s $R/probes_$TAG.txt ]; then
  mkdir -p $OUT
  while read -r n js q extra; do
    [ -z "$n" ] && continue
    [ $(el) -gt 1500 ] && { echo "== probe time guard at $n"; break; }
    rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
    # shellcheck disable=SC2086
    "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
       -WHTravScript="$js" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" $extra < /dev/null | tail -1
    echo "   probe $n done at $(el) s"
  done < $R/probes_$TAG.txt
fi
est() { python3 $RD/tools/split_est.py "$1"; }   # round 26: estimates from the measured s/frame (split_est.py)
[ -n "${EST_SCALE:-}" ] || EST_SCALE=1.0
while true; do
  s=$(head -1 $R/queue_$TAG.txt 2>/dev/null | tr -d ' ')
  [ -z "$s" ] && { echo "== queue empty at $(el) s"; break; }
  [ -f $R/est_scale ] && EST_SCALE=$(cat $R/est_scale)
  E=$(python3 -c "print(int($(est $s) * $EST_SCALE))")
  if [ $(( $(el) + E )) -gt 2200 ]; then echo "== time guard: $s (est $E s) left at $(el) s"; break; fi
  tail -n +2 $R/queue_$TAG.txt > $R/queue_$TAG.tmp && mv $R/queue_$TAG.tmp $R/queue_$TAG.txt
  EXTRA_ARGS=""; [ -f $R/tune.env ] && . $R/tune.env
  T0=$(el)
  echo "== $s at $T0 s (EXTRA_ARGS='$EXTRA_ARGS') $(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1)"
  case "$s" in
    warm)
      rm -rf /Users/midir/sm2-n1/_scratch/traversal/capture/warmup
      "$UE/Scripts/run_game.sh" /Users/midir/sm2-n1/_scratch/traversal/capture/warmup -map /Game/Maps/Manhattan -res 960x540 -quit 4 -name warmup -timeout 1500 \
        -- -benchmark -fps=60 -WHTravScript="$SC/a_swing_chain.json" $EXTRA_ARGS < /dev/null | tail -1 ;;
    splitA:*|splitB:*)   # split movie capture (round-26/tools/split_capture.sh): "splitA:<clip>:<tm>" / "splitB:<clip>:<tm>"
      M=$(echo $s | cut -d: -f1); C=$(echo $s | cut -d: -f2); TMS=$(echo $s | cut -d: -f3)
      EXTRA_ARGS="$EXTRA_ARGS" $RD/tools/split_capture.sh ${M#split} $C $TMS
      L=/Users/midir/sm2-n1/_scratch/traversal/capture/${C}_${M#split}/$C.log
      echo "   $(grep -c 'Tracing Screenshot' $L 2>/dev/null) frames written; $(grep -h 'WH_TRAV hero suit' $L | sed 's/^.*Display: //' | head -1)"
      echo "$s $(date +%T) $EXTRA_ARGS" >> $R/captured.txt ;;
    default)
      D=$R/default_launch; rm -rf $D; mkdir -p $D
      "$UE/Scripts/run_game.sh" $D -map /Game/Maps/Manhattan -res 1920x1080 -shots 3,5,7 -quit 8 -name default -timeout 1500 -exec "r.ScreenPercentage 100" < /dev/null | tail -1
      grep -E "WH_SUIT|WH_TRAV hero suit" $D/default.log | sed 's/^.*LogWebHomage: Display: //' | head -8 ;;
    *)
      GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 EXTRA_ARGS="$EXTRA_ARGS" docs/night1/traversal/capture_round.sh $RD $s < /dev/null 2>&1 | tail -3
      grep -hE "WH_SUIT start|WH_TRAV hero suit" /Users/midir/sm2-n1/_scratch/traversal/capture/$s/$s.log | sed 's/^.*LogWebHomage: Display: //' | head -3
      echo "$s $(date +%T) $EXTRA_ARGS" >> $R/captured.txt ;;
  esac
  echo "   $s took $(( $(el) - T0 )) s"
done
echo "== hold $TAG done $(date +%T) at $(el) s, queue left: $(tr '\n' ' ' < $R/queue_$TAG.txt 2>/dev/null)"
touch $R/hold_$TAG.done; rm -f $R/hold_$TAG.running
exit 0
