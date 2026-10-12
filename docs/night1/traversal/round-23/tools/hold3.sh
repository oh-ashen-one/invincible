#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r23 hold 3: captures the clips hold2's time guard left ($R/LEFT), compiled defaults, after hold2 has finished (one engine per agent).
R=/Users/midir/sm2-n1/_scratch/traversal/r23
TD=/Users/midir/sm2-n1/traversal/docs/night1/traversal
RD=$TD/round-23
START=$(date +%s)
el() { echo $(( $(date +%s) - START )); }
echo "== hold3 acquired $(date +%T)"
while [ -f $R/hold2.running ] && kill -0 "$(cat $R/hold2.running 2>/dev/null)" 2>/dev/null; do sleep 10; done
pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" >/dev/null && { echo "== own engine still running: wait"; sleep 60; }
[ -s $R/LEFT ] || { echo "== nothing left $(date +%T)"; exit 0; }
cd /Users/midir/sm2-n1/traversal
for s in $(cat $R/LEFT); do
  if [ $(el) -gt 2150 ]; then echo "== time guard: $s still left"; echo $s >> $R/LEFT3; continue; fi
  echo "== capture $s at $(el) s"
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 docs/night1/traversal/capture_round.sh $RD $s 2>&1 | tail -3
done
echo "== hold 3 done $(date +%T)"
exit 0
