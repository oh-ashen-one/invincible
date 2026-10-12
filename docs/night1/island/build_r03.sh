#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r03 (M2): rebuild /Game/City + /Game/Maps/Manhattan_WP for the WHOLE island on top of the r02 (M1) content.
#   prerequisites (done by build_manhattan.py --steps city_export,city_prep,city_extra; defaults = whole island, export 'island')
#   tex   re-import textures (signs.png IP rows: CHASE BANK et al. -> tools/export/ip_sanitize.py)
#   mesh  SM2_ISLAND_MESH_ONLY=missing: only the meshes M1 did not have (the shared GLBs are byte-identical)
#   kit, fsky, map (classic geo level), coll (empty placeholder), wp (World Partition map, WHBox cubes as per-tile components)
# then build_manhattan's map step. Holds /Users/midir/sm2-n1/_scratch/island/BUILDING (capture_round.sh waits on it).
# A clean from-scratch build is: python3 unreal/WebHomage/Scripts/build_manhattan.py   (all steps, every mesh imported)
set -u
FLAG=/Users/midir/sm2-n1/_scratch/island/BUILDING
WT=/Users/midir/sm2-n1/island
while pgrep -f "$WT/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 10; done
touch "$FLAG"; trap 'rm -f "$FLAG"' EXIT
cd "$WT" && SM2_ISLAND_MESH_ONLY=missing SM2_ISLAND_CITY_STEPS=${SM2_ISLAND_CITY_STEPS:-tex,mesh,kit,fsky,map,coll,wp} \
  python3 unreal/WebHomage/Scripts/build_manhattan.py --steps ${STEPS:-city,map}
echo "rebuild rc $?"
