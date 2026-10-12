#!/bin/bash
# tricks r01 hold b: (my previous engine must be gone) rebuild C++ (dump window), fit the last turn key, render window 0
cd /Users/midir/sm2-n1/tricks
while pgrep -f "[/]Users/midir/sm2-n1/tricks/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 5; done
unreal/WebHomage/Scripts/build_editor.sh > /Users/midir/sm2-n1/_scratch/tricks/build_cpp.log 2>&1; grep -E " error|Result:" /Users/midir/sm2-n1/_scratch/tricks/build_cpp.log | head -5
W=/Users/midir/sm2-n1/_scratch/tricks/route; mkdir -p $W
FIXED_KEYS=12.63:90,29.97:180 python3 tools/tricks/auto_route.py docs/night1/tricks/scripts/t60_trick_reel.json $W/t60_fitted.json $W 2>&1 | grep -v "^run_game\|WH_QUIT"
cp $W/t60_fitted.json docs/night1/tricks/scripts/t60_trick_reel.json
NOHOLD=1 SEGS="0:25,25:42.5,42.5:60.5" SEG_ONLY=1 tools/tricks/capture.sh docs/night1/tricks/round-01 t60_trick_reel
