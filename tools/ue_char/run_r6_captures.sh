#!/bin/bash
# Round-06 capture driver (Fan homage project; not official Marvel/Sony/Insomniac; no affiliation).
# One capture_r5.sh invocation per group, most important first, so a failed / queued-out group never blocks the others.  Every launch inside goes
# through gpu_slot.sh capture (never bypassed).  Frame folders are removed after their clips are cut (workspace hygiene).
#   tools/ue_char/run_r6_captures.sh <out_dir> [GROUPS]        GROUPS default: K C S E H F
#     K = chroma-key crowd stills (CH18 in the engine)      C = crowd 1080p60 movie (tracking + wide)     S = crowd 4K stills (tracking + wide)
#     E = enemy face close-ups (thug collar etc.)           H = hero movies (side / 3/4 / leap, chase / toward) + hero 4K stills + leap
#     F = fight movies + 4K stills
set -u
WT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT=${1:?out dir}; GROUPS_=${2:-"K C S E H F"}
mkdir -p "$OUT"
CAP="$WT/tools/ue_char/capture_r5.sh"
for g in $GROUPS_; do
  echo "[r6 captures] group $g start $(date +%H:%M:%S)"
  case $g in
    K) "$CAP" "$OUT" "" "gK" "" ;;
    I) "$CAP" "$OUT" "" "gI" "" ;;
    C) "$CAP" "$OUT" "C" "" "" ;;
    S) "$CAP" "$OUT" "" "gC" "" ;;
    E) "$CAP" "$OUT" "" "gE" "" ;;
    H) "$CAP" "$OUT" "H G" "gH" "1" ;;
    F) "$CAP" "$OUT" "F" "gF" "" ;;
  esac
  echo "[r6 captures] group $g exit $? $(date +%H:%M:%S)"
  for d in "$OUT"/seg*_frames; do [ -d "$d" ] && case "$d" in "$OUT"/*) rm -rf "$d";; esac; done
done
echo "[r6 captures] done"
