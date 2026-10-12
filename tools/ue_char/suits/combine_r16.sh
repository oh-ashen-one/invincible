#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 16: one directory for post_r16.sh out of the round's holds (symlinks): stills + orbit from hold 3, pawn + lineups from hold 2, both chain logs.
#   bash tools/ue_char/suits/combine_r16.sh <hold-2 run dir> <hold-3 run dir> <out dir>
set -eu
H2="${1:?hold-2 run}"; H3="${2:?hold-3 run}"; O="${3:?out}"
mkdir -p "$O"
for d in stills orbit; do rm -f "$O/$d"; ln -s "$H3/$d" "$O/$d"; done
for d in pawn lineup lineup34; do rm -f "$O/$d"; ln -s "$H2/$d" "$O/$d"; done
cat "$H2/chain.log" "$H3/chain.log" > "$O/chain.log"
cat "$H2"/gpu_util_before_*.txt "$H3"/gpu_util_before_*.txt > "$O/gpu_util_before_all.txt" 2>/dev/null || true
for f in "$H3"/gpu_util_before_*.txt "$H2"/gpu_util_before_pawn.txt "$H2"/gpu_util_before_lineup*.txt; do [ -f "$f" ] && cp "$f" "$O/"; done
echo "combined: stills / orbit <- $H3, pawn / lineups <- $H2 -> $O"
