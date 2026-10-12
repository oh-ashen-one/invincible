#!/bin/bash
# Round 09: partial headless rebuild for the choreographed fight (no wipe of /Game/Characters; the editor must be closed).
# Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.
#   tools/ue_char/fight/build_fight.sh [steps]      default steps: fightclips,abp,maps5   (python3 tools/ue_char/fight/make_fight_clips.py and choreo.py run first)
#   full round-09 rebuild: tools/ue_char/fight/build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,mapkey,mapavoid
# One engine, through the GPU lock (-nullrhi commandlet); the log goes to Saved/Logs/characters_build.log, stdout of this script is the lock's own line only.
set -u
cd "$(dirname "$0")/../../.."
WT=$(pwd)
export P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"
STEPS="${1:-fightclips,abp,maps5}"
export CHAR_BUILD_ARGS="{\"steps\":\"$STEPS\"}"
# 'clean' = the committed idempotent rebuild: our two content folders are wiped on disk first (editor closed), exactly like build_characters_headless.sh
case "$STEPS" in *clean*)
  for d in "$WT/unreal/WebHomage/Content/Characters" "$WT/unreal/WebHomage/Content/Tests/Characters"; do
    case "$d" in "$WT"/unreal/WebHomage/Content/*) rm -rf "$d";; *) echo "refusing to delete $d"; exit 1;; esac
  done ;;
esac
case "$STEPS" in *mapkey*) rm -f "$WT/unreal/WebHomage/Content/Tests/Characters/Char_CrowdKey.umap" "$WT/unreal/WebHomage/Content/Tests/Characters/Char_CrowdID.umap" "$WT/unreal/WebHomage/Content/Tests/Characters/Char_HeroKey.umap";; esac
GPU_SLOT="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
"$GPU_SLOT" capture --label characters -- "$UE" "$WT/unreal/WebHomage/WebHomage.uproject" -RenderOffScreen -NoSound -run=pythonscript \
  -script="$WT/unreal/WebHomage/Scripts/build_characters.py" -unattended -nullrhi -nosplash -abslog="$WT/unreal/WebHomage/Saved/Logs/characters_build.log" > "${BUILD_STDOUT:-/dev/null}" 2>&1 < /dev/null
echo "build_fight exit=$?"
grep -E "build_characters\]|Error:|Traceback" "$WT/unreal/WebHomage/Saved/Logs/characters_build.log" | grep -v LogInit | tail -40
