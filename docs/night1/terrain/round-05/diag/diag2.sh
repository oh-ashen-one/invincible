#!/bin/bash
# terrain r05 diagnostic hold: why the trees cast no visible lawn shadow (1080p stills of V_p4 on the r04 content, console variants)
set -uo pipefail
WT=/Users/midir/sm2-n1/terrain; UE_DIR=$WT/unreal/WebHomage; OUT=/Users/midir/sm2-n1/_scratch/terrain/r05/diag
ROOT="${ROOT:-/Game/TerrainR4}"
mkdir -p $OUT
export WH_CAPTURE_MAXFPS=6
run() { # name map exec
  echo "== $1 $(date +%H:%M:%S)"
  "$UE_DIR/Scripts/run_game.sh" "$OUT/$1" -map "$2" -res 1920x1080 -shots 2 -quit 3 -name "$1" -timeout 900 -exec "r.ScreenPercentage 100${3:+,$3}" -- -benchmark -fps=30 | tail -2
  rc=$?; [ -e $OUT/STOP ] && exit 9
}
for V in ${VARIANTS:-nodirect nolumen}; do
  case $V in
    nodirect) run p4_nodirect $ROOT/Maps/V_p4_greatlawn "ShowFlag.DirectLighting 0";;
    nolumen) run p4_nolumen $ROOT/Maps/V_p4_greatlawn "r.Lumen.DiffuseIndirect.Allow 0";;
    def) run p4_def $ROOT/Maps/V_p4_greatlawn "";;
    noshadow) run p4_noshadow $ROOT/Maps/V_p4_greatlawn "ShowFlag.DynamicShadows 0";;
    nogi) run p4_nogi $ROOT/Maps/V_p4_greatlawn "r.DynamicGlobalIlluminationMethod 0";;
    nogi_p10) run p10_nogi $ROOT/Maps/V_p10_lawn_eye "r.DynamicGlobalIlluminationMethod 0";;
  esac
done
echo "diag done $(date +%H:%M:%S)"
