#!/bin/bash
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# Make a rendered round folder repo-sized: full-res <case>.mp4 moves to ~/sm2-invincible-cache/<tag>/full/ (disposable), a 960x540
# review copy (<case>_540p.mp4) stays in docs, telemetry CSVs are gzipped. Sheets, luma, CHECK, RUN, CRITIC stay as they are.
# usage: tools/invincible/slim_round.sh <tag>
set -euo pipefail
T="$1"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; D="$ROOT/docs/invincible/captures/$T"; F="$HOME/sm2-invincible-cache/$T/full"
mkdir -p "$F"
for m in "$D"/*.mp4; do
  case "$m" in *_540p.mp4) continue;; esac
  n=$(basename "$m" .mp4)
  ffmpeg -loglevel error -y -i "$m" -vf scale=960:-2 -c:v libx264 -crf 30 -preset medium -pix_fmt yuv420p -movflags +faststart "$D/${n}_540p.mp4"
  mv "$m" "$F/"
done
for c in "$D"/*_telemetry.csv; do [ -f "$c" ] && gzip -9f "$c"; done
du -sh "$D"
