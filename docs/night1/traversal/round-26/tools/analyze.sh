#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r26 measurement pass on the captured round (CPU only):
#   R26_TARGETS.txt  targets 1-2 (r26_checks.py V1-V3, C1-C2 on w1; the same numbers on the other wall-run clips for reference)
#   ROPE_CHECK.txt   rope readability (rope_r25_check.py, a at 10 fps)       R25_GATES.txt  c perch gate + pawn run cadence
#   GAPS.txt / R24_CHECK.txt (T7 / T3 / T1 / T2 / T4)   WALL.txt (r21 W21 + wall_check)   FLIPS.txt (flip_check f4)   OWNER_BUGS.txt   SIZES.txt
set -u
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-26
cd $RD
{ echo "# Round 26 targets 1-2 (r26_checks.py; w1 window 0.95-3.58 s)"
  python3 $TD/r26_checks.py w1_wallrun_tall_zip_telemetry.csv w1_wallrun_tall_zip 0.95 3.58
  echo; echo "# r25 w1 telemetry, same checker (for comparison)"
  python3 $TD/r26_checks.py $TD/round-25/w1_wallrun_tall_zip_telemetry.csv r25_w1 0.95 3.58
  echo; echo "# other clips with a vertical wall run (whole wall window; reference only)"
  for n in c_wallrun_perch r1_roofrun_zip s1_high_swing; do [ -f ${n}_telemetry.csv ] && python3 $TD/r26_checks.py ${n}_telemetry.csv $n 0 99; done
} > R26_TARGETS.txt 2>&1; cat R26_TARGETS.txt
{ echo "# Round 26 rope readability (rope_r25_check.py, 10 fps, rendered 1080p movies)"
  for n in a_swing_chain m1_mouse_swing s1_high_swing; do [ -f $n.mp4 ] && python3 $TD/rope_r25_check.py $n.mp4 ${n}_telemetry.csv $n --out /Users/midir/sm2-n1/_scratch/traversal/r26/${n}_rope25.json; done
} > ROPE_CHECK.txt 2>&1; tail -30 ROPE_CHECK.txt
{ echo "# Round 26 gates (r25_checks.py on round-26)"; python3 $TD/r25_checks.py $RD
  echo "# pawn run cadence (cadence_r25.py, head-top FFT over 1.5-11 s)"; [ -f p1_pawn_run.mp4 ] && python3 $TD/cadence_r25.py p1_pawn_run.mp4 p1_pawn_run_telemetry.csv 1.5 11
} > R25_GATES.txt 2>&1; cat R25_GATES.txt
{ echo "# attach-to-attach gaps (<= 3.3 s)"
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
{ echo "# f4 flips (flip_check.py)"; [ -f f4_chain_flips_telemetry.csv ] && python3 $TD/flip_check.py f4_chain_flips_telemetry.csv f4_chain_flips; } > FLIPS.txt 2>&1; tail -20 FLIPS.txt
sed "s#round-{r}#round-{r}#; s#for r in ('24', '25')#for r in ('25', '26')#" $TD/round-25/tools/owner_bugs.py > /Users/midir/sm2-n1/_scratch/traversal/r26/owner_bugs26.py
python3 /Users/midir/sm2-n1/_scratch/traversal/r26/owner_bugs26.py > OWNER_BUGS.txt 2>&1 || true
for f in $RD/*.mp4; do s=$(stat -f %z "$f"); echo "$(basename $f) $((s / 1048576)) MB $([ $s -le 15728640 ] && echo ok || echo OVER)"; done | tee $RD/SIZES.txt
{ echo "# wall-run stride / lateral knee gap (r21_checks.py W21)"; python3 $TD/r21_checks.py $RD 2>&1 | sed -n '/== W21/,/== S21/p' | grep -v "== S21"
  for n in w1_wallrun_tall_zip w2_wallrun_side_zip c_wallrun_perch; do [ -f $RD/${n}_telemetry.csv ] && python3 $TD/wall_check.py $RD/${n}_telemetry.csv $n; done
} > $RD/WALL.txt 2>&1; cat $RD/WALL.txt
