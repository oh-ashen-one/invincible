#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 10: writes <round>/SPEC_CHECK.txt — TRAVERSAL-SPEC lines with the spec's own tools on the 1080p60 captures (spec_video_check.sh:
# ref_hero_dets / rope_px_check / vp_cam / nearflow) plus the engine-side telemetry checks (rhythm_check, spec_cam_check, anim,
# wall, facade). usage: spec_check_round.sh <round dir>
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; R="$(cd "$1" && pwd)"; O="$R/SPEC_CHECK.txt"
LAY=/Users/midir/sm2-n1/_scratch/traversal/manhattan/export/midtown3x3/layout.json
{
echo "# TRAVERSAL-SPEC check, $(basename "$R") — lit /Game/Maps/Manhattan (golden), 1080p60 captures; generated $(date '+%Y-%m-%d %H:%M')"
echo "# (homage fan game; not affiliated with Marvel, Sony or Insomniac)"
for S in "a_swing_chain 0.4 15.6" "b_release_trick_dive_zip 0 7" "c_wallrun_perch 0 10.5" "d_sprint_jump_first_swing 2.6 12"; do
  set -- $S; N=$1; T0=$2; T1=$3
  echo; echo "================ $N (window $T0-$T1 s)"
  echo "---- engine side: T1-T4 / T7 (rhythm_check.py, heights = feet over the street)"
  python3 "$HERE/rhythm_check.py" "$R/${N}_telemetry.csv" "$LAY" "$T0" "$T1"
  echo "---- engine side: T8-T14, T16, T19 (spec_cam_check.py, AVENUE_YAW=90)"
  AVENUE_YAW=90 python3 "$HERE/spec_cam_check.py" "$R/${N}_telemetry.csv" "$N" "$T0" "$T1"
  echo "---- video instruments (spec tools on the mp4): T3/T5/T6, T8-T10, T11-T14, T17/T18"
  "$HERE/spec_video_check.sh" "$R/$N.mp4" "r10_$N" "$T0" "$T1" 2>&1 | grep -v "^ \.\|^ R\|^\.\|^R" 
  echo "---- anim (T-pose, air silhouettes)"; python3 "$HERE/anim_check.py" "$R/${N}_telemetry.csv" "$N" 2>&1 | tail -6
done
echo; echo "================ c wall-run (T22)"; python3 "$HERE/wall_check.py" "$R/c_wallrun_perch_telemetry.csv" c 2>&1 | tail -6
} > "$O" 2>&1
echo "wrote $O"
