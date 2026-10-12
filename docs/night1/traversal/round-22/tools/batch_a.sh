#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r22 hold A (run INSIDE one gpu_slot capture hold): -nullrhi route probes -> auto pick (pick_route.py) -> w1 / w2 scripts
# -> wait <= 6 min for GO / NOGO (VARS lines "tag|extra args|names" = extra probes meanwhile) -> wall-clip captures (SEQS_A).
R=/Users/midir/sm2-n1/_scratch/traversal/r22
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SC=/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city
RD=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-22
OUT=$R/probe
mkdir -p $OUT $RD
probe() { # name json quit [extra args]
  local n=$1 j=$2 q=$3; shift 3
  rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$j" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" "$@" | tail -1
}
while [ -e $R/BUILDING ]; do sleep 5; done
echo "== probes $(date +%T)"
for n in $(cat $R/PROBES); do probe $n $R/scripts/$n.json 6.0; done
python3 $R/pick_route.py $OUT $(cat $R/PROBES) | tee $R/pick.txt
PICK=$(cat $OUT/PICK 2>/dev/null)
if [ -n "$PICK" ]; then
  python3 $R/make_final.py $PICK
  probe w1probe $R/scripts/w1probe.json 4.6
  python3 $R/make_final.py $PICK --w1 $OUT/w1probe/w1probe_telemetry.csv
  probe w2final $SC/w2_wallrun_side_zip.json 7.0
  probe w1final $SC/w1_wallrun_tall_zip.json 7.5
fi
touch $R/PROBES_DONE
echo "== probes done $(date +%T); waiting for GO / NOGO"
end=$(( $(date +%s) + ${GO_WAIT:-360} ))
while [ ! -e $R/GO ] && [ ! -e $R/NOGO ] && [ $(date +%s) -lt $end ]; do
  if [ -s $R/VARS ]; then
    mv $R/VARS $R/VARS.run
    while IFS='|' read -r tg xa names; do
      [ -z "$tg" ] && continue
      for n in $names; do j=$R/scripts/$n.json; [ -f $j ] || j=$SC/$n.json; probe ${n}_$tg $j 7.5 $xa; done
    done < $R/VARS.run
    touch $R/VARS_DONE
  fi
  sleep 3
done
[ -e $R/NOGO ] && { echo "NOGO"; exit 0; }
GOARGS=$(cat $R/GO 2>/dev/null)
SEQS=$(cat $R/SEQS_A)
echo "== captures $(date +%T) with [$GOARGS]: $SEQS"
cd /Users/midir/sm2-n1/traversal
GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 EXTRA_ARGS="$GOARGS" docs/night1/traversal/capture_round.sh $RD $SEQS
echo "== hold A done $(date +%T)"
exit 0
