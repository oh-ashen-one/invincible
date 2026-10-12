#!/bin/bash
# island r01 hold B (inside one GPU-slot hold): ISM collision verification (r1, r4 telemetry-only) + r3 take 2 movie
export ISLAND_IN_LOCK=1
cd "$(dirname "$0")/../../.."
docs/night1/island/verify_map.sh /Game/Maps/Manhattan_WP_ism /Users/midir/sm2-n1/_scratch/island/verify_ism r1 r4 > /Users/midir/sm2-n1/_scratch/island/logs/verify_ism.log 2>&1
docs/night1/island/capture_round.sh docs/night1/island/round-01 r3 > /Users/midir/sm2-n1/_scratch/island/logs/capture_r01e.log 2>&1
