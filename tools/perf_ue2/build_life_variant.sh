#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F (round 05): city life (P6 traffic + crowd) in THIS worktree for the "with traffic and crowd" perf runs, with P6's UNCHANGED build script.
#   1. derived inputs in F's scratch (never P6's): vehicles = tools/life/prep_vehicles.py (IP-clean atlas) -> _scratch/perf/life/vehicles;
#      citizens = a read-only copy of P6's Blender-exported citizen FBX + recolour PNGs (_scratch/life/citizens/fbx -> _scratch/perf/life/citizens/fbx),
#      the same staging pattern piece C uses for P2's characters; lanes / parked / walk / signals = the committed Scripts/life_data (not regenerated)
#   2. python3 Scripts/build_life.py --steps content,map with SM2_LIFE_SCR / SM2_LIFE_EXPORT pointing at F's scratch (/Game/Life, /Game/Tests/Life)
#   3. commandlet tools/perf_ue2/make_life_variant.py: /Game/PerfF/Life/Manhattan = /Game/Maps/Manhattan + /Game/Tests/Life/Life_Actors
# Editor and game of this worktree closed. Wrap in the GPU lock like every Unreal launch:
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label perf -- tools/perf_ue2/build_life_variant.sh
set -euo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"
case "$WT" in /Users/midir/sm2-n1/perf) ;; *) echo "not F's worktree: $WT"; exit 1;; esac
L=/Users/midir/sm2-n1/_scratch/perf/life
mkdir -p "$L/logs" "$L/citizens/fbx"
[ -d "$L/vehicles/glb" ] || python3 "$WT/tools/life/prep_vehicles.py" --out "$L/vehicles" > "$L/logs/prep_vehicles.log" 2>&1
[ "$(ls "$L/citizens/fbx" | wc -l)" -gt 20 ] || { rsync -a /Users/midir/sm2-n1/_scratch/life/citizens/fbx/ "$L/citizens/fbx/"; git -C /Users/midir/sm2-n1/life log -1 --format='%h %s' > "$L/CITIZENS_STAGED_FROM.txt"; }
SM2_LIFE_SCR="$L" SM2_LIFE_EXPORT=/Users/midir/sm2-n1/_scratch/perf/export/midtown3x3 python3 "$WT/unreal/WebHomage/Scripts/build_life.py" --steps content,map
UEBIN="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
"$UEBIN" "$WT/unreal/WebHomage/WebHomage.uproject" -run=pythonscript -script="$WT/tools/perf_ue2/make_life_variant.py" -unattended -nullrhi -nosplash -RenderOffScreen -NoSound -NoCrashReports \
  -abslog="$L/logs/make_life_variant.log" > "$L/logs/make_life_variant.stdout" 2>&1
grep -h '\[make_life_variant\]' "$L/logs/make_life_variant.log" | tail -1
