#!/bin/zsh
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 10: rebuild the lit city in THIS worktree from the committed P1 / P4 scripts, on P3's own dev port (5204) and scratch.
#   1. vite :5204 -> tools/export/export_city.mjs -> $S/export/midtown3x3 (manifest texture URLs rewritten 5204 -> 5202: the
#      P1 scripts split URLs on '5202/'), patch_export, prep_textures, street signs, street kit, street props, gen_shaders
#      (steps 1 are run by hand / SKIP_EXPORT=1 skips them)
#   2. headless commandlets (editor closed, waits while 3+ Unreal run): build_traversal.py (hero), build_city.py
#      (SM2_CITY_EXPORT / SM2_CITY_TEX -> P3 scratch), build_look.py geo,rigs,maps for the golden preset -> Look_Midtown_golden
# usage: docs/night1/traversal/city/build_city_p3.sh [steps]   steps: export,trav,city,look (default all)
set -e
WT="$(cd "$(dirname "$0")/../../../.." && pwd)"; cd "$WT"
S=/Users/midir/sm2-n1/_scratch/traversal/city; E=$S/export/midtown3x3; mkdir -p $S
STEPS=${1:-export,trav,city,look}
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
P="$WT/unreal/WebHomage/WebHomage.uproject"
wait_slot() { while [ "$(pgrep -f 'MacOS/UnrealEditor( |$)' | wc -l)" -ge 3 ]; do echo "$(date +%T) waiting: 3+ Unreal instances"; sleep 60; done; }
cmdlet() { wait_slot; echo "$(date +%T) commandlet $1"; "$UE" "$P" -run=pythonscript -script="$2" -unattended -nullrhi \
  -NoCrashReports -NoSound -abslog="$S/$1.log" > "$S/$1.stdout" 2>&1 || echo "  rc=$?"; grep -E "LogPython: \[build|LogPython: Error|Traceback" "$S/$1.log" | tail -8; }
if [[ $STEPS == *export* ]]; then
  [ -d node_modules ] || npm ci
  curl -s -o /dev/null http://127.0.0.1:5204/ || { (nohup npx vite --port 5204 --host 127.0.0.1 --strictPort > $S/vite.log 2>&1 &); sleep 5; }
  node tools/export/export_city.mjs --url http://127.0.0.1:5204/ --out $E --profile $S/chrome-profile
  sed -i '' 's#127.0.0.1:5204/#127.0.0.1:5202/#g' $E/manifest.json
  python3 tools/export/patch_export.py $E/
  python3 tools/export/prep_textures.py $S/tex $E/manifest.json
  python3 tools/export/gen_street_signs.py $S/tex/street_signs.png
  python3 tools/export/street_kit.py $E/
  python3 tools/export/street_props.py $E/
  node tools/export/gen_shaders.mjs
  pkill -f "vite --port 5204" || true
fi
export SM2_CITY_EXPORT=$E SM2_CITY_TEX=$S/tex SM2_LOOK_STEPS=geo,rigs,maps SM2_LOOK_PRESETS=${LOOK_PRESETS:-golden}
[[ $STEPS == *trav* ]] && cmdlet build_traversal.py "$WT/unreal/WebHomage/Scripts/build_traversal.py"
if [[ $STEPS == *city* ]]; then
  # build_city.py needs the editor (StaticMeshEditorSubsystem): P3's own editor, offscreen, runs the driver at startup
  wait_slot; LOG=$S/build_city_editor.log; rm -f $LOG; echo "$(date +%T) editor build_city"
  open -n "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app" --args "$P" -NoCrashReports -unattended -RenderOffScreen -NoSound \
    -abslog=$LOG "-ExecCmds=py $WT/docs/night1/traversal/city/run_build_city.py"
  for i in $(seq 1 240); do sleep 15; grep -q "ALL_PASSES_DONE\|LogPython: Error: Traceback" $LOG 2>/dev/null && break; done
  grep -E "LogPython: \[build|LogPython: Error" $LOG | tail -12
  pkill -9 -f "$P"; sleep 5
fi
[[ $STEPS == *look* ]] && cmdlet build_look.py "$WT/unreal/WebHomage/Scripts/build_look.py"
echo "$(date +%T) done"
