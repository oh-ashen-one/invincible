#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Terrain r02 capture hold: ONE slot hold = warm-up (shader compile + shader sanity check), the nine terrain stills at 4K (shots.json, v3 shore cameras included), then the two movies with the hero hidden.
# The terrain content is rebuilt BEFORE the slot (nullrhi commandlet, no GPU): see HANDOFF.md "Rebuild recipe". Enqueue with:
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label terrain --timeout 28800 -- docs/night1/terrain/round2.sh
set -uo pipefail
# a rebuild of the terrain content (nullrhi commandlet, no GPU) may still be running when the ticket comes up: wait for it (it writes this sentinel), max 15 min
for _ in $(seq 1 180); do [ -e /Users/midir/sm2-n1/_scratch/terrain/BUILDING ] || break; sleep 5; done
export HOLD_START=$(date +%s)
HERE="$(cd "$(dirname "$0")" && pwd)"; ROUND="$HERE/${ROUND_NAME:-round-02}"   # ROUND_NAME=round-02b for a second pass that must not overwrite the first
mkdir -p "$ROUND/stills"
export BASE_IDS="" HIDE_HERO=1 WARM_QUIT="${WARM_QUIT:-20}" PRIO_IDS="${PRIO_IDS-p1_south p10_lawn_eye p2_reservoir p6_west_shore}"
"$HERE/capture_round.sh" "$ROUND" warm stills moves
