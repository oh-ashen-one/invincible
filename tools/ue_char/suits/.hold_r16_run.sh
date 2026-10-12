#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 16 hold launcher (run by the queued gpu_slot wrapper): runs the whole round-14 chain (build + stills + lineup + pawn + orbit + hero + chase + fight + crowd) from a SNAPSHOT of
# chain_r15.sh, but only when the marker <chain dir>/READY_R16 exists (written by hand after the CPU preparation - hero GLB build check, textures, regression, checkers - is complete).
# A grant that arrives BEFORE the marker waits up to 4 minutes for it (the slot is held meanwhile; the hold limit is 2400 s and the chain needs ~1450 s), then releases the slot.
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 28800 -- bash tools/ue_char/suits/.hold_r16_run.sh <chain dir>
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:?chain dir}"
for i in $(seq 1 24); do [ -f "$OUT/READY_R16" ] && break; sleep 10; done
if [ ! -f "$OUT/READY_R16" ]; then echo "[r16 launcher] $OUT/READY_R16 missing after 4 min: CPU preparation not finished, releasing the slot"; exit 3; fi
cd "$WT"
mkdir -p "$OUT/run"
P2_FIRST_EXTRA="${P2_FIRST_EXTRA:-9.0}" EV=10.0 STEPS="${STEPS:-build stills lineup pawn orbit hero chase fight crowd}" exec bash "$WT/tools/ue_char/suits/.chain_r16_run.sh" "$OUT/run"
