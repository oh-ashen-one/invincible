#!/bin/bash
# round 03: as-found "before" stills of the REBUILT integrated map (no preset in Saved config, content untouched by perf_apply), TSR 50 %
WT=/Users/midir/sm2-n1/perf
export SM2_PERF_ROUTE_SHOTS=20,28,38,42
export SM2_PERF_STILL_TWICE=1
$WT/tools/perf_ue2/stills2.sh /Users/midir/sm2-n1/_scratch/perf/r03/before "before50@50" "S1 S2 S7 route"
