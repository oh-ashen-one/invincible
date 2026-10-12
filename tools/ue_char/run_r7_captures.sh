#!/bin/bash
# Round-07 capture driver (Fan homage project; not official Marvel/Sony/Insomniac; no affiliation).
#   tools/ue_char/run_r7_captures.sh <out_dir> [GROUPS]       GROUPS default: T K I C A D S E H F
#     T = walker telemetry (no renderer): old layout with avoidance OFF (baseline), old layout avoidance ON, the round-07 crowd
#     K = chroma-key crowd stills (stencil keyer), I = per-walker id stills, D = per-walker id movie (frame-exact with the crowd clip), C = crowd 1080p60 movie (+ telemetry of the same run), S = crowd 4K stills,
#     E = enemy faces, H = hero movies + stills + leap, F = fight movies + stills
# Every launch goes through gpu_slot.sh (capture_r5.sh / run_telemetry.sh); groups run one at a time, one engine of mine at any moment.
set -u
WT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT=${1:?out dir}; GROUPS_=${2:-"T K I C S E H F"}
mkdir -p "$OUT"
for g in $GROUPS_; do
  echo "[r7 captures] group $g start $(date +%H:%M:%S)"
  case $g in
    T) TEL="$WT/tools/ue_char/crowd/run_telemetry.sh"; MAPS=/Game/Tests/Characters
       WHX="-WHNoAvoid" "$TEL" "$OUT/telemetry" $MAPS/Char_CrowdAvoid avoid_off_r6layout 15
       "$TEL" "$OUT/telemetry" $MAPS/Char_CrowdAvoid avoid_on_r6layout 15
       "$TEL" "$OUT/telemetry" $MAPS/Char_Crowd crowd_r7layout 15 ;;
    K) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "" "gK" "" ;;
    I) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "" "gI" "" ;;
    C) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "C" "" "" ;;
    A) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "A" "" "" ;;
    D) "$WT/tools/ue_char/crowd/id_movie.sh" "$OUT" ;;
    S) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "" "gC" "" ;;
    E) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "" "gE" "" ;;
    H) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "H G" "gH" "1" ;;
    F) "$WT/tools/ue_char/capture_r5.sh" "$OUT" "F" "gF" "" ;;
  esac
  echo "[r7 captures] group $g exit $? $(date +%H:%M:%S)"
  for d in "$OUT"/seg*_frames; do [ -d "$d" ] && case "$d" in "$OUT"/segD_frames) ;; "$OUT"/*) rm -rf "$d";; esac; done   # segD (id movie) frames are analysed before they go
done
echo "[r7 captures] done"
