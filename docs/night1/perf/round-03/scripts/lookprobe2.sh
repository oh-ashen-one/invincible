#!/bin/bash
WT=/Users/midir/sm2-n1/perf; O=/Users/midir/sm2-n1/_scratch/perf/r03/lp
export SM2_PERF_STILL_TWICE=1   # new map copies: first launch of each may build DF / shaders
for V in A B C; do $WT/tools/perf_ue2/stills2.sh $O/rtv$V "rtv$V@ini+variant:RTv$V" "S1 S2"; done
