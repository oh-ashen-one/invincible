#!/bin/bash
# Terrain r01 v3 pass: ONE slot hold: rebuild the terrain content (fixes found in the v1 / v2 stills), warm-up, all terrain stills again (baseline stills are kept). v2 stills are archived in stills_v2/.
#   gpu_slot.sh capture --label terrain --timeout 28800 -- docs/night1/terrain/turn4.sh
set -uo pipefail
export HOLD_START=$(date +%s)
HERE="$(cd "$(dirname "$0")" && pwd)"; ROUND="$HERE/round-01"; S=/Users/midir/sm2-n1/_scratch/terrain; M=$S/manhattan
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"; WT="$(cd "$HERE/../../.." && pwd)"
mkdir -p "$ROUND/stills_v2"; cp -p "$ROUND"/stills/*.jpg "$ROUND/stills_v2/" 2>/dev/null
cat > $S/jobs_terrain_v3.py <<PY
import os, traceback
import unreal
unreal.SystemLibrary.execute_console_command(None, 'Module Load StaticMeshEditor')
ns = {'__file__': '$WT/unreal/WebHomage/Scripts/build_terrain.py', '__name__': '__main__', 'JOB_ARGS': {'steps': 'clean,tex,mat,mesh,foliage,trees,map,views'}}
try: exec(compile(open(ns['__file__']).read(), ns['__file__'], 'exec'), ns)
except Exception: traceback.print_exc()
PY
echo "== v3 rebuild $(date +%H:%M:%S)"
SM2_TERRAIN_SCRATCH=$S "$UE" "$WT/unreal/WebHomage/WebHomage.uproject" -run=pythonscript -script=$S/jobs_terrain_v3.py -unattended -nullrhi -nosplash -RenderOffScreen -NoSound -NoCrashReports -abslog=$M/logs/terrain_v3.log
echo "== v3 rebuild done rc=$? $(date +%H:%M:%S)"
BASE_IDS="" "$HERE/capture_round.sh" "$ROUND" warm stills
