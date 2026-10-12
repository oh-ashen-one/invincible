#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r23 hold 2 (inside ONE gpu_slot capture hold, compiled defaults only, no -WHGaitTune / -WHTravTune on any capture):
#   -nullrhi probes of w2 (full zip) / c (full) + w1 tower entries t1_c / t1_d -> r23_checks + pick w1 ->
#   if V23 a/b on both windows + Z23 + c perches: real captures of all 11 shot-list clips (time-guarded; leftovers in $R/LEFT, run by hold3)
#   else: -WHTravTune variant probes for the next build (no captures)
# The follow-up hold3 is queued (back of the FIFO) when this hold starts; it waits for this hold to finish before launching anything.
R=/Users/midir/sm2-n1/_scratch/traversal/r23
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SC=/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-23
OUT=$R/probe2
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
echo "== hold2 acquired $(date +%T)"
echo $$ > $R/hold2.running
# wait (bounded) for the build to be marked ready
for i in $(seq 1 90); do [ -f $R/READY ] && break; sleep 10; done
[ -f $R/READY ] || { echo "== build not READY after 15 min: exit"; rm -f $R/hold2.running; exit 0; }
probe() { local n=$1 j=$2 q=$3; shift 3; rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$j" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" "$@" | tail -1; }
verdict() { local f=$1 P=1
  [ "$(grep -c 'b) .*-> PASS' $f)" = 2 ] || P=0
  [ "$(grep -c 'a) .*-> PASS' $f)" = 2 ] || P=0
  grep -q "Z23 .*PASS" $f || P=0
  grep -q "CPERCH .*perch [0-9]" $f || P=0
  echo $P; }
