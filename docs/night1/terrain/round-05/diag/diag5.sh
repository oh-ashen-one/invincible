#!/bin/bash
# terrain r05 diagnostic 5 (after the final holds): is the sun's shadow path ray traced for the leaf pools (out of the RT scene)? 1080p V_p4, final content
set -uo pipefail
WT=/Users/midir/sm2-n1/terrain; UE_DIR=$WT/unreal/WebHomage; OUT=/Users/midir/sm2-n1/_scratch/terrain/r05/diag5
mkdir -p $OUT
export WH_CAPTURE_MAXFPS=6
run() { echo "== $1 $(date +%H:%M:%S)"; "$UE_DIR/Scripts/run_game.sh" "$OUT/$1" -map "$2" -res 1920x1080 -shots 2 -quit 3 -name "$1" -timeout 900 -exec "r.ScreenPercentage 100${3:+,$3}" -- -benchmark -fps=30 -notraceserver | tail -2; }
run p4_def /Game/TerrainR5/Maps/V_p4_greatlawn ""
run p4_nomega /Game/TerrainR5/Maps/V_p4_greatlawn "r.MegaLights.EnableForProject 0,r.MegaLights.Allowed 0"
run p4_coarse /Game/TerrainR5/Maps/V_p4_greatlawn "r.Shadow.Virtual.NonNanite.IncludeInCoarsePages 1,r.Shadow.Virtual.NonNanite.UseRadiusThreshold 0,r.Shadow.RadiusThreshold 0"
echo "diag5 done $(date +%H:%M:%S)"
