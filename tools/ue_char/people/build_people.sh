#!/bin/bash
# Street enemies (thug, brute, hood, tee, beard) for Unreal: raw Tripo people (~/sm2-assets/raw, the owner's assets, never committed) -> dress -> fit to the hero's
# 58-bone skeleton -> texture-free GLB for Interchange + 4096^2 base colour PNG. Idempotent; the (slow) skinfit step is cached on the
# SHA of the prepared mesh.   Fan homage project; not official Marvel/Sony/Insomniac.
#   tools/ue_char/people/build_people.sh [--force]
set -e
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"; export P2_SCRATCH   # tools/ue_char/p2paths.py
SCR="$P2_SCRATCH/r3"
GLB="$P2_SCRATCH/ueimport"
RAW="${P2_RAW:-$HOME/sm2-assets/raw}"
ART="$WT/art/night1/characters/people"
mkdir -p "$SCR/people" "$SCR/fit" "$GLB" "$ART"
for src in "leather+jacket+man+3d+model.glb" "human+character+3d+model.glb" "human+figure+3d+model.glb" "adult+male+3d+model.glb" "human+character+3d+model (3).glb" "baseball+cap+3d+model.glb"; do
  [ -f "$RAW/$src" ] || { echo "missing raw Tripo person: $RAW/$src" >&2; exit 1; }
done
pids=()
PEOPLE="thug brute hood tee beard"
for c in $PEOPLE; do
  C="Street$(python3 -c "print('$c'.capitalize())")"
  python3 "$WT/tools/ue_char/people/prepare_person.py" $c --out "$SCR/people" > "$SCR/people/$C.prep.log"
  sha=$(shasum "$SCR/people/${C}_prepared.glb" | cut -d' ' -f1)
  if [ "$1" = "--force" ] || [ ! -f "$SCR/fit/$C.glb" ] || [ "$(cat "$SCR/fit/$C.sha" 2>/dev/null)" != "$sha" ]; then
    ( python3 "$WT/tools/skinfit/skinfit.py" "$SCR/people/${C}_prepared.glb" "$SCR/fit/$C.glb" --name "$C" --spatial-smooth 0.035 --weld --report "$SCR/fit/$C.json" > "$SCR/fit/$C.log" 2>&1 && echo "$sha" > "$SCR/fit/$C.sha" ) &
    pids+=($!)
  fi
done
for p in "${pids[@]}"; do wait "$p"; done
for c in $PEOPLE; do
  C="Street$(python3 -c "print('$c'.capitalize())")"
  N="$(python3 -c "print('$c'.capitalize())")"
  [ -f "$SCR/fit/$C.glb" ] || { echo "skinfit failed for $C (see $SCR/fit/$C.log)" >&2; exit 1; }
  python3 "$WT/tools/ue_char/strip_glb.py" "$SCR/fit/$C.glb" "$GLB/SK_Street_$N.glb" > /dev/null
  cp "$SCR/people/${C}_atlas.png" "$ART/${c}_basecolor.png"
  for v in "$SCR/people/${C}"_*_atlas.png; do            # tint variants (same mesh): <c>_<Variant>_basecolor.png
    [ -f "$v" ] || continue
    t=$(basename "$v" _atlas.png); t=${t#${C}_}
    cp "$v" "$ART/${c}_${t}_basecolor.png"
  done
  # round 09: the thug's collar wedge = the skin of the nape between the hair line and the hood collar: darken those texels (final bind-pose mesh, see nape_fix.py)
  if [ "$c" = thug ]; then python3 "$WT/tools/ue_char/people/nape_fix.py" "$GLB/SK_Street_Thug.glb" "$ART/thug_basecolor.png" "$ART/thug_Oxblood_basecolor.png"; fi
done
# hand weapons (Blender headless, generic shapes) rigidly skinned into the right hand: SK_Street_<Person>_<Weapon>.glb
W="$SCR/weapons"; mkdir -p "$W"
if [ ! -f "$W/pistol.glb" ] || [ "$WT/tools/ue_char/weapons/make_weapons.py" -nt "$W/pistol.glb" ]; then
  /Applications/Blender.app/Contents/MacOS/Blender -b -P "$WT/tools/ue_char/weapons/make_weapons.py" -- "$W" > "$W/make.log" 2>&1
fi
for pw in Thug:bat Thug:pistol Brute:pipe Hood:pistol Tee:bat Beard:pipe; do
  N=${pw%%:*}; K=${pw##*:}; KC="$(python3 -c "print('$K'.capitalize())")"
  python3 "$WT/tools/ue_char/weapons/add_weapon.py" "$SCR/fit/Street$N.glb" "$W/$K.glb" "$SCR/fit/Street${N}_$KC.glb" > /dev/null
  python3 "$WT/tools/ue_char/strip_glb.py" "$SCR/fit/Street${N}_$KC.glb" "$GLB/SK_Street_${N}_$KC.glb" > /dev/null
done
# upright / heavy walk clips (numpy IK on the hero walk), appended to a copy of the thug fit; UE imports only the animations from it
python3 "$WT/tools/ue_char/people/make_walk.py" "$SCR/fit/StreetThug.glb" "$SCR/fit/walks.glb" > "$SCR/fit/walks.log"
python3 "$WT/tools/ue_char/strip_glb.py" "$SCR/fit/walks.glb" "$GLB/SK_Street_Walks.glb" > /dev/null
echo "people ok: $(ls "$GLB"/SK_Street_*.glb | wc -l) meshes, textures in $ART"
