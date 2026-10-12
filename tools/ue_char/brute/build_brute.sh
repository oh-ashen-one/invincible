#!/bin/bash
# Brute base colour: (re)generate from the thug UV layout. Fan homage project; not official Marvel/Sony/Insomniac.
#   tools/ue_char/brute/build_brute.sh        -> public/assets/enemies/brute_basecolor.webp (browser), art/.../brute_basecolor.png + brute_regions.png (UE)
# needs art/night1/characters/thug/tex/thug_basecolor.png (tools/ue_char/extract_textures.py)
set -e
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"; export P2_SCRATCH   # tools/ue_char/p2paths.py
SCR="$P2_SCRATCH/r2"
mkdir -p "$SCR"
[ -f "$SCR/uvgeom.npz" ] || /Applications/Blender.app/Contents/MacOS/Blender -b -P "$WT/tools/ue_char/brute/uvgeom.py" -- "$WT/public/assets/thug.glb" "$SCR/uvgeom.npz" > "$SCR/uvgeom.log" 2>&1
python3 "$WT/tools/ue_char/brute/paint_brute.py" "$@"
