#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# tricks r01 resume, hold d (inside ONE gpu_slot capture hold, max 40 min): rebuild the merged content, probe the reel (-nullrhi), then
# render reel windows while >= 22 min of the hold remain and the probe passed (RENDER_ANY=1: whenever the route is clean).
# BUILD=0 skips the content build; PROBE=0 reuses the last VERDICT.
cd /Users/midir/sm2-n1/tricks
T0=$(date +%s); LEFT() { echo $(( 2400 - ( $(date +%s) - T0 ) )); }
while pgrep -f "[/]Users/midir/sm2-n1/tricks/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 5; done
if [ "${BUILD:-1}" = 1 ]; then
  python3 tools/tricks/run_build.py "${STEPS:-city_prep,city_extra,city,traversal,characters,look,map}" 2>&1 | grep -E "=== step|all done|error|Error|failed" | tail -20
fi
W=/Users/midir/sm2-n1/_scratch/tricks/probe_d; mkdir -p $W
if [ "${PROBE:-1}" = 1 ]; then
  python3 tools/tricks/probe_reel.py docs/night1/tricks/scripts/t60_trick_reel.json $W/best.json $W
  cp $W/best.json docs/night1/tricks/scripts/t60_trick_reel.json
fi
cat $W/VERDICT 2>/dev/null
if [ "${RENDER:-1}" = 1 ] && grep -q "route OK" $W/VERDICT && { [ "${RENDER_ANY:-0}" = 1 ] || ! grep -q -E "fails .*(V1|L|K|G)" $W/VERDICT; }; then
  C=/Users/midir/sm2-n1/_scratch/tricks/capture/t60_trick_reel
  for K in 0 1 2 3; do
    if [ -f "$C/seg$K/DONE" ]; then continue; fi
    if [ "$(LEFT)" -lt 1320 ]; then echo "window $K left for the next hold ($(LEFT) s left)"; break; fi
    NOHOLD=1 SEGS="0:15,15:30,30:45,45:60.5" SEG_ONLY=$K EXTRA_ARGS="-WHTrickWarm=4" tools/tricks/capture.sh docs/night1/tricks/round-01 t60_trick_reel
    N=$(ls "$C/seg$K/t60_trick_reel_frames" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$N" -ge 850 ]; then touch "$C/seg$K/DONE"; else echo "window $K short ($N frames)"; break; fi
  done
else
  echo "no render this hold"
fi
echo "hold d end, $(LEFT) s left"
