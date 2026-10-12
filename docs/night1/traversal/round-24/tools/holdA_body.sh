#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r24 hold A (inside ONE gpu_slot capture hold): -nullrhi probes of the a-chain variants (script repressVz x AltApexH) and the c camera
# variants -> pick -> (header default + rebuild if a tune wins) -> regression probes -> real captures (time-guarded; leftovers -> hold B).
R=/Users/midir/sm2-n1/_scratch/traversal/r24
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SC=/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-24
OUT=$R/probe
H=$UE/Source/WebHomage/Traversal/WebTraversalComponent.h
HC=$UE/Source/WebHomage/Traversal/WebTravCamera.h
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
echo "== holdA body $(date +%T)"; echo $$ > $R/holdA.running
probe() { local n=$1 j=$2 q=$3; shift 3; rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$j" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" "$@" | tail -1; }
mkdir -p $OUT
# queue hold B now (back of the FIFO): leftovers of the capture list
if [ ! -f $R/holdB.queued ]; then
  touch $R/holdB.queued
  ( env -u GPU_SLOT_HELD -u GPU_SLOT_LABEL -u GPU_SLOT_WAIT_S -u GPU_SLOT_JSON GPU_SLOT_CAPTURE_WAIT_TIMEOUT=14400 \
      nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label traversal -- $R/holdB.sh > $R/holdB.log 2>&1 & echo $! > $R/holdB.pid )
fi
echo "== a variants $(date +%T)"
NAMES=""
for rv in 6 12 18; do
  probe a_rv$rv $R/scripts/a_rv$rv.json 16; NAMES="$NAMES a_rv$rv"
  # (the probe dir name = clip name for r24_checks --clip)
done
for rv in 12 18; do
  cp $R/scripts/a_rv$rv.json $R/scripts/a_rv${rv}h.json
  sed -i '' "s/\"name\": \"a_rv$rv\"/\"name\": \"a_rv${rv}h\"/" $R/scripts/a_rv${rv}h.json
  probe a_rv${rv}h $R/scripts/a_rv${rv}h.json 16 -WHTravTune=AltApexH=36; NAMES="$NAMES a_rv${rv}h"
done
python3 $R/pick_a.py $OUT $NAMES | tee $R/pick_a.txt
for n in $NAMES; do echo "---- $n"; grep -E "T7|T3|T1|T2|T4 ->|^   +[0-9]" $OUT/$n/check.txt | head -16; done
BEST=$(cat $OUT/BEST_A 2>/dev/null)
echo "== c camera variants $(date +%T)"
probe c_wallrun_perch $SC/c_wallrun_perch.json 10.5
python3 $TD/r24_checks.py $OUT/c_wallrun_perch --clip none | grep -A3 CAM | tee $R/c_default.txt
mkdir -p $OUT/c_abs0; probe c_abs0 $SC/c_wallrun_perch.json 10.5 -WHCamTune=GndAbsorb=0
mv $OUT/c_abs0/c_abs0_telemetry.csv $OUT/c_abs0/c_wallrun_perch_telemetry.csv 2>/dev/null
python3 $TD/r24_checks.py $OUT/c_abs0 --clip none | grep -A3 CAM | tee $R/c_abs0.txt
CPASS=$(grep -c "c_wallrun_perch 7.7-8.5.*PASS" $R/c_default.txt)
CPASS0=$(grep -c "c_wallrun_perch 7.7-8.5.*PASS" $R/c_abs0.txt)
CHANGED=0
case "$BEST" in *h) echo "== AltApexH 36 wins: header default"; sed -i '' -E 's/(float AltApexH = )[0-9.]+f;/\136.f;/' $H; grep -n "float AltApexH" $H; CHANGED=1;; esac
if [ "$CPASS" = 0 ] && [ "$CPASS0" = 1 ]; then echo "== GndAbsorb 0 wins"; sed -i '' -E 's/GndAbsorb = 1\.0/GndAbsorb = 0.0/' $HC; grep -n "GndAbsorb =" $HC; CHANGED=1; fi
RV=$(echo "$BEST" | sed -E 's/a_rv([0-9]+)h?/\1/')
if [ -n "$RV" ]; then
  python3 - $RV <<'PY'
import json, sys
p = '/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city/a_swing_chain.json'
d = json.load(open(p)); rv = -float(sys.argv[1])
for k in d['keys']:
    if k.get('autoChain'): k['repressVz'] = rv
d['note'] = d['note'].split(' Round 24:')[0] + f' Round 24: the player re-presses the web once falling at {-rv:g} m/s (altitude chain: the release climbs to the roofline first).'
json.dump(d, open(p, 'w'), indent=1); print('a script repressVz ->', rv)
PY
fi
if [ $CHANGED = 1 ]; then echo "== rebuild $(date +%T)"; $TD/build_p3.sh | tail -2; fi
echo "== regression probes at $(el) s"
probe a_swing_chain $SC/a_swing_chain.json 16
[ $CHANGED = 1 ] && { probe c_wallrun_perch $SC/c_wallrun_perch.json 10.5; }
probe w2_wallrun_side_zip $SC/w2_wallrun_side_zip.json 7.6
probe w1_wallrun_tall_zip $SC/w1_wallrun_tall_zip.json 7.5
python3 $TD/r24_checks.py $OUT | tee $R/probe_r24.txt
python3 $TD/r23_checks.py $OUT | grep -E "PASS|FAIL|Z23|V23" | tee $R/probe_r23.txt
cd /Users/midir/sm2-n1/traversal
mkdir -p $RD
: > $R/LEFT
for s in a_swing_chain c_wallrun_perch w2_wallrun_side_zip w1_wallrun_tall_zip f1_flow_backDouble f4_chain_flips x2_rmb_cancel_wall x1_rmb_cancel_flip m1_mouse_swing s1_high_swing r1_roofrun_zip; do
  if [ $(el) -gt 1900 ]; then echo "== time guard: $s left for hold B"; echo $s >> $R/LEFT; continue; fi
  echo "== capture $s at $(el) s (GPU $(ioreg -r -d 1 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1))"
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
done
echo "== hold A done $(date +%T), left: $(tr '\n' ' ' < $R/LEFT)"
touch $R/holdA.done; rm -f $R/holdA.running
exit 0
