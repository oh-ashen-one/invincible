#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r24 hold F (build 7: on foot / perched the chase spot is pulled in rather than over a raised roof feature; on top of build 6 --
# GndStopExtra 2.4 / GndStopR 0.9 compiled): -nullrhi probes of every clip build 4 can change -> r24 / r23 checks -> real captures of the
# clips whose path or camera differs from their round-24 capture (c always: its gate needs the render). Time-guarded.
R=/Users/midir/sm2-n1/_scratch/traversal/r24
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SC=/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-24
OUT=$R/probeF
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
echo "== holdF acquired $(date +%T)"; echo $$ > $R/holdF.running
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine still running: wait"; sleep 60; }
[ -f $R/READY7 ] || { echo "== build 7 not READY: exit"; rm -f $R/holdF.running; exit 0; }
mkdir -p $OUT
LIST="c_wallrun_perch"
for spec in c_wallrun_perch:10.5 x2_rmb_cancel_wall:5 r1_roofrun_zip:9.5 w2_wallrun_side_zip:7 w1_wallrun_tall_zip:7.5 a_swing_chain:15.6; do
  n=${spec%%:*}; q=${spec#*:}
  rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$SC/$n.json" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" | tail -1
  V=$(python3 $R/same.py $OUT/$n/${n}_telemetry.csv $RD/${n}_telemetry.csv); V23=$(python3 $R/same.py $OUT/$n/${n}_telemetry.csv $TD/round-23/${n}_telemetry.csv)
  echo "== build 7 $n vs round-24 capture: $V | vs round 23: $V23"
  case "$V" in SAME*) ;; *) case " $LIST " in *" $n "*) ;; *) LIST="$LIST $n";; esac;; esac
done
python3 $TD/r24_checks.py $OUT | grep -E "T7|T3|T1|T2|T4 ->|CAM|c_wallrun|c zip|^     " | tee $R/probeF_r24.txt
python3 $TD/r23_checks.py $OUT | grep -E "PASS|FAIL|recoveries|torso|T22" | tee $R/probeF_r23.txt
for n in c_wallrun_perch w1_wallrun_tall_zip w2_wallrun_side_zip r1_roofrun_zip; do python3 - $OUT/$n/${n}_telemetry.csv $n <<'PY'
import csv, sys
r = list(csv.DictReader(open(sys.argv[1])))
g = [x for x in r if x['mode'] in ('perch', 'ground', 'land')]
out = [x['t'] for x in g if float(x['hero_in_frame']) < 1]
print(f"== {sys.argv[2]} on foot / perched rows {len(g)}: hero out of frame {len(out)} {out[:3]}{out[-2:] if len(out) > 3 else ''}")
PY
done
echo "== capture list: $LIST"
cd /Users/midir/sm2-n1/traversal
: > $R/LEFTF
for s in $LIST; do
  if [ $(el) -gt 2000 ]; then echo "== time guard: $s left"; echo $s >> $R/LEFTF; continue; fi
  echo "== capture $s at $(el) s"
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
done
echo "== hold F done $(date +%T), left: $(tr '\n' ' ' < $R/LEFTF)"
touch $R/holdF.done; rm -f $R/holdF.running
exit 0
