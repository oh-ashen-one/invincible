#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Terrain content rebuild through the nullrhi commandlet (CPU only, no GPU lock needed, ~2-9 min): runs unreal/WebHomage/Scripts/build_terrain.py.
#   tools/terrain/run_build.sh [steps]      steps default: clean,tex,mat,mesh,foliage,trees,map,views
# r05: -notraceserver (the editor otherwise auto-starts UnrealTraceServer, a listener on 1981 / 1989). Launch it through the GPU lock: gpu_slot.sh capture --label terrain -- tools/terrain/run_build.sh
# Touches <scratch>/BUILDING while it runs (docs/night1/terrain/round2.sh waits for it). Run the offline checks first: tools/terrain/check_hlsl.py, tools/terrain/scw_check.py.
set -uo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"; S="${SM2_TERRAIN_SCRATCH:-/Users/midir/sm2-n1/_scratch/terrain}"; STEPS="${1:-clean,tex,mat,mesh,foliage,trees,map,views}"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
mkdir -p "$S/manhattan/logs"
cat > "$S/jobs_terrain_build.py" <<PY
import traceback
import unreal
unreal.SystemLibrary.execute_console_command(None, 'Module Load StaticMeshEditor')
ns = {'__file__': '$WT/unreal/WebHomage/Scripts/build_terrain.py', '__name__': '__main__', 'JOB_ARGS': {'steps': '$STEPS'}}
try: exec(compile(open(ns['__file__']).read(), ns['__file__'], 'exec'), ns)
except Exception: traceback.print_exc()
PY
touch "$S/BUILDING"; rm -f "$S/build.rc"
SM2_TERRAIN_SCRATCH="$S" "$UE" "$WT/unreal/WebHomage/WebHomage.uproject" -run=pythonscript -script="$S/jobs_terrain_build.py" -unattended -nullrhi -nosplash -RenderOffScreen -NoSound -NoCrashReports -notraceserver -abslog="$S/manhattan/logs/terrain_build.log"
echo "rc=$?" > "$S/build.rc"; rm -f "$S/BUILDING"; cat "$S/build.rc"; grep -a "build_terrain.*\(DONE\|FAILED\|WARN\)\|Traceback" "$S/manhattan/logs/terrain_build.log" | cut -c1-160
