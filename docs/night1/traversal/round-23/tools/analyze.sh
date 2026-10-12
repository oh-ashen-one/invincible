#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r23 measurement pass on the captured round (CPU only): r23 director tests, r22 gates vs round 22, shot list, sizes.
set -u
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-23
cd /Users/midir/sm2-n1/traversal
python3 $TD/r23_checks.py $RD --sheets $RD/sheets > /dev/null; cat $RD/R23_CHECK.txt
python3 $TD/r22_checks.py $RD --sheets $RD/sheets --prev $TD/round-22 > $RD/R22_GATES.txt 2>&1; cat $RD/R22_GATES.txt
for f in $RD/*.mp4; do s=$(stat -f %z "$f"); echo "$(basename $f) $((s / 1048576)) MB $([ $s -le 15728640 ] && echo ok || echo OVER)"; done | tee $RD/SIZES.txt
python3 $TD/make_shotlist.py $RD "round 23" "$(git rev-parse --short HEAD)" > /dev/null 2>&1 && echo "shotlist ok"
