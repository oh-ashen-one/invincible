#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r25 hold, build 2 (run INSIDE one `gpu_slot.sh capture --label traversal -- <this> <tag>`; queue it from your own shell):
#   1. content: M_TravWeb (-nullrhi commandlet) when $R/WEBMAT2_DONE is missing
#   2. -nullrhi probes listed in $R/probes_<tag>.txt ("<name> <script path> <quit>" per line), telemetry -> $R/probe_<tag>/<name>/
#   3. a worker popping $R/queue_<tag>.txt: "<clip>" = capture_round.sh into round-25 (NO_STILLS, SKIP_WARM),
#      "rprobe:<label>:<quit>" = a short rendered a_swing_chain movie into $R/rprobe_<label>/ + rope_r25_check.py (tune: $R/tune.env EXTRA_ARGS),
#      "warm" = the 960x540 warm-up render (shaders of the rebuilt M_TravWeb)
# Time-guarded under the 2400 s max hold; a watchdog stops MY engine the safe way (stop_ue.sh: SIGTERM, wait) at 2280 s.
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
for i in $(seq 1 60); do ls $R/hold_*.running 2>/dev/null | grep -qv "hold_$TAG.running" || break; [ $i = 1 ] && echo "== waiting for my previous hold to end"; sleep 10; done
ls $R/hold_*.running 2>/dev/null | grep -qv "hold_$TAG.running" && { echo "== previous hold still running: exit"; exit 0; }
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine still running: wait 60 s"; sleep 60; }
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine STILL running: exit"; exit 0; }
echo $$ > $R/hold_$TAG.running
cd $WT
( while [ $(el) -lt 2280 ]; do sleep 5; [ -f $R/hold_$TAG.done ] && exit 0; done
  pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== WATCHDOG: stopping my engine at $(el) s"; \
    /Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/traversal"; } ) &
if [ ! -f $R/WEBMAT2_DONE ]; then
  echo "== content M_TravWeb (build 2) at $(el) s"
  "$UEB" "$UE/WebHomage.uproject" -run=pythonscript -script="$UE/Scripts/build_traversal_web.py" -unattended -nullrhi -NoSound \
     -abslog="$R/webmat2_$TAG.log" > /dev/null 2>&1
  echo "   rc $? at $(el) s: $(grep -o 'TRAVWEB: built.*' $R/webmat2_$TAG.log | head -1)"
  grep -E "TRAVWEB|Error|error" $R/webmat2_$TAG.log | grep -v LogInit | head -12
  grep -q "TRAVWEB: built.*connections_ok=True" $R/webmat2_$TAG.log && touch $R/WEBMAT2_DONE
fi
if [ -s $R/probes_$TAG.txt ]; then
  mkdir -p $OUT
  while read -r n js q; do
    [ -z "$n" ] && continue
    [ $(el) -gt 900 ] && { echo "== probe time guard at $n"; break; }
    rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
    "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
       -WHTravScript="$js" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" | tail -1
    echo "   probe $n done at $(el) s"
  done < $R/probes_$TAG.txt
fi
est() { case "$1" in a_swing_chain) echo 1370;; f4_chain_flips) echo 1200;; c_wallrun_perch) echo 970;; p1_pawn_run) echo 1090;; r1_roofrun_zip) echo 890;; f1_flow_backDouble) echo 850;;
        w1_wallrun_tall_zip) echo 740;; w2_wallrun_side_zip) echo 700;; s1_high_swing|m1_mouse_swing) echo 620;; x2_rmb_cancel_wall) echo 540;; x1_rmb_cancel_flip) echo 470;;
        rprobe:*) echo 420;; warm) echo 200;; *) echo 900;; esac; }
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
        -- -benchmark -fps=60 -WHTravScript="$SC/a_swing_chain.json" $EXTRA_ARGS | tail -1 ;;
    rprobe:*)
      L=$(echo $s | cut -d: -f2); Q=$(echo $s | cut -d: -f3); P=$R/rprobe_$L; rm -rf $P; mkdir -p $P
      QP=$(python3 -c "print(round($Q + 0.8, 3))")
      "$UE/Scripts/run_game.sh" $P/run -map /Game/Maps/Manhattan -res 1920x1080 -quit $QP -name a -movie -timeout 1500 -exec "r.ScreenPercentage 100" \
        -- -WHTravScript="$SC/a_swing_chain.json" -WHTravPreroll=0.8 -WHTravMask $EXTRA_ARGS | tail -1
      FR=$P/run/a_frames; CSV=$P/run/a_telemetry.csv
      if [ -d $FR ] && [ -f $CSV ]; then
        NF=$(ls $FR | wc -l | tr -d ' '); NT=$(( $(wc -l < $CSV) - 1 )); SK=$(( NF - NT ))
        ffmpeg -loglevel error -y -framerate 60 -start_number $SK -i "$FR/MovieFrame%05d.png" -c:v libx264 -pix_fmt yuv420p -crf 18 $P/a.mp4
        cp $CSV $P/a_telemetry.csv
        python3 $TD/rope_r25_check.py $P/a.mp4 $P/a_telemetry.csv rprobe_$L --out $P/rope.json 2>&1 | tee $P/ROPE.txt
        rm -rf $FR
      fi ;;
    *)
      GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 EXTRA_ARGS="$EXTRA_ARGS" docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
      echo "$s $(date +%T) $EXTRA_ARGS" >> $R/captured.txt ;;
  esac
  echo "   $s took $(( $(el) - T0 )) s"
done
echo "== hold $TAG done $(date +%T) at $(el) s, queue left: $(tr '\n' ' ' < $R/queue_$TAG.txt)"
touch $R/hold_$TAG.done; rm -f $R/hold_$TAG.running
exit 0
