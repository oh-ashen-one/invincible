#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Terrain r04 capture hold (ONE slot hold, max 40 min). Enqueue with (detached):
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label terrain --timeout 28800 -- docs/night1/terrain/round4.sh      (env STAGE=A | B | R)
# STAGE=A  hold 1 = the whole round: safe warm-up, the nine 4K stills (p10 p4 p9 p1 first), the t5 route probes (nullrhi; the best candidate becomes the t5 movie), the t4 + t5 movies, GPU ms of p1 / p10 on the HEAD content vs this build (basegpu, if time is left)
# STAGE=B  hold 2 = whatever hold 1 did not finish: ONLY_IDS / MOVIES / WANT from the environment, default the five non-lawn stills + the t5 movie + basegpu
# STAGE=R  resume: ONLY_IDS / WANT / MOVIES from the environment (e.g. ONLY_IDS="p6_west_shore" WANT="stills")
# Content is built BEFORE the slot (nullrhi commandlets, no GPU). Capture safety (two health-monitor stops on 2026-10-02): 960x540 warm-up with r.ScreenPercentage 50 and a 4 fps fixed step,
# 4K stills stay at the 4 fps frame cap; WARM_QUIT 75 game seconds = 300 frames at the 4 fps step / cap = ~75 s wall, long enough for the new materials' shaders to finish compiling (the compile dies with the process); watch /Users/midir/sm2-n1/_scratch/gpu/health.log during the first 2 minutes.
set -uo pipefail
S=/Users/midir/sm2-n1/_scratch/terrain
for _ in $(seq 1 120); do [ -e $S/BUILDING ] || break; sleep 5; done
if [ -e $S/BUILDING ]; then echo "terrain content still building after 10 min: giving the slot back"; exit 5; fi
export HOLD_START=$(date +%s)
rm -f "$S/capture/STOPPED" "$S/capture/FAILS"   # (capture_round.sh: a stopped / failed run ends the hold)
HERE="$(cd "$(dirname "$0")" && pwd)"
export WH_CAPTURE_MAXFPS="${WH_CAPTURE_MAXFPS:-4}" MOVIE_MAXFPS="${MOVIE_MAXFPS:-12}" WARM_QUIT="${WARM_QUIT:-75}" HIDE_HERO=1 BASE_IDS=""   # movies: 1080p, fixed 1/60 s step, frame cap 12 fps (r03: 20) so the GPU idles between frames
case "${STAGE:-A}" in
  A) # hold 1 = the whole round in one hold: safe warm-up, the nine 4K stills (lawn / canopy gate p10 p4 p9 p1 first), the t5 route probes (nullrhi, picks the best candidate), the t4 + t5 movies, GPU ms of p1 / p10 HEAD vs r04
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" BASE_ROOT=/Game/Terrain PRIO_IDS="p10_lawn_eye p4_greatlawn p9_park_panorama p1_south" STILL_TAG=r04 PROBE_DIR="${PROBE_DIR:-$HERE/round-04/t5_candidates}"
     ROUND="$HERE/${ROUND_NAME:-round-04}"; WANT=(warm stills); AFTER=("t5probe" "moves" "basegpu");;
  C) # hold 3 (r04 final stills): safe warm-up, the nine 4K stills (p10 p4 p9 p1 first), the t5 route probes (picks chosen.json for the movies hold), GPU ms of p1 / p10 HEAD vs r04 (basegpu, if time is left)
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" BASE_ROOT=/Game/Terrain PRIO_IDS="p10_lawn_eye p4_greatlawn p9_park_panorama p1_south" STILL_TAG=r04 PROBE_DIR="${PROBE_DIR:-$HERE/round-04/t5_candidates3}"
     ROUND="$HERE/${ROUND_NAME:-round-04}"; WANT=(warm stills); AFTER=("t5probe" "basegpu");;
  D) # hold 4 (r04 final stills): safe warm-up + the nine 4K stills only (p10 p4 p9 p1 first); no probes (the route is chosen), no movies (hold M), no baseline (hold 3 has it)
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" PRIO_IDS="p10_lawn_eye p4_greatlawn p9_park_panorama p1_south" STILL_TAG=r04
     ROUND="$HERE/${ROUND_NAME:-round-04}"; WANT=(warm stills); AFTER=();;
  M) # movies hold: t5 (on the probe's chosen route) then t4; each only starts in the first 25 min of the hold; the shaders are cached by the stills hold (no warm-up)
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" MOVIES="${MOVIES:-t5_avenue_to_park t4_lawn_sprint}"
     ROUND="$HERE/${ROUND_NAME:-round-04}"; WANT=(moves); AFTER=();;
  W) # hold 5 (r04 final build, 2026-10-03): safe warm-up (the final build adds M_TerrainRock), then the t5 movie (on the committed route) and the t4 movie; each only starts in the first 25 min of the hold
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" MOVIES="${MOVIES:-t5_avenue_to_park t4_lawn_sprint}"
     ROUND="$HERE/${ROUND_NAME:-round-04}"; WANT=(warm moves); AFTER=();;
  S) # hold 6 (r04 final build): the nine 4K stills (p10 p4 p9 p1 first), then the GPU ms of p1 / p10 on the HEAD content (/Game/Terrain) vs this build again, same hold (basegpu, as far as the hold budget allows)
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" BASE_ROOT=/Game/Terrain PRIO_IDS="p10_lawn_eye p4_greatlawn p9_park_panorama p1_south" STILL_TAG=r04
     ROUND="$HERE/${ROUND_NAME:-round-04}"; WANT=(warm stills); AFTER=("basegpu");;
  B) # hold 2: everything the first hold did not take (the other five stills + the t5 movie on the chosen route); BASE_IDS stays empty
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" ONLY_IDS="${ONLY_IDS:-p2_reservoir p3_lake p6_west_shore p7_east_shore p8_pier}" PRIO_IDS="${PRIO_IDS-}" STILL_TAG="${STILL_TAG:-r04}" MOVIES=t5_avenue_to_park
     ROUND="$HERE/${ROUND_NAME:-round-04}"; WANT=(warm stills moves basegpu); AFTER=();;
  R) # resume: ONLY_IDS / WANT / MOVIES from the environment
     export TERRAIN_ROOT="${TERRAIN_ROOT:-/Game/TerrainR4}" PRIO_IDS="${PRIO_IDS-}" STILL_TAG="${STILL_TAG:-r04}"; ROUND="$HERE/${ROUND_NAME:-round-04}"; read -r -a WANT <<< "${WANT:-stills}"; AFTER=();;
  *) echo "unknown STAGE"; exit 2;;
esac
mkdir -p "$ROUND/stills"
echo "round4: stage ${STAGE:-B} root $TERRAIN_ROOT round $ROUND want ${WANT[*]} start $(date +%H:%M:%S) GPU $(ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' | head -1)"
"$HERE/capture_round.sh" "$ROUND" "${WANT[@]}"
for G in "${AFTER[@]+"${AFTER[@]}"}"; do read -r -a GW <<< "$G"; "$HERE/capture_round.sh" "$ROUND" "${GW[@]}"; done   # r04 hold A: stills, then the (GPU-free) route probes, then the t4 movie
