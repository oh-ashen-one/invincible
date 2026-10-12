#!/bin/zsh
# Capture every SHOTLIST view from the RUNNING game (Scripts/run_game.sh: offscreen -game, auto-activated shot camera),
# with frame times at 1920x1080 and 3840x2160. usage: tools/export/capture_round.sh <round_dir> [ids...]
# (r09) safety, after two engines of the r09 final hold went zombie ('?E' = stuck exiting in the GPU driver) and the follow-up launch hung 15 min until run_game.sh's own `kill -9` timeout:
#   - never launch while ANY UnrealEditor is stuck exiting (the nested gpu_slot pass-through does not re-check): wait up to 25 min, then abort the round (exit 6);
#   - run_game.sh gets -timeout 7200 (its timeout is a SIGKILL); a watchdog stops a capture that runs > 480 s with stop_ue.sh (drivers first, SIGTERM, wait) instead;
#   - abort (exit 7) as soon as one of our engines is left stuck exiting after its run: never stack a second launch on it;
#   - stop launching (exit 8) after CAPTURE_DEADLINE_S seconds (default 2100): the gpu_slot max hold is 2400 s and it kills what is still running. Re-run with the missing ids.
set -u
OUT=$1; shift
HERE=${0:A:h}
STOP=/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh
cd "$HERE/../../unreal/WebHomage"
WTPAT="[/]Users/midir/sm2-n1/city/unreal/WebHomage"
sick() { ps -axo stat=,comm= | awk '$1 ~ /[ZE]/ && $2 ~ /UnrealEditor/ && $2 !~ /Services/ {f=1} END {exit !f}'; }
T_START=$SECONDS; DEADLINE=${CAPTURE_DEADLINE_S:-2100}
IDS=("$@"); [ ${#IDS[@]} -eq 0 ] && IDS=($(python3 -c "import json;print(' '.join(s['id'] for s in json.load(open('Scripts/city_shots.json'))))"))
mkdir -p "$OUT/raw"
for id in $IDS; do
  for res in ${=RES_LIST:-1920x1080 3840x2160}; do   # (r10) RES_LIST="1920x1080" for a 1080p-only round
    w=0; while sick; do echo "capture_round: an UnrealEditor is stuck exiting, not launching ($w s)"; sleep 20; w=$((w+20)); [ $w -gt 1500 ] && { echo "capture_round: ABORT, GPU driver still wedged"; exit 6; }; done
    "$HERE/ue/wait_slot.sh"
    [ $((SECONDS - T_START)) -gt $DEADLINE ] && { echo "capture_round: deadline reached before $id $res (rerun with the remaining ids)"; exit 8; }
    GPU=$(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1 | grep -o '[0-9]*$')
    ( sleep 480; echo "capture_round: watchdog stop of $id $res"; $STOP "$WTPAT" ) &
    WD=$!
    ${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh} capture --label city -- Scripts/run_game.sh "$OUT/raw" -map /Game/Tests/City/City_View_$id -res $res -shots 28 -perf 18:28 -name ${id}_${res} -timeout 7200 > "$OUT/raw/${id}_${res}.run.txt" 2>&1
    kill $WD 2>/dev/null; wait $WD 2>/dev/null
    echo "{\"id\":\"$id\",\"res\":\"$res\",\"gpu_util_before_pct\":${GPU:-null}}" > "$OUT/raw/${id}_${res}_gpu.json"
    grep WH_PERF "$OUT/raw/${id}_${res}.run.txt" | tail -1
    sleep 8
    sick && { echo "capture_round: ABORT, an UnrealEditor is stuck exiting after $id $res"; exit 7; }
  done
done
