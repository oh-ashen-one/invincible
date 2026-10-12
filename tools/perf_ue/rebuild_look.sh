#!/bin/zsh
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Headless rebuild of /Game/Look + /Game/Tests/Look (Scripts/build_look.py) with your editor CLOSED.
# usage: tools/perf_ue/rebuild_look.sh [steps=geo,rigs,night,maps] [presets=midday,golden,night]
# needs the city content (tools/perf_ue/rebuild_city.sh) and, for the traversal hero, Scripts/build_traversal.py once.
# DEPENDENCY: step `geo` (traversal building boxes + WorldDynamic patch of the city geometry level) must run after EVERY city build (Scripts/build_city.py):
#   rebuild_city.sh does it for you; capture_looks.py / run_perf.py call tools/perf_ue/ensure_boxes.py, which re-runs `geo` when Look_Boxes.umap is older than City_Midtown_Geo.umap.
# Env: SM2_LOOK_SCRATCH (scratch root, default /Users/midir/sm2-n1/_scratch/look; the city export is <scratch>/export/midtown3x3), SM2_CITY_EXPORT (override the export dir), SM2_LOOK_LOG.
WT="$(cd "$(dirname "$0")/../.." && pwd)"
export SM2_LOOK_SCRATCH=${SM2_LOOK_SCRATCH:-/Users/midir/sm2-n1/_scratch/look}
export SM2_LOOK_WORKTREE="$WT"
export SM2_CITY_EXPORT=${SM2_CITY_EXPORT:-$SM2_LOOK_SCRATCH/export/midtown3x3}
export SM2_LOOK_STEPS=${1:-geo,rigs,night,maps}; export SM2_LOOK_PRESETS=${2:-midday,golden,night}
LOG=${SM2_LOOK_LOG:-$SM2_LOOK_SCRATCH/build_look_headless.log}
mkdir -p "$SM2_LOOK_SCRATCH"
cd "$WT/unreal/WebHomage"
# RULES (2026-09-29 16:43): every Unreal launch goes through the GPU slot, at most 2 Unreal processes across all agents; -nullrhi = no GPU use
GS=${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}; [ -x "$GS" ] && SLOT=("$GS" capture --label look --) || SLOT=()
"${SLOT[@]}" "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$PWD/WebHomage.uproject" -run=pythonscript \
  -script="$PWD/Scripts/build_look.py" -unattended -nullrhi -NoCrashReports -abslog="$LOG" > "$LOG.stdout" 2>&1
grep -E "LogPython: \[build_look|LogPython: (Error|Warning)|    [A-Za-z_.]+ \(" "$LOG" | grep -v Deprecat | sed 's/^.*LogPython: //' | tail -40
