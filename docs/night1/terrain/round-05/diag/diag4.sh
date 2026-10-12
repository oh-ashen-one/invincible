#!/bin/bash
# terrain r05 diagnostic 4: tree / lamp shadows on our lawn -- CSM in range (p10) vs VSM, VSM with larger non-Nanite allocations
set -uo pipefail
WT=/Users/midir/sm2-n1/terrain; UE_DIR=$WT/unreal/WebHomage; OUT=/Users/midir/sm2-n1/_scratch/terrain/r05/diag4
mkdir -p $OUT
export WH_CAPTURE_MAXFPS=6
run() { echo "== $1 $(date +%H:%M:%S)"; "$UE_DIR/Scripts/run_game.sh" "$OUT/$1" -map "$2" -res 1920x1080 -shots 2 -quit 3 -name "$1" -timeout 900 -exec "r.ScreenPercentage 100${3:+,$3}" -- -benchmark -fps=30 -notraceserver | tail -2; }
run p10_csm /Game/TerrainR5/Maps/V_p10_lawn_eye "r.Shadow.Virtual.Enable 0"
run p10_vsm /Game/TerrainR5/Maps/V_p10_lawn_eye ""
run p4_vsmbig /Game/TerrainR5/Maps/V_p4_greatlawn "r.Shadow.Virtual.NonNanite.CulledInstanceAllocationFactor 4,r.Shadow.Virtual.NonNanite.MaxCulledInstanceAllocationSize 268435456,r.Shadow.Virtual.NonNanite.UseHZB 0"
echo "diag4 done $(date +%H:%M:%S)"
