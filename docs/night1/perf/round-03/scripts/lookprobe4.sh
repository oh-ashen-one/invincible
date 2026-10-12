#!/bin/bash
WT=/Users/midir/sm2-n1/perf; O=/Users/midir/sm2-n1/_scratch/perf/r03/lp
export SM2_PERF_ROUTE_SHOTS=20,42
for V in D E F; do $WT/tools/perf_ue2/stills2.sh $O/rtv$V "rtv$V@ini+variant:RTv$V" "S1 route"; done
