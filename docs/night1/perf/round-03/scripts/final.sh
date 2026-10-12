#!/bin/bash
# round 03 final captures of the SHIPPED path (preset perf60_hwl from Config/Mac/MacEngine.ini; content = rebuilt + perf_apply rt_lite,cloud; no per-run cvars)
WT=/Users/midir/sm2-n1/perf; O=/Users/midir/sm2-n1/_scratch/perf/r03
export SM2_PERF_ROUTE_SHOTS=20,28,38,42
$WT/tools/perf_ue2/stills2.sh $O/final "ship@ini" "S1 S2 S7 route"
while pgrep -f "MacOS/UnrealEditor .*sm2-n1/perf/unreal" > /dev/null; do sleep 3; done
$WT/tools/perf_ue2/route_movie.sh $O/movie "movie@100+set:perf60_hwl"
