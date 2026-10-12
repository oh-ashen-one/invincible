#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Terrain r03 capture hold: ONE slot hold = warm-up (shader compile + sanity check), the nine terrain stills at 4K (frame cap 8 fps, GPU ms per still), the two movies
# with the hero hidden, then the r02-vs-r03 GPU-ms pair (p1 / p10 on /Game/TerrainR2 = the round-02 scripts built side by side, then r03 again).
# Content is rebuilt BEFORE the slot (nullrhi commandlets, no GPU). Enqueue with:
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label terrain --timeout 28800 -- docs/night1/terrain/round3.sh
set -uo pipefail
S=/Users/midir/sm2-n1/_scratch/terrain   # BUILDING = one commandlet running, BUILDING_CHAIN = a chain of builds (terrain, then the r02 copy) not finished yet
for _ in $(seq 1 120); do [ -e $S/BUILDING ] || [ -e $S/BUILDING_CHAIN ] || break; sleep 5; done
if [ -e $S/BUILDING ] || [ -e $S/BUILDING_CHAIN ]; then echo "terrain content still building after 10 min: giving the slot back"; exit 5; fi
export HOLD_START=$(date +%s)
HERE="$(cd "$(dirname "$0")" && pwd)"; ROUND="$HERE/${ROUND_NAME:-round-03}"
mkdir -p "$ROUND/stills"
export BASE_IDS="" HIDE_HERO=1 WARM_QUIT="${WARM_QUIT:-20}" WH_CAPTURE_MAXFPS="${WH_CAPTURE_MAXFPS:-4}" PRIO_IDS="${PRIO_IDS-p1_south p10_lawn_eye p6_west_shore p7_east_shore p8_pier}"
"$HERE/capture_round.sh" "$ROUND" warm stills moves r2gpu
