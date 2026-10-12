#!/bin/bash
WT=/Users/midir/sm2-n1/perf; O=/Users/midir/sm2-n1/_scratch/perf/r03/lp
GI="r.Lumen.ScreenProbeGather.HardwareRayTracing=1"
$WT/tools/perf_ue2/stills2.sh $O/gi50m8 "gi50m8@50+$GI+r.Nanite.MaxPixelsPerEdge=8" "S1 S2"
$WT/tools/perf_ue2/stills2.sh $O/gi48m8 "gi48m8@ini+$GI+r.Nanite.MaxPixelsPerEdge=8" "S1 S2"
$WT/tools/perf_ue2/stills2.sh $O/gi50 "gi50@50+$GI" "S1 S2"
