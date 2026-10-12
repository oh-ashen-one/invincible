#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r04: FRESH rebuild of every Unreal content folder the island map uses, on the merged branch, timed (SPEC I8):
#   cpp (build_editor.sh) | city: clean,tex,mat | mesh (all 1,793 tile meshes, resumable) | proto | kit (272 tiles, resumable) | fsky,map,coll | wp
#   | traversal | characters | look | map (Manhattan* + Manhattan_WP player start / game mode / stream sources)
# Every commandlet is its own `gpu_slot.sh capture --label island` hold (SM2_ISLAND_GPU_SLOT=1, build_manhattan.py), one engine at a time.
# Inputs: the island export (_scratch/island/export/island; the browser sources are unchanged by the merge, so city_export / city_prep are
# not re-run: they need a vite listener), city_extra + street_kit re-run this round. Holds _scratch/island/BUILDING (capture_round.sh waits).
set -u
export GPU_SLOT_DIR=$HOME/.cache/gpu-slot   # (M5) the one shared coordinator; build_manhattan.py refuses any other root
FLAG=$HOME/sm2-n1/_scratch/island/BUILDING
WT=$HOME/sm2-n1/island
LOG=$HOME/sm2-n1/_scratch/island/r04/logs
while pgrep -f "$WT/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 10; done
FREE=$(df -k $HOME | awk 'NR==2 {printf "%d", $4 * 1024 / 1e9}'); echo "free GB (decimal) before: $FREE"
[ "$FREE" -lt 150 ] && { echo "ABORT: $FREE GB free < 150 GB"; exit 1; }   # build_manhattan.py re-checks before every commandlet
touch "$FLAG"; trap 'rm -f "$FLAG"' EXIT
T0=$(date +%s)
cd "$WT" && SM2_ISLAND_GPU_SLOT=1 SM2_ISLAND_SPLIT_FROM=${SPLIT_FROM:-a} python3 unreal/WebHomage/Scripts/build_manhattan.py --steps ${STEPS:-cpp,city,traversal,characters,look,map}
RC=$?
T1=$(date +%s)
echo "rebuild rc $RC wall $((T1 - T0)) s"
du -sk "$WT/unreal/WebHomage/Content" | awk '{printf "Content %.2f GB\n", $1 / 1048576}'
du -sh "$WT/unreal/WebHomage/Content"/* 2>/dev/null | sort -h | tail -8
FREE=$(df -k $HOME | awk 'NR==2 {printf "%d", $4 * 1024 / 1e9}'); echo "free GB (decimal) after: $FREE"
exit $RC
