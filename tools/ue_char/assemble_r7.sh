#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Copies the round-07 captures + evidence from the scratch capture dir into docs/night1/characters/round-07 (mp4 <= 15 MB each, no frame folders, no full-run dumps).
#   tools/ue_char/assemble_r7.sh <scratch_captures_dir> <scratch_evidence_dir>
set -eu
WT="$(cd "$(dirname "$0")/../.." && pwd)"
CAP=${1:?}; EV=${2:?}
R7="$WT/docs/night1/characters/round-07"; mkdir -p "$R7/captures" "$R7/evidence"
for f in "$CAP"/*.mp4; do b=$(basename "$f"); case "$b" in seg*) continue;; esac; s=$(stat -f%z "$f"); [ "$s" -le 15000000 ] && cp "$f" "$R7/captures/$b" || echo "SKIP (>15 MB) $b"; done
for f in "$CAP"/*_4k.jpg "$CAP"/*_4k.png "$CAP"/*_1080.jpg "$CAP"/*_4k_t*.jpg; do [ -f "$f" ] && cp "$f" "$R7/captures/"; done
mkdir -p "$R7/evidence/telemetry"
for c in "$CAP"/telemetry/*_walkers.csv "$CAP"/crowd_walkers.csv; do [ -f "$c" ] && gzip -c "$c" > "$R7/evidence/telemetry/$(basename "$c").gz"; done
cp "$CAP"/telemetry/*_separation.* "$CAP"/*_separation.* "$R7/evidence/telemetry/" 2>/dev/null || true
cp "$CAP"/*_perf.json "$R7/evidence/" 2>/dev/null || true
cp "$CAP"/gpu_util_before_4k.txt "$CAP"/seg*_gpu_util_before.txt "$R7/evidence/" 2>/dev/null || true
cp -R "$EV"/. "$R7/evidence/" 2>/dev/null || true
du -sh "$R7"
