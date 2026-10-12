#!/bin/bash
# terrain r05 diagnostic 3: where does the lawn's shadow come from (1080p, r05 test content)
set -uo pipefail
WT=/Users/midir/sm2-n1/terrain; UE_DIR=$WT/unreal/WebHomage; OUT=/Users/midir/sm2-n1/_scratch/terrain/r05/diag3
mkdir -p $OUT
export WH_CAPTURE_MAXFPS=6
run() { echo "== $1 $(date +%H:%M:%S)"; "$UE_DIR/Scripts/run_game.sh" "$OUT/$1" -map "$2" -res 1920x1080 -shots 2 -quit 3 -name "$1" -timeout 900 -exec "r.ScreenPercentage 100${3:+,$3}" -- -benchmark -fps=30 -notraceserver | tail -2; }
run vb_p4 /Game/TerrainR5/Maps/VB_p4_greatlawn ""
run p4_csm /Game/TerrainR5/Maps/V_p4_greatlawn "r.Shadow.Virtual.Enable 0"
run p4_r5 /Game/TerrainR5/Maps/V_p4_greatlawn ""
echo "diag3 done $(date +%H:%M:%S)"
