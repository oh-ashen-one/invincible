#!/bin/bash
# Terrain r01 turn 2: run under ONE gpu slot hold:
#   gpu_slot.sh capture --label terrain -- docs/night1/terrain/turn2.sh
# Optional rebuild first (only if /Users/midir/sm2-n1/_scratch/terrain/turn2_rebuild_steps exists: its content = build_terrain steps, e.g. "mat,mesh,foliage,trees,map,views"),
# then warm-up + all stills (terrain build V_*, baseline VB_* for the pair views).
set -uo pipefail
export HOLD_START=$(date +%s)
HERE="$(cd "$(dirname "$0")" && pwd)"; S=/Users/midir/sm2-n1/_scratch/terrain; M=$S/manhattan
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
WT="$(cd "$HERE/../../.." && pwd)"
if [ -f $S/turn2_rebuild_steps ]; then
  STEPS=$(cat $S/turn2_rebuild_steps)
  echo "== turn2: rebuild terrain steps=$STEPS $(date +%H:%M:%S)"
  cat > $S/jobs_terrain_only.py <<PY
import os, traceback
import unreal
unreal.SystemLibrary.execute_console_command(None, 'Module Load StaticMeshEditor')
ns = {'__file__': '$WT/unreal/WebHomage/Scripts/build_terrain.py', '__name__': '__main__', 'JOB_ARGS': {'steps': '$STEPS'}}
try: exec(compile(open(ns['__file__']).read(), ns['__file__'], 'exec'), ns)
except Exception: traceback.print_exc()
PY
  SM2_TERRAIN_SCRATCH=$S "$UE" "$WT/unreal/WebHomage/WebHomage.uproject" -run=pythonscript -script=$S/jobs_terrain_only.py -unattended -nullrhi -nosplash -RenderOffScreen -NoSound -NoCrashReports -abslog=$M/logs/terrain_turn2.log
  echo "== turn2: rebuild done rc=$? $(date +%H:%M:%S)"
fi
"$HERE/capture_round.sh" "$HERE/round-01" warm stills
