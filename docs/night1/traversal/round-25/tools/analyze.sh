#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r25 measurement pass on the captured round (CPU only): rope readability (rope_r25_check.py, a at 10 fps), c perch gate + r24 ground-orbit
# gate (r25_checks.py), pawn run cadence (cadence_r25.py), r24 tests (T7/T3/T1/T2/T4) for "no axis below r24", owner bugs, sizes, shot list.
set -u
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-25
cd $RD
{ echo "# Round 25 rope readability (rope_r25_check.py, 10 fps, rendered 1080p movies)"
  for n in a_swing_chain m1_mouse_swing s1_high_swing; do [ -f $n.mp4 ] && python3 $TD/rope_r25_check.py $n.mp4 ${n}_telemetry.csv $n --out /Users/midir/sm2-n1/_scratch/traversal/r25/${n}_rope25.json; done
} > ROPE_CHECK.txt 2>&1; cat ROPE_CHECK.txt
{ echo "# Round 25 gates (r25_checks.py)"; python3 $TD/r25_checks.py $RD
  echo "# pawn run cadence (cadence_r25.py, head-top FFT over 1.5-11 s)"; [ -f p1_pawn_run.mp4 ] && python3 $TD/cadence_r25.py p1_pawn_run.mp4 p1_pawn_run_telemetry.csv 1.5 11
} > R25_GATES.txt 2>&1; cat R25_GATES.txt
{ echo "# attach-to-attach gaps (critic r24 secondary 2: <= 3.3 s)"
  for n in a_swing_chain m1_mouse_swing s1_high_swing f4_chain_flips; do [ -f ${n}_telemetry.csv ] && python3 -c "
import csv
r=list(csv.DictReader(open('${n}_telemetry.csv'))); prev=0; on=[]
for x in r:
    w=float(x['web_on'])>0.5
    if w and not prev: on.append(round(float(x['t']),2))
    prev=w
g=[round(b-a,2) for a,b in zip(on,on[1:])]
print('  $n attaches', on, 'gaps', g, 'max', max(g) if g else None, '-> PASS' if g and max(g) <= 3.3 else '-> FAIL')"; done
} > GAPS.txt 2>&1; cat GAPS.txt
python3 $TD/r24_checks.py $RD --rendered > /dev/null 2>&1; [ -f R24_CHECK.txt ] && cat R24_CHECK.txt
python3 $TD/round-25/tools/owner_bugs.py > OWNER_BUGS.txt 2>&1 || true
for f in $RD/*.mp4; do s=$(stat -f %z "$f"); echo "$(basename $f) $((s / 1048576)) MB $([ $s -le 15728640 ] && echo ok || echo OVER)"; done | tee $RD/SIZES.txt
# vertical run lateral knee gap (critic r24 secondary 3: median <= .25 m) and wall-run gait, r21 checker
{ echo "# wall-run stride / lateral knee gap (r21_checks.py W21)"; python3 $TD/r21_checks.py $RD 2>&1 | sed -n '/== W21/,/== S21/p' | grep -v "== S21"
  for n in w1_wallrun_tall_zip w2_wallrun_side_zip c_wallrun_perch; do [ -f $RD/${n}_telemetry.csv ] && python3 $TD/wall_check.py $RD/${n}_telemetry.csv $n; done
} > $RD/WALL.txt 2>&1; cat $RD/WALL.txt
