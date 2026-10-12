#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: apply / restore the perf transformations of the local city content (tools/perf_ue2/perf_apply.py).
#   perf_content.sh apply <steps>     e.g. static,far_rt,far_plain,kit_plain | all     (backs up the touched files first, once)
#   perf_content.sh restore           puts the backed-up files back (the state of C's build)
# Editor AND game must be closed (waits while 3+ real UnrealEditor processes run; -nullrhi commandlet, no GPU).
# Content is script-generated and never committed: re-running C's `build_manhattan.py --steps city,...` also restores it.
set -uo pipefail
WT="$(cd "$(dirname "$0")/../.." && pwd)"; UE="$WT/unreal/WebHomage"; C="$UE/Content"
BK="/Users/midir/sm2-n1/_scratch/perf/content_backup"
case "$WT" in /Users/midir/sm2-n1/perf) ;; *) echo "not my worktree: $WT"; exit 1;; esac
case "$BK" in /Users/midir/sm2-n1/_scratch/perf/*) ;; *) echo bad backup path; exit 1;; esac
FILES=(Tests/City/City_Midtown_Geo.umap City/Props/SM_hinterland.uasset City/Meshes/streetkit City/Meshes/detail Look/Rigs/Look_Rig_golden.umap Look/Rigs/Look_Rig_midday.umap Look/Rigs/Look_Rig_night.umap)
UEBIN="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
wait_slot() { while [ "$(ps -axo comm= | grep -c 'MacOS/UnrealEditor$')" -ge 3 ]; do echo "3+ Unreal running, waiting 60 s"; sleep 60; done; }
case "${1:-}" in
  apply)
    STEPS="${2:?steps}"
    mkdir -p "$BK"; for f in "${FILES[@]}"; do   # back up each file once (the state of C's build); files added to the list later are backed up on their first apply
      if [ ! -e "$BK/$f" ]; then mkdir -p "$BK/$(dirname "$f")"; cp -R "$C/$f" "$BK/$f"; echo "backed up $f"; fi
    done; touch "$BK/.done"
    while pgrep -f "sm2-n1/perf/tools/perf_ue2/[s]tills.sh" > /dev/null || pgrep -f "sm2-n1/perf/unreal/WebHomage/WebHomage.uproject" > /dev/null; do echo "my stills / game still running, waiting 20 s"; sleep 20; done
    wait_slot
    SM2_PERF_APPLY="$STEPS" "$UEBIN" "$UE/WebHomage.uproject" -run=pythonscript -script="$WT/tools/perf_ue2/perf_apply.py" -unattended -nullrhi -RenderOffScreen -NoSound \
      -abslog="/Users/midir/sm2-n1/_scratch/perf/logs/perf_apply.log" > /Users/midir/sm2-n1/_scratch/perf/logs/perf_apply.stdout 2>&1
    echo "commandlet exit $?"; grep -h '\[perf_apply\]' /Users/midir/sm2-n1/_scratch/perf/logs/perf_apply.log | tail -1 ;;
  restore)
    [ -f "$BK/.done" ] || { echo "no backup"; exit 1; }
    for f in "${FILES[@]}"; do [ -e "$BK/$f" ] || continue; rm -rf "$C/$f"; mkdir -p "$(dirname "$C/$f")"; cp -R "$BK/$f" "$C/$f"; done; echo restored ;;
  *) echo "usage: $0 apply <steps> | restore"; exit 2 ;;
esac
