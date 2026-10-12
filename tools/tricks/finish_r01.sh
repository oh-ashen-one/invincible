#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C r01: after the 4 reel windows merged (capture.sh): stitch the telemetry by window (pixel columns valid everywhere), run the
# SPEC checker into round-01/CHECK.txt, then build the blind critic pack (owner-clip pairs stay in _scratch, never committed).
set -euo pipefail
cd "$(dirname "$0")/../.."
R=docs/night1/tricks/round-01
C=/Users/midir/sm2-n1/_scratch/tricks/capture/t60_trick_reel
SEGS="0:15,15:30,30:45,45:60.5"
python3 tools/tricks/stitch_telemetry.py $C t60_trick_reel "$SEGS" $R/t60_trick_reel_telemetry.csv
gunzip -c $R/t60_trick_reel_pose.csv.gz > /Users/midir/sm2-n1/_scratch/tricks/final_pose.csv
python3 tools/tricks/tricks_check.py $R/t60_trick_reel_telemetry.csv /Users/midir/sm2-n1/_scratch/tricks/final_pose.csv > $R/CHECK.txt
ffprobe -v error -show_entries stream=width,height,r_frame_rate,nb_frames:format=duration,size -of default=nw=1 $R/t60_trick_reel.mp4 >> $R/CHECK.txt
grep -E "^(P|V1|V2|K|L|G1|G2|G3|G4) " $R/CHECK.txt | grep -E "PASS|FAIL"
