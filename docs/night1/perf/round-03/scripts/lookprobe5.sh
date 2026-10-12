#!/bin/bash
WT=/Users/midir/sm2-n1/perf; O=/Users/midir/sm2-n1/_scratch/perf/r03/lp
export SM2_PERF_ROUTE_SHOTS=20,42
$WT/tools/perf_ue2/stills2.sh $O/hwC "hwC@ini+variant:RTvC" "S1 route"
