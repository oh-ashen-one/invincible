#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r24 measurement pass on the captured round (CPU only): r24 tests (T7/T3/T1/T2/T4 on a, c camera gate), drop test >= 20 m,
# rhythm check, r23 director tests (V23 / X23 / T22 / Z23), r22 gates vs round 23, owner-bug numbers, sizes, shot list.
set -u
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-24
cd /Users/midir/sm2-n1/traversal
python3 $TD/r24_checks.py $RD --rendered > /dev/null; cat $RD/R24_CHECK.txt
{ echo "== drop_test.py --min 20 (first swing = the spawn drop, listed; --skip-first below)"; python3 $TD/drop_test.py $RD/a_swing_chain_telemetry.csv --min 20;
  python3 $TD/drop_test.py $RD/a_swing_chain_telemetry.csv --min 20 --skip-first | tail -1;
  echo "== rhythm_check.py a"; python3 $TD/rhythm_check.py $RD/a_swing_chain_telemetry.csv; } > $RD/DROP_RHYTHM.txt 2>&1; cat $RD/DROP_RHYTHM.txt
python3 $TD/r23_checks.py $RD --sheets $RD/sheets > /dev/null; cp $RD/R23_CHECK.txt $RD/R23_GATES.txt 2>/dev/null; cat $RD/R23_CHECK.txt
python3 $TD/r22_checks.py $RD --sheets $RD/sheets --prev $TD/round-23 > $RD/R22_GATES.txt 2>&1; grep -E "PASS|FAIL|BIT" $RD/R22_GATES.txt
python3 $TD/round-24/tools/owner_bugs.py > $RD/OWNER_BUGS.txt; cat $RD/OWNER_BUGS.txt
for f in $RD/*.mp4; do s=$(stat -f %z "$f"); echo "$(basename $f) $((s / 1048576)) MB $([ $s -le 15728640 ] && echo ok || echo OVER)"; done | tee $RD/SIZES.txt
python3 $TD/make_shotlist.py $RD "round 24" "$(git rev-parse --short HEAD)" > /dev/null 2>&1 && echo "shotlist ok"
