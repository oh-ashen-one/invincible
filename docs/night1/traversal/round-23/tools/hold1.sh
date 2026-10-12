#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r23 hold 1 (inside ONE gpu_slot capture hold, compiled defaults only): -nullrhi probes of the two vertical windows (w2, c) + two w1
# tower entries -> r23_checks -> if V23 a/b + Z23 pass: real captures of all 11 shot-list clips (time-guarded under the 40 min hold);
# else: variant probes (-WHGaitTune) of w2 / c to pick the next defaults, no captures
R=/Users/midir/sm2-n1/_scratch/traversal/r23
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SC=/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-23
OUT=$R/probe
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
probe() { local n=$1 j=$2 q=$3; shift 3; rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$j" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" "$@" | tail -1; }
echo "== probes $(date +%T)"
probe w2_wallrun_side_zip $SC/w2_wallrun_side_zip.json 7.2
probe c_wallrun_perch $SC/c_wallrun_perch.json 4.6
cp $OUT/w2_wallrun_side_zip/w2_wallrun_side_zip_telemetry.csv $OUT/c_wallrun_perch/c_wallrun_perch_telemetry.csv $OUT/ 2>/dev/null
python3 $TD/r23_checks.py $OUT | tee $R/probe_check.txt
for n in t1_c t1_d; do probe $n $R/scripts/$n.json 7.5; done
python3 $R/pick_w1.py $OUT t1_c t1_d | tee $R/pick_w1.txt
PASS=1
grep -q "b) .*-> PASS" $R/probe_check.txt || PASS=0
[ "$(grep -c 'b) .*-> PASS' $R/probe_check.txt)" = 2 ] || PASS=0
[ "$(grep -c 'a) .*-> PASS' $R/probe_check.txt)" = 2 ] || PASS=0
grep -q "Z23 .*PASS" $R/probe_check.txt || PASS=0
echo "== probe verdict PASS=$PASS at $(el) s"
if [ $PASS = 0 ]; then
  for v in $(cat $R/VARIANTS); do
    n=v_$(echo $v | tr ',=.' '_-p'); mkdir -p $OUT/$n
    probe w2_wallrun_side_zip $SC/w2_wallrun_side_zip.json 3.0 -WHGaitTune=$v
    probe c_wallrun_perch $SC/c_wallrun_perch.json 4.3 -WHGaitTune=$v
    mkdir -p $OUT/$n; cp $OUT/w2_wallrun_side_zip/*_telemetry.csv $OUT/c_wallrun_perch/*_telemetry.csv $OUT/$n/
    echo "-- variant $v"; python3 $TD/r23_checks.py $OUT/$n | grep -E "^  [wc]|a\)|b\)|recoveries|hips|torso"
    [ $(el) -gt 2000 ] && break
  done
  echo "== hold 1 done (no captures) $(date +%T)"; exit 0
fi
if [ -s $OUT/PICK_T1 ]; then
  python3 - "$(cat $OUT/PICK_T1)" <<'PY'
import json, sys
R = '/Users/midir/sm2-n1/_scratch/traversal/r23'; SC = '/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city'
w1 = json.load(open(f'{R}/scripts/{sys.argv[1]}.json')); w1['name'] = 'w1_wallrun_tall_zip'
w1['note'] = (f'Round 23: w1 on the sunlit 284 m tower west face (x ~-229.4, lit above ~48 m): jump onto the face from the podium height, vertical wall run, '
              f'E at {w1["keys"][2]["t"]} s -> zip (the facade top is > 110 m up: nearest roof edge) -> perch, E on the perch at {w1["keys"][5]["t"]} s. Variant {sys.argv[1]}.')
json.dump(w1, open(f'{SC}/w1_wallrun_tall_zip.json', 'w'), indent=1)
PY
fi
cd /Users/midir/sm2-n1/traversal
mkdir -p $RD
for s in c_wallrun_perch w2_wallrun_side_zip w1_wallrun_tall_zip x2_rmb_cancel_wall a_swing_chain f1_flow_backDouble f4_chain_flips x1_rmb_cancel_flip m1_mouse_swing s1_high_swing r1_roofrun_zip; do
  if [ $(el) -gt 2050 ]; then echo "== time guard: $s and later left for the next hold"; echo $s >> $R/LEFT; continue; fi
  echo "== capture $s at $(el) s"
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
done
echo "== hold 1 done $(date +%T)"
exit 0
