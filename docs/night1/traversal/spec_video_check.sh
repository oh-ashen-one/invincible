#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Runs the TRAVERSAL-SPEC video instruments on one 1080p60 capture: specs/tools/ref_hero_dets.py (YOLO11x-seg, 10 fps),
# rope_px_check.py (T3/T5/T6, T8-T10), specs/tools/vp_cam.py + vp_summary.py (T11-T14), specs/tools/nearflow.py 8 (T17/T18).
# usage: spec_video_check.sh <mp4> <label> [t0 t1]      (work files in /Users/midir/sm2-n1/_scratch/traversal/specwork/<label>)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; TOOLS="$HERE/../specs/tools"
PY=/Users/midir/sm2-n1/_scratch/traversal/specv/bin/python
MP4="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; L="$2"; T0="${3:-0}"; T1="${4:-1e9}"
W=/Users/midir/sm2-n1/_scratch/traversal/specwork/$L; mkdir -p "$W/frames"; cd "$W"
rm -f frames/*.jpg; ffmpeg -loglevel error -y -i "$MP4" -vf fps=10 -q:v 3 frames/%04d.jpg
[ -f "${L}_dets.json" ] || $PY "$TOOLS/ref_hero_dets.py" "$MP4" "$L" 6 > /dev/null 2>&1
$PY "$HERE/rope_px_check.py" "${L}_dets.json" frames "$L" "$T0" "$T1"
$PY "$TOOLS/vp_cam.py" "$MP4" "$L" 6 > /dev/null 2>&1; $PY "$HERE/vp_summary.py" "${L}_cam.csv" "$T0" "$T1"
$PY "$TOOLS/nearflow.py" 8 "$MP4"
