#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r22 hold B (inside one gpu_slot capture hold): tower-route probes (-nullrhi) -> pick_tower.py -> w1 / w2 scripts on the sunlit
# tower face (x ~-228) -> captures of w2 / w1 (when picked) and SEQS_B with the GO args of hold A
R=/Users/midir/sm2-n1/_scratch/traversal/r22
UE=/Users/midir/sm2-n1/traversal/unreal/WebHomage
SC=/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city
RD=/Users/midir/sm2-n1/traversal/docs/night1/traversal/round-22
OUT=$R/probe
while [ -e $R/BUILDING ]; do sleep 5; done
probe() { local n=$1 j=$2 q=$3; shift 3; rm -rf "$OUT/$n"; mkdir -p "$OUT/$n"
  "$UE/Scripts/run_game.sh" "$OUT/$n" -map /Game/Maps/Manhattan -res 1920x1080 -quit $q -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 \
     -WHTravScript="$j" -WHTravCsv="$OUT/$n/${n}_telemetry.csv" "$@" | tail -1; }
echo "== tower probes $(date +%T)"
for n in t2_a t2_b t2_c t2_d; do probe $n $R/scripts/$n.json 6.5; done
for n in t1_a t1_b; do probe $n $R/scripts/$n.json 7.5; done
python3 $R/pick_tower.py $OUT t2_a t2_b t2_c t2_d -- t1_a t1_b | tee $R/pick_tower.txt
WALL=""
if [ -s $OUT/PICK_T2 ]; then
  python3 - "$(cat $OUT/PICK_T2)" "$(cat $OUT/PICK_T1 2>/dev/null)" <<'PY'
import json, sys
R = '/Users/midir/sm2-n1/_scratch/traversal/r22'; SC = '/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city'
w2 = json.load(open(f'{R}/scripts/{sys.argv[1]}.json')); w2['name'] = 'w2_wallrun_side_zip'
w2['note'] = ('Round 22 (director: side run on a sun-facing facade): the west face of the 284 m tower at x ~-228 (y -62..-43; the only long west face '
              'whose sun line clears the hinterland at the 8 deg golden-hour sun: lit above ~48 m). Jump from the west avenue onto the face, '
              f'vertical wall run up, stick sideways + sprint at {w2["keys"][2]["t"]} s (upright side run), E at {w2["keys"][3]["t"]} s -> zip. Variant {sys.argv[1]}.')
json.dump(w2, open(f'{SC}/w2_wallrun_side_zip.json', 'w'), indent=1)
if len(sys.argv) > 2 and sys.argv[2]:
    w1 = json.load(open(f'{R}/scripts/{sys.argv[2]}.json')); w1['name'] = 'w1_wallrun_tall_zip'
    w1['note'] = (f'Round 22: w1 on the sunlit 284 m tower west face (x ~-228): jump onto the face, vertical wall run, E at {w1["keys"][2]["t"]} s -> zip up -> perch, '
                  f'E on the perch at {w1["keys"][5]["t"]} s. Variant {sys.argv[2]}.')
    json.dump(w1, open(f'{SC}/w1_wallrun_tall_zip.json', 'w'), indent=1)
PY
  WALL="w2_wallrun_side_zip"; [ -s $OUT/PICK_T1 ] && WALL="$WALL w1_wallrun_tall_zip"
fi
GOARGS=$(cat $R/GO 2>/dev/null)
cd /Users/midir/sm2-n1/traversal
echo "== hold B captures $(date +%T) with [$GOARGS]: $WALL $(cat $R/SEQS_B)"
[ -n "$WALL" ] && GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 W1Q=8.5 EXTRA_ARGS="$GOARGS" docs/night1/traversal/capture_round.sh $RD/tower $WALL
GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 EXTRA_ARGS="$GOARGS" docs/night1/traversal/capture_round.sh $RD $(cat $R/SEQS_B)
echo "== hold B extra: tower retime probes $(date +%T) (t2_c hit the recessed core face in the notch and wrapped the corner)"
rm -f $OUT/PICK_T2 $OUT/PICK_T1
for n in t2_e t2_f t2_g t2_h; do probe $n $R/scripts/$n.json 6.5 $GOARGS; done
python3 $R/pick_tower2.py $OUT t2_e t2_f t2_g t2_h -- | tee $R/pick_tower2.txt
if [ -s $OUT/PICK_T2 ]; then
  python3 - "$(cat $OUT/PICK_T2)" <<'PY'
import json, sys
R = '/Users/midir/sm2-n1/_scratch/traversal/r22'; SC = '/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city'
w2 = json.load(open(f'{R}/scripts/{sys.argv[1]}.json')); w2['name'] = 'w2_wallrun_side_zip'
w2['note'] = ('Round 22 (director: side run on a sun-facing facade): the west face of the 284 m tower at x ~-229.4 (y -61..-42; the only long west face '
              'whose sun line clears the hinterland at the 8 deg golden-hour sun: lit above ~48 m). Jump from the west avenue onto the face, '
              f'vertical wall run up, stick sideways + sprint at {w2["keys"][2]["t"]} s (upright side run north, ends before the fin at y -40), '
              f'E at {w2["keys"][3]["t"]} s -> zip. Variant {sys.argv[1]}.')
json.dump(w2, open(f'{SC}/w2_wallrun_side_zip.json', 'w'), indent=1)
PY
  GPU_OUTER=1 NO_STILLS=1 SKIP_WARM=1 EXTRA_ARGS="$GOARGS" docs/night1/traversal/capture_round.sh $RD/tower2 w2_wallrun_side_zip
fi
echo "== hold B done $(date +%T)"
exit 0
