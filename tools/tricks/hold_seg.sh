#!/bin/bash
# tricks r01: render the first reel window that has no frames yet (one engine run inside the caller's hold); no-op when all exist
cd /Users/midir/sm2-n1/tricks
while pgrep -f "[/]Users/midir/sm2-n1/tricks/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 5; done
C=/Users/midir/sm2-n1/_scratch/tricks/capture/t60_trick_reel
for K in 1 2; do
  if [ ! -d "$C/seg$K/t60_trick_reel_frames" ] || [ "$(ls "$C/seg$K/t60_trick_reel_frames" | wc -l)" -lt 900 ]; then
    NOHOLD=1 SEGS="0:25,25:42.5,42.5:60.5" SEG_ONLY=$K tools/tricks/capture.sh docs/night1/tricks/round-01 t60_trick_reel
    exit 0
  fi
done
echo "all reel windows rendered"
