#!/bin/zsh
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P4 wrapper around P1's city pipeline (tools/export, unchanged) using P4's own ports and scratch dirs, so it never touches
# P1's dev server (5202), editor (8771), export or chrome profile.
#   1. vite on 5205 (this worktree)   2. tools/export/export_city.mjs -> <SCR>/export/midtown3x3   3. rewrite the manifest's
#   texture URLs 5205 -> 5202 (prep_textures.py / build_city.py split on '5202/')   4. prep_textures.py + gen_shaders.mjs
#   5. Scripts/build_city.py in the P4 editor (tools/perf_ue/launch_editor.sh, job server) = /Game/City + /Game/Tests/City
#   6. tools/perf_ue/rebuild_look.sh geo   (patch the city geometry level for the traversal + Look_Boxes)   [run by you afterwards]
# usage: tools/perf_ue/rebuild_city.sh        (about 10 min export + import; the editor must be running: tools/perf_ue/launch_editor.sh)
set -e
WT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$WT"
SCR=${SM2_LOOK_SCRATCH:-/Users/midir/sm2-n1/_scratch/look}; mkdir -p $SCR; export SM2_LOOK_SCRATCH=$SCR   # scratch root (env SM2_LOOK_SCRATCH); dev port: SM2_LOOK_DEV_PORT
DEVP=${SM2_LOOK_DEV_PORT:-5205}
[ -d node_modules ] || npm ci
curl -s -o /dev/null http://127.0.0.1:$DEVP/ || { (nohup npx vite --port $DEVP --host 127.0.0.1 --strictPort > $SCR/vite.log 2>&1 &); sleep 4; }
[ -n "$SKIP_EXPORT" ] || node tools/export/export_city.mjs --url http://127.0.0.1:$DEVP/ --out $SCR/export/midtown3x3 --profile $SCR/chrome-profile
sed -i '' "s#127.0.0.1:$DEVP/#127.0.0.1:5202/#g" $SCR/export/midtown3x3/manifest.json
# (round 03) mirror P1's tools/export/build_city.sh (round 05 / 06): patch_export -> textures -> street signs -> street kit -> street props -> shaders,
# every script pointed at THIS worktree's scratch (never P1's _scratch/city); paths need the trailing slash
EXPD=$SCR/export/midtown3x3/
python3 tools/export/patch_export.py $EXPD
python3 tools/export/prep_textures.py $SCR/tex $EXPD/manifest.json
python3 tools/export/gen_street_signs.py $SCR/tex/street_signs.png
python3 tools/export/street_kit.py $EXPD
python3 tools/export/street_props.py $EXPD
node tools/export/gen_shaders.mjs
UEJOB_TIMEOUT=7200 python3 tools/perf_ue/uejob.py unreal/WebHomage/Scripts/build_city.py steps=${STEPS:-clean,tex,mat,mesh,proto,kit,map}
echo "city content rebuilt: closing this worktree's editor and re-running the traversal-box / look build (steps geo,rigs,night,maps: the boxes depend on the city geometry level)"
pkill -9 -f "$WT/unreal/WebHomage/WebHomage.uproject"; sleep 4
"$WT/tools/perf_ue/rebuild_look.sh" geo,rigs,night,maps
