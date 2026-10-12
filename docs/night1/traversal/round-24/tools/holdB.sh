#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r24 hold B (one gpu_slot capture hold, after hold A): build 2 (ground-camera orbit stop) must be marked READY2. -nullrhi probes of the
# c roof camera turn (GndStop variants) -> pick the first that passes the CAM gate -> (header default + rebuild) -> captures: c, the
# ground / perch clips (w2, w1, r1: the ground camera changed after hold A captured them), then hold A's leftovers. Time-guarded.
R=/Users/midir/sm2-n1/_scratch/traversal/r24
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SC=/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-24
OUT=$R/probeB
HC=$UE/Source/WebHomage/Traversal/WebTravCamera.h
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
echo "== holdB acquired $(date +%T)"; echo $$ > $R/holdB.running
while [ -f $R/holdA.running ] && kill -0 "$(cat $R/holdA.running 2>/dev/null)" 2>/dev/null; do sleep 10; done
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine still running: wait"; sleep 60; }
for i in $(seq 1 60); do [ -f $R/READY2 ] && break; sleep 10; done
[ -f $R/READY2 ] || { echo "== build 2 not READY: exit"; rm -f $R/holdB.running; exit 0; }
probe() { local n=$1 j=$2 q=$3; shift 3; rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$j" -WHTravCsv="$OUT/$n/c_wallrun_perch_telemetry.csv" "$@" | tail -1; }
mkdir -p $OUT
PICK=""
for v in default GndStopExtra=2.4 GndStopExtra=2.4,GndStopR=0.9 GndStopExtra=0.4; do
  n=c_$(echo $v | tr ',=.' '_-p')
  if [ $v = default ]; then probe $n $SC/c_wallrun_perch.json 10.5; else probe $n $SC/c_wallrun_perch.json 10.5 -WHCamTune=$v; fi
  python3 $TD/r24_checks.py $OUT/$n --clip none | grep -E "c_wallrun|c zip" | tee $OUT/$n/cam.txt | sed "s/^/$v: /"
  # nullrhi: hero_occl is not rendered (-1); the gate here = in frame, >= 3 m, no reversal, and the zip still ends on a perch
  if /usr/bin/grep -q "GEOM_OK" $OUT/$n/cam.txt && /usr/bin/grep -q "perch [0-9]" $OUT/$n/cam.txt; then PICK=$v; break; fi
done
echo "== camera pick: '${PICK:-none}' at $(el) s"
if [ -n "$PICK" ] && [ "$PICK" != default ]; then
  for kv in $(echo $PICK | tr ',' ' '); do k=${kv%%=*}; x=${kv#*=}; sed -i '' -E "s/($k = )[0-9.]+/\1$x/" $HC; grep -n "$k = " $HC; done
  echo "$PICK" > $R/CAM_DEFAULT_CHANGED
  $TD/build_p3.sh | tail -2
  probe c_rebuilt $SC/c_wallrun_perch.json 10.5
  python3 $TD/r24_checks.py $OUT/c_rebuilt --clip none | grep -E "c_wallrun|c zip"
fi
# build 3 (open-street rule for the altitude release): which hold-A captures does it change? (-nullrhi path + camera vs the captured telemetry)
cd /Users/midir/sm2-n1/traversal
LIST="c_wallrun_perch x2_rmb_cancel_wall r1_roofrun_zip m1_mouse_swing"
for spec in a_swing_chain:16 w2_wallrun_side_zip:7.6 w1_wallrun_tall_zip:7.5 s1_high_swing:6; do
  n=${spec%%:*}; q=${spec#*:}
  rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$SC/$n.json" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" | tail -1
  V=$(python3 $R/same.py $OUT/$n/${n}_telemetry.csv $RD/${n}_telemetry.csv); echo "== build 3 vs captured $n: $V"
  case "$V" in SAME*) ;; *) LIST="$LIST $n";; esac
done
for n in x2_rmb_cancel_wall r1_roofrun_zip; do
  q=5; [ $n = r1_roofrun_zip ] && q=9.5
  rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$SC/$n.json" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" | tail -1
  echo "== build 3 $n vs ROUND 23: $(python3 $R/same.py $OUT/$n/${n}_telemetry.csv $TD/round-23/${n}_telemetry.csv)"
done
echo "== capture list: $LIST"
: > $R/LEFTB
for s in $LIST; do
  if [ $(el) -gt 2050 ]; then echo "== time guard: $s left"; echo $s >> $R/LEFTB; continue; fi
  echo "== capture $s at $(el) s"
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
done
echo "== hold B done $(date +%T), left: $(tr '\n' ' ' < $R/LEFTB)"
touch $R/holdB.done; rm -f $R/holdB.running
exit 0
