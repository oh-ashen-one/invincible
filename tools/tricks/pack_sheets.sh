#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C: per-clip contact sheets (4x3 frames evenly spaced, <= 2048 px wide) next to every A / B clip of an abpack pack.
#   tools/tricks/pack_sheets.sh <pack dir>
set -uo pipefail
for v in "$1"/*/[AB].mp4; do
  d=$(dirname "$v"); s=$(basename "$v" .mp4)
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v")
  n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$v")
  step=$(( n / 12 )); [ "$step" -lt 1 ] && step=1
  ffmpeg -loglevel error -y -i "$v" -vf "select='not(mod(n\,$step))',scale=512:-2,tile=4x3:padding=4:color=black" -frames:v 1 -update 1 -q:v 3 "$d/${s}_sheet.jpg"
  echo "$d/${s}_sheet.jpg (${dur}s, $n frames, every ${step}th)"
done
