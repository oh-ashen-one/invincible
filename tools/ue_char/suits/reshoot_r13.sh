#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 13 SECOND hold (launcher run by the queued gpu_slot wrapper): the first hold's results were wrong in three ways found on its frames, all fixed on CPU before this one:
#   1. build_characters.py had put the lineup's -0.6 EV bias into new_stage() too: the Char_Hero / Char_Fight / Char_Crowd clips were 0.6 EV darker than r10 / r12 (the CH2 / CH7 colour-mask
#      instrument then picked the dark sky up) -> removed; the lineup keeps its bias (it is the only map that should);
#   2. the first still (Tessera front) was taken at 2.2 s while the 8192 px maps streamed in (a white mannequin) -> 3.7 s;
#   3. one silver rim for every suit lost the rim on mid / pale masks -> a per-suit FrameMaterial (C++ WHHeroSuitEntry, build_characters.py 'skins').
# It runs the whole round-13 chain again (build + stills + lineup + pawn + orbit + hero + chase + fight + crowd) from a snapshot of chain_r13.sh into <chain dir>/v2, but only when the marker
# <chain dir>/READY_V2 exists (written by hand after the CPU preparation is complete: a grant that arrives earlier releases the slot at once).
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 28800 -- bash tools/ue_char/suits/.reshoot_r13_run.sh <chain dir>
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:?chain dir}"
if [ ! -f "$OUT/READY_V2" ]; then echo "[r13 v2 launcher] $OUT/READY_V2 missing: CPU preparation not finished, releasing the slot"; exit 3; fi
cd "$WT"
mkdir -p "$OUT/v2"
EV=10.0 STEPS="build stills lineup pawn orbit hero chase fight crowd" exec bash "$WT/tools/ue_char/suits/.chain_r13b_run.sh" "$OUT/v2"
