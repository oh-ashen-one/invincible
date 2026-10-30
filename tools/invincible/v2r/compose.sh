#!/bin/bash
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# Frames -> mp4 and a contact strip; two frame dirs -> side-by-side mp4 (old | new, same camera).
#   compose.sh mp4   <frames_dir> <out.mp4> [fps=24]
#   compose.sh strip <frames_dir> <out.jpg> [n=10]
#   compose.sh pair  <left_frames_dir> <right_frames_dir> <out.mp4> [fps=24]
set -e
case $1 in
  mp4)  ffmpeg -v error -y -framerate ${4:-24} -i "$2/%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 18 "$3" ;;
  strip) n=${4:-10}; total=$(ls "$2"/*.png | wc -l | tr -d ' '); files=$(python3 -c "import numpy as np;print(' '.join('$2/%04d.png'%i for i in np.linspace(0,$total-1,$n).round().astype(int)))"); ffmpeg -v error -y $(for f in $files; do printf -- "-i %s " $f; done) -filter_complex "hstack=inputs=$n" "$3" ;;
  pair) ffmpeg -v error -y -framerate ${5:-24} -i "$2/%04d.png" -framerate ${5:-24} -i "$3/%04d.png" -filter_complex "[0:v]drawtext=text='A':x=10:y=10:fontsize=28:fontcolor=yellow[a];[1:v]drawtext=text='B':x=10:y=10:fontsize=28:fontcolor=yellow[b];[a][b]hstack=inputs=2" -c:v libx264 -pix_fmt yuv420p -crf 18 "$4" ;;
  *) echo "usage: compose.sh mp4|strip|pair ..." >&2; exit 2 ;;
esac
