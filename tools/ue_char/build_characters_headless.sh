#!/bin/bash
# Headless rebuild of /Game/Characters + /Game/Tests/Characters (P2 editor must be closed). Fan homage project.
#   tools/ue_char/build_characters_headless.sh ['{"steps":"mesh,citizens,abp,map"}']
cd "$(dirname "$0")/../.."
WT=$(pwd)
# idempotent: our folders are wiped on disk first (editor closed), then rebuilt from committed sources
case "$1" in ""|*clean*) rm -rf "$WT/unreal/WebHomage/Content/Characters" "$WT/unreal/WebHomage/Content/Tests/Characters";; esac
A="$1"; [ -z "$A" ] && A="{}"; export CHAR_BUILD_ARGS="$A"
# the key / id maps are duplicated from Char_Crowd: an existing copy cannot be deleted from inside the commandlet (DuplicateAsset fails), so remove the files first
case "$A" in *mapkey*) rm -f "$WT/unreal/WebHomage/Content/Tests/Characters/Char_CrowdKey.umap" "$WT/unreal/WebHomage/Content/Tests/Characters/Char_CrowdID.umap" "$WT/unreal/WebHomage/Content/Tests/Characters/Char_HeroKey.umap";; esac
export P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"   # derived inputs + caches (tools/ue_char/p2paths.py)
GPU_SLOT="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
"$WT/tools/ue_char/ue_wait.sh"   # owner rule: never a 3rd+ Unreal instance
# owner rule (16:43 incident): every Unreal launch goes through the GPU lock, even a -nullrhi commandlet
"$GPU_SLOT" capture --label characters -- "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$WT/unreal/WebHomage/WebHomage.uproject" \
  -RenderOffScreen -NoSound -run=pythonscript -script="$WT/unreal/WebHomage/Scripts/build_characters.py" -unattended -nullrhi -nosplash \
  -abslog="$WT/unreal/WebHomage/Saved/Logs/characters_build.log" 2>&1 < /dev/null | grep -E "build_characters\]|Error|Traceback|gpu_slot" | grep -v LogInit | tail -40
