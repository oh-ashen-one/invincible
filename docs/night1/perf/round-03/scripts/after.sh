#!/bin/bash
# round 03: stills of the SHIPPED path (preset from Config/Mac/MacEngine.ini, content = rebuilt + perf_apply rt_lite,cloud; no per-run cvars)
WT=/Users/midir/sm2-n1/perf
export SM2_PERF_ROUTE_SHOTS=20,28,38,42
$WT/tools/perf_ue2/stills2.sh /Users/midir/sm2-n1/_scratch/perf/r03/after "ship@ini" "S1 S2 S7 route"
