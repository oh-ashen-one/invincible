#!/bin/bash
# which lever moves the S1 / S2 crops? (each: shipped preset with ONE lever reverted toward the as-found look; stills only)
WT=/Users/midir/sm2-n1/perf; O=/Users/midir/sm2-n1/_scratch/perf/r03/lp
$WT/tools/perf_ue2/stills2.sh $O/t50 "t50@50" "S1 S2"
$WT/tools/perf_ue2/stills2.sh $O/gi1 "gi1@ini+r.Lumen.ScreenProbeGather.HardwareRayTracing=1" "S1 S2"
$WT/tools/perf_ue2/stills2.sh $O/mpe1 "mpe1@ini+r.Nanite.MaxPixelsPerEdge=1" "S1 S2"
$WT/tools/perf_ue2/stills2.sh $O/all "all@50+r.Lumen.ScreenProbeGather.HardwareRayTracing=1+r.Nanite.MaxPixelsPerEdge=1" "S1 S2"
