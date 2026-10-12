#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Texture streaming: the first ~0.4 s of every -movie run shows the lowest texture mips.  The first clip of each run starts 0.6 s later (re-encoded crf 17 from the cut clip);
# the original is kept in <dir>/untrimmed/.   tools/ue_char/trim_clips_r7.sh <captures_dir>
set -eu
D=${1:?captures dir}; mkdir -p "$D/untrimmed"
for c in hero_run_side hero_run_chase street_fight_wide crowd_tracking; do
  f="$D/$c.mp4"; [ -f "$f" ] || continue; [ -f "$D/untrimmed/$c.mp4" ] && continue
  cp "$f" "$D/untrimmed/$c.mp4"
  ffmpeg -loglevel error -y -ss 0.6 -i "$D/untrimmed/$c.mp4" -c:v libx264 -pix_fmt yuv420p -crf 17 -movflags +faststart "$f"
done
ls -la "$D"/*.mp4 | awk '{print $5, $9}'
