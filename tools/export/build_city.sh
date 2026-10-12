#!/bin/zsh
# Rebuild P1 City content from committed sources: browser export -> texture prep -> shader includes -> UE build.
# Requires: dev server on :$SM2_CITY_PORT (default 5202; npx vite --port <port> --host 127.0.0.1 --strictPort) unless SKIP_EXPORT=1 and the P1 editor with its job
# server (tools/export/ue/launch_editor.sh).  STEPS=clean,tex,mat,mesh,proto,map (default all).
set -e
cd "$(dirname "$0")/../.."
[ -n "$SKIP_EXPORT" ] || node tools/export/export_city.mjs
python3 tools/export/patch_export.py
python3 tools/export/prep_textures.py
python3 tools/export/gen_street_signs.py
python3 tools/export/street_kit.py
python3 tools/export/street_props.py
python3 tools/export/export_vehicles.py   # (r08) parked-car prototypes into proto/ + manifest
python3 tools/export/street_cars.py       # (r08) parked cars / taxis along the avenue curbs
python3 tools/export/street_trees.py      # (r08) street trees on every avenue sidewalk (fills empty pits + gaps)
python3 tools/export/street_traffic.py    # (r08) stopped avenue traffic (own actors, folder City/Traffic)
python3 tools/export/far_skyline.py        # (r10) far skyline / wooded bluff / shoreline / tree clumps (-> mesh/farsky, farsky.json; imported by the fsky step)
python3 tools/export/bake_sunmask.py      # (r09) building height field the materials ray-march for the canyon shade fill (-> $TEX/sunmask_h.png, imported by the tex / sunh step)
node tools/export/gen_shaders.mjs
UEJOB_TIMEOUT=7200 python3 tools/export/ue/uejob.py unreal/WebHomage/Scripts/build_city.py steps=${STEPS:-clean,tex,mat,mesh,proto,kit,fsky,map}
