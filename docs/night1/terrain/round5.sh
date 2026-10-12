#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Terrain r05 capture hold (ONE slot hold, max 40 min). Enqueue from your own shell (detached), never from inside another hold:
#   STAGE=T /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label terrain --timeout 28800 -- docs/night1/terrain/round5.sh
# STAGE=T  test hold: safe warm-up (960x540) + the crown / lawn stills p4 p1 p10 (4K out) -> round-05/test/
# STAGE=S  final stills: safe warm-up + the nine 4K stills (p10 p4 p1 p9 first)                -> round-05/
# STAGE=M  final movies on the SAME content (no rebuild between S and M): t5 then t4 (1080p native, hero hidden)
# STAGE=R  resume: ONLY_IDS / WANT / MOVIES from the environment
# Content is built BEFORE the slot (tools/terrain/run_build.sh with SM2_TERRAIN_ROOT=/Game/TerrainR5, nullrhi, also through the lock). Every run passes -notraceserver (capture_round.sh RUN).
set -uo pipefail
S=/Users/midir/sm2-n1/_scratch/terrain
for _ in $(seq 1 120); do [ -e $S/BUILDING ] || break; sleep 5; done
if [ -e $S/BUILDING ]; then echo "terrain content still building after 10 min: giving the slot back"; exit 5; fi
export HOLD_START=$(date +%s)
rm -f "$S/capture/STOPPED" "$S/capture/FAILS"
HERE="$(cd "$(dirname "$0")" && pwd)"
export WH_CAPTURE_MAXFPS="${WH_CAPTURE_MAXFPS:-4}" MOVIE_MAXFPS="${MOVIE_MAXFPS:-12}" WARM_QUIT="${WARM_QUIT:-75}" HIDE_HERO=1 BASE_IDS=""
export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR5}" STILL_TAG="${STILL_TAG:-r05}"
case "${STAGE:-T}" in
  T) export ONLY_IDS="${ONLY_IDS:-p4_greatlawn p1_south p10_lawn_eye}" PRIO_IDS=""; ROUND="$HERE/round-05/${TEST_NAME:-test}"; WANT=(warm stills);;
  S) export PRIO_IDS="p10_lawn_eye p4_greatlawn p1_south p9_park_panorama"; ROUND="$HERE/round-05"; WANT=(warm stills);;
  M) export MOVIES="${MOVIES:-t5_avenue_to_park t4_lawn_sprint}"; ROUND="$HERE/round-05"; WANT=(moves);;
  R) export PRIO_IDS="${PRIO_IDS-}"; ROUND="$HERE/round-05"; read -r -a WANT <<< "${WANT:-stills}";;
  *) echo "unknown STAGE"; exit 2;;
esac
mkdir -p "$ROUND/stills"
echo "round5: stage ${STAGE:-T} root $TERRAIN_ROOT round $ROUND want ${WANT[*]} start $(date +%H:%M:%S) GPU $(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1)"
"$HERE/capture_round.sh" "$ROUND" "${WANT[@]}"
echo "round5 done $(date +%H:%M:%S)"