cperch() { python3 - $1 <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
z = next((r for r in rows if r['sub'] == 'zipFire'), None)
p = next((r for r in rows if r['mode'] == 'perch'), None)
print(f"CPERCH zip {z['t'] if z else '-'} ({z['zip_why'] if z else '-'}) perch {p['t'] if p else 'none'} last {rows[-1]['mode']}/{rows[-1]['sub']} z {rows[-1]['z_m']}")
PY
}
mkdir -p $OUT
echo "== probes $(date +%T)"
probe w2_wallrun_side_zip $SC/w2_wallrun_side_zip.json 7.6
probe c_wallrun_perch $SC/c_wallrun_perch.json 10.5
python3 $TD/r23_checks.py $OUT | tee $R/probe2_check.txt
cperch $OUT/c_wallrun_perch/c_wallrun_perch_telemetry.csv | tee -a $R/probe2_check.txt
for n in t1_c t1_d; do probe $n $R/scripts/$n.json 7.5; done
python3 $R/pick_w1.py $OUT t1_c t1_d | tee $R/pick_w1_2.txt
PASS=$(verdict $R/probe2_check.txt)
echo "== probe verdict PASS=$PASS at $(el) s"
if [ $PASS = 0 ]; then
  # self-adapting: probe -WHTravTune variants; the first that passes becomes the compiled default (header edit + 15 s rebuild + re-probe)
  for v in WallZipFarRange=140 WallVertMaxDeg=14 WallVertMaxDeg=6 WallVertMaxDeg=0 WallZipFarRange=140,WallVertMaxDeg=0; do
    n=v_$(echo $v | tr ',=.' '_-p'); mkdir -p $OUT/$n
    probe w2_wallrun_side_zip $SC/w2_wallrun_side_zip.json 7.6 -WHTravTune=$v
    probe c_wallrun_perch $SC/c_wallrun_perch.json 10.5 -WHTravTune=$v
    cp $OUT/w2_wallrun_side_zip/*_telemetry.csv $OUT/c_wallrun_perch/*_telemetry.csv $OUT/$n/
    python3 $TD/r23_checks.py $OUT/$n > $OUT/$n/check.txt; cperch $OUT/$n/c_wallrun_perch_telemetry.csv >> $OUT/$n/check.txt
    echo "-- variant $v"; grep -E "^  [wc]|a\)|b\)|recoveries|hips|torso|touchdowns|Z23|T22|CPERCH" $OUT/$n/check.txt
    if [ "$(verdict $OUT/$n/check.txt)" = 1 ]; then
      echo "== variant $v passes: make it the compiled default $(date +%T)"
      H=/Users/midir/sm2-n1/traversal/unreal/WebHomage/Source/WebHomage/Traversal/WebTraversalComponent.h
      for kv in $(echo $v | tr ',' ' '); do k=${kv%%=*}; x=${kv#*=}
        sed -i '' -E "s/(float $k = )[0-9.]+f;/\1${x}.f;/" $H; grep -n "float $k = " $H; done
      echo "$v" > $R/DEFAULT_CHANGED
      /Users/midir/sm2-n1/traversal/docs/night1/traversal/build_p3.sh | tail -3
      probe w2_wallrun_side_zip $SC/w2_wallrun_side_zip.json 7.6
      probe c_wallrun_perch $SC/c_wallrun_perch.json 10.5
      python3 $TD/r23_checks.py $OUT | tee $R/probe2_check.txt; cperch $OUT/c_wallrun_perch/c_wallrun_perch_telemetry.csv | tee -a $R/probe2_check.txt
      PASS=$(verdict $R/probe2_check.txt); echo "== rebuilt default verdict PASS=$PASS at $(el) s"
      break
    fi
  done
  if [ $PASS = 0 ]; then echo "== hold 2 done (no captures) $(date +%T)"; rm -f $R/hold2.running; exit 0; fi
  for n in t1_c t1_d; do probe $n $R/scripts/$n.json 7.5; done
  python3 $R/pick_w1.py $OUT t1_c t1_d | tee $R/pick_w1_2.txt
fi
# queue the follow-up hold now (back of the FIFO); it waits for this hold before launching
if [ ! -f $R/hold3.queued ]; then
  touch $R/hold3.queued
  ( env -u GPU_SLOT_HELD -u GPU_SLOT_LABEL -u GPU_SLOT_WAIT_S -u GPU_SLOT_JSON GPU_SLOT_CAPTURE_WAIT_TIMEOUT=14400 \
      nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label traversal -- $R/hold3.sh > $R/hold3.log 2>&1 & echo $! > $R/hold3.pid )
fi
if [ -s $OUT/PICK_T1 ]; then
  python3 - "$(cat $OUT/PICK_T1)" <<'PY'
import json, sys
R = '/Users/midir/sm2-n1/_scratch/traversal/r23'; SC = '/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city'
w1 = json.load(open(f'{R}/scripts/{sys.argv[1]}.json')); w1['name'] = 'w1_wallrun_tall_zip'
w1['note'] = (f'Round 23: w1 on the sunlit 300 m tower west face (x ~-229.4, lit above ~48 m): jump onto the face from the podium height, vertical wall run, '
              f'E at {w1["keys"][2]["t"]} s -> zip (facade top > 110 m up: nearest visible roof edge) -> perch, E on the perch at {w1["keys"][5]["t"]} s. Variant {sys.argv[1]}.')
json.dump(w1, open(f'{SC}/w1_wallrun_tall_zip.json', 'w'), indent=1)
print('w1 script <-', sys.argv[1])
PY
else echo "== no w1 tower pick: w1 stays on the r22 route"; fi
cd /Users/midir/sm2-n1/traversal
mkdir -p $RD
: > $R/LEFT
for s in c_wallrun_perch w2_wallrun_side_zip w1_wallrun_tall_zip x2_rmb_cancel_wall a_swing_chain f1_flow_backDouble f4_chain_flips x1_rmb_cancel_flip m1_mouse_swing s1_high_swing r1_roofrun_zip; do
  if [ $(el) -gt 1950 ]; then echo "== time guard: $s left for hold3"; echo $s >> $R/LEFT; continue; fi
  echo "== capture $s at $(el) s (GPU $(ioreg -r -d 1 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1))"
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
done
echo "== hold 2 done $(date +%T), left: $(cat $R/LEFT | tr '\n' ' ')"
rm -f $R/hold2.running
exit 0
