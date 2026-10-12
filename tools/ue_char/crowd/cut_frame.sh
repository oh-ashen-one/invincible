#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# One frame of a fixed-step movie run as a still:  tools/ue_char/crowd/cut_frame.sh <frames_dir> <frame number> <out.jpg|out.png>
set -eu
D=${1:?frames dir}; N=${2:?frame}; O=${3:?out}
F=$(printf "%s/MovieFrame%05d.png" "$D" "$N")
[ -f "$F" ] || { echo "missing $F" >&2; exit 1; }
case "$O" in *.png) cp "$F" "$O";; *) ffmpeg -loglevel error -y -i "$F" -q:v 2 "$O";; esac
echo "$O <- frame $N"
