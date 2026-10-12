#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 17: one directory for post_r17.sh out of the round's holds (symlinks): stills + both lineups from the stills hold, pawn / orbit / lineupx0 from hold E, hero / chase / fight / crowd from hold F.
#   bash tools/ue_char/suits/combine_r17.sh <stills hold run dir> <hold E run dir> <hold F run dir> <out dir>
set -eu
HS="${1:?stills hold run}"; HE="${2:?hold E run}"; HF="${3:?hold F run}"; O="${4:?out}"
mkdir -p "$O"
for d in stills lineup lineup34 lineupx; do [ -e "$HS/$d" ] && { rm -f "$O/$d"; ln -s "$HS/$d" "$O/$d"; }; done
for d in pawn orbit lineupx0; do [ -e "$HE/$d" ] && { rm -f "$O/$d"; ln -s "$HE/$d" "$O/$d"; }; done
for d in hero chase fight crowd; do [ -e "$HF/$d" ] && { rm -f "$O/$d"; ln -s "$HF/$d" "$O/$d"; }; done
cat "$HS/chain.log" "$HE/chain.log" "$HF/chain.log" > "$O/chain.log" 2>/dev/null || true
for f in "$HS"/gpu_util_before_*.txt "$HE"/gpu_util_before_*.txt "$HF"/gpu_util_before_*.txt; do [ -f "$f" ] && cp "$f" "$O/"; done
cat "$O"/gpu_util_before_*.txt > "$O/gpu_util_before_all.txt" 2>/dev/null || true
echo "combined: stills / lineups <- $HS, pawn / orbit <- $HE, hero / chase / fight / crowd <- $HF -> $O"
