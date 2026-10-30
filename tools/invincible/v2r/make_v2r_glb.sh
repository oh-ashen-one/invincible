#!/bin/bash
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
#
# GLB for the in-game blind A/B of new hero clips: the v2 rig + ONLY the listed clips, for
# unreal/WebHomage/Scripts/import_invincible_v2r_anims.py (animations only, onto the shipped skeleton, into /Game/Invincible/HeroV2R/Anims).
# Thin wrapper around tools/invincible/merge_hero_clips.py (headless Blender; the rig glb is that script's first argument).
#
#   tools/invincible/v2r/make_v2r_glb.sh <out.glb> <clip.glb>:<ACTION>=A_<Clip> [...]
#   e.g. tools/invincible/v2r/make_v2r_glb.sh unreal/WebHomage/Saved/P2Build/invincible/SK_InvincibleV2R.glb \
#          Local/video2rig/hero/out-glb/Hover_v2r_v3.glb:Hover_v2r_v3=A_Hover Local/video2rig/hero/out-glb/LandHero_v2r_v2.glb:LandHero_v2r_v2=A_LandHero
#
# Every spec must rename to A_<Clip> with <Clip> one of the game's 12 (the importer maps A_<Clip> -> AS_<Clip>; the game looks up AS_<Clip>).
# After the merge the output's glTF animation names are checked against the specs (exactly the listed A_<Clip>, nothing else).
# Blender: one headless process (-b --factory-startup, no render); waits while 3 or more Blender processes run, or while any UnrealEditor
# runs and 1 Blender runs (same rule as run_clip.sh); 2-hour wait ceiling.
# env: V2R_BLENDER (default /Applications/Blender.app/Contents/MacOS/Blender), V2R_RIG_GLB (default the v2 rig below)
# Exit codes: 0 done (prints MAKE_V2R_GLB_OK), 2 usage, 3 merge / check failed, 4 no Blender slot within 2 h. bash 3.2 compatible.
set -u -o pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)                                   # repo root
B=${V2R_BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
RIG=${V2R_RIG_GLB:-$ROOT/docs/invincible/character/customuse/v2/rigged_hunyuanTex.glb}
MERGE=$ROOT/tools/invincible/merge_hero_clips.py
GAME_CLIPS=' Hover Fly LaunchUp BoostLaunch BoostHold Brake LandHero Takeoff GroundIdle PunchCombo Jab FlyingFistKick '

usage() { sed -n '7,10p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
[ $# -ge 2 ] || usage
OUT=$1; shift
case "$OUT" in *.glb) ;; *) echo "out must be a .glb: $OUT" >&2; exit 2 ;; esac
[ -f "$RIG" ] || { echo "rig glb missing: $RIG" >&2; exit 2; }
[ -x "$B" ] || { echo "Blender missing: $B" >&2; exit 2; }

WANT=''
for spec in "$@"; do
  path=${spec%:*}; act=${spec##*:}
  case "$act" in *=A_*) ;; *) echo "spec must end in :<ACTION>=A_<Clip>: $spec" >&2; exit 2 ;; esac
  clip=${act##*=A_}
  case "$GAME_CLIPS" in *" $clip "*) ;; *) echo "unknown game clip A_$clip in $spec (game clips:$GAME_CLIPS)" >&2; exit 2 ;; esac
  case " $WANT " in *" A_$clip "*) echo "A_$clip listed twice" >&2; exit 2 ;; esac
  [ -f "$path" ] || { echo "clip glb missing: $path" >&2; exit 2; }
  WANT="$WANT A_$clip"
done

waited=0
while true; do   # machine cap: 3 Blender, or 1 Blender once an UnrealEditor runs (count only; never touches other processes)
  nb=$(ps -axo comm= | grep -c '/MacOS/Blender$')
  ue=$(ps -axo comm= | grep -c 'UnrealEditor')
  if [ "$nb" -lt 3 ] && { [ "$ue" -eq 0 ] || [ "$nb" -lt 1 ]; }; then break; fi
  [ $waited -ge 7200 ] && { echo "no Blender slot within 2 h ($nb Blender, $ue UnrealEditor)" >&2; exit 4; }
  [ $((waited % 300)) -eq 0 ] && echo "waiting for a Blender slot: $nb Blender, $ue UnrealEditor running"
  sleep 20; waited=$((waited + 20))
done

mkdir -p "$(dirname "$OUT")"
LOG=${OUT%.glb}.merge.log
"$B" --background --factory-startup -P "$MERGE" -- "$RIG" "$OUT" "$@" > "$LOG" 2>&1
rc=$?
grep -E '^(CLIP|MERGE_OK)' "$LOG"
if [ $rc -ne 0 ] || ! grep -q '^MERGE_OK' "$LOG"; then echo "merge failed (rc $rc), log $LOG" >&2; exit 3; fi

# the output must carry exactly the listed animations
python3 - "$OUT" $WANT <<'PY' || exit 3
import json, struct, sys
out, want = sys.argv[1], sorted(sys.argv[2:])
with open(out, 'rb') as f:
    f.read(12); n, _ = struct.unpack('<I4s', f.read(8)); doc = json.loads(f.read(n))
got = sorted(a.get('name', '') for a in doc.get('animations', []))
if got != want:
    sys.exit('animation check FAILED: %s carries %s, expected %s' % (out, got, want))
print('ANIMS', ' '.join(got))
PY
echo "MAKE_V2R_GLB_OK $OUT"
