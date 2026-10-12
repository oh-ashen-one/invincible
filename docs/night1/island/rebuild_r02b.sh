#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r02b: after capture hold 1 (warmup + r3) ends, rebuild Manhattan_WP with the split_giants.py pieces (bridges / seawalls no longer
# r20 "giant" components): import only the split pieces, then the classic geo map + the WP map + build_manhattan's map step.
# Holds /Users/midir/sm2-n1/_scratch/island/BUILDING while it runs (capture_round.sh waits on it). Log: _scratch/island/logs/build_r02b.log
set -u
FLAG=/Users/midir/sm2-n1/_scratch/island/BUILDING
WT=/Users/midir/sm2-n1/island
until grep -q "hold 'warmup r3' rc" /Users/midir/sm2-n1/_scratch/island/logs/holds_r02.log; do sleep 10; done
while pgrep -f "$WT/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 10; done
touch "$FLAG"; trap 'rm -f "$FLAG"' EXIT
cd "$WT" && SM2_ISLAND_MESH_ONLY=split SM2_ISLAND_CITY_STEPS=mesh,map,wp python3 unreal/WebHomage/Scripts/build_manhattan.py --steps city,map
echo "rebuild rc $?"
