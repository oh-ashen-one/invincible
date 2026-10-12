#!/bin/bash
# tricks r01 hold c: route search for the 25-60 s continuation; then window 1 if the 40-min hold still has >= 26 min left
cd /Users/midir/sm2-n1/tricks
T0=$(date +%s)
while pgrep -f "[/]Users/midir/sm2-n1/tricks/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 5; done
W=/Users/midir/sm2-n1/_scratch/tricks/search; mkdir -p $W
python3 tools/tricks/route_search.py docs/night1/tricks/scripts/t60_trick_reel.json $W/best.json $W
cp $W/best.json docs/night1/tricks/scripts/t60_trick_reel.json
EL=$(( $(date +%s) - T0 )); echo "search took $EL s"
if [ $EL -lt 840 ]; then /Users/midir/sm2-n1/_scratch/tricks/hold_seg.sh; else echo "window 1 left for the next hold"; fi
