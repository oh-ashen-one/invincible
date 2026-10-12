#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r03: turn the capture work dir (final_r03.sh output) into docs/night1/combat/round-03/ (mp4 <= 15 MB, 4K stills as JPEG, measurements, logs).
# Runs OUTSIDE the GPU hold (ffmpeg + numpy only). The published mp4 (what the critic sees) is measured as well as the crf-18 master.
#   package_r03.sh <work_dir> <picked seed>
set -uo pipefail
W="$1"; SEED="${2:?seed}"; HERE="$(cd "$(dirname "$0")" && pwd)"; R="$HERE/round-03"
MV="${MOVIE_DIR:-$W/cap/movie}"; ST="${STILLS_DIR:-$W/cap/stills}"; RD="${REPLAY_DIR:-$W/cap}"
mkdir -p "$R/stills" "$R/ue/record" "$R/ue/movie" "$R/hit_strips"
# movie: skip the first 0.9 s (P3 chase camera + exposure adaptation before the fight starts), crf raised until <= 15 MB
for crf in 22 24 26 28 30 32; do
  ffmpeg -loglevel error -y -ss 0.9 -i "$MV/fight.mp4" -an -c:v libx264 -preset slow -crf $crf -pix_fmt yuv420p -movflags +faststart "$R/fight30_1080p60.mp4"
  SZ=$(stat -f %z "$R/fight30_1080p60.mp4"); echo "crf $crf -> $SZ bytes"
  [ "$SZ" -le 15000000 ] && break
done
ffmpeg -loglevel error -y -i "$R/fight30_1080p60.mp4" -vf "select='not(mod(n\,90))',scale=640:360,tile=4x5" -frames:v 1 -q:v 3 "$R/contact_sheet_1080p.jpg"
# measurements: the published file (primary, what the critic sees) and the master
python3 "$HERE/measure_r03.py" "$MV" "$R/measure.md" "$R/measure.json" --video "$R/fight30_1080p60.mp4" --trim 54 --strips "$R/hit_strips" --sheet "$R/boxes_check.jpg" --label "published fight30_1080p60.mp4 (x264)" > "$R/measure.out" 2>&1
python3 "$HERE/measure_r03.py" "$MV" "$R/measure_master.md" "$R/measure_master.json" --label "master (crf 18)" > "$R/measure_master.out" 2>&1
python3 "$HERE/sim_metrics.py" "$MV" "$R/sim_metrics.json" > /dev/null
n=0
for f in "$ST"/still_[0-9]*.png; do
  b=$(basename "$f" .png); ffmpeg -loglevel error -y -i "$f" -q:v 2 "$R/stills/$b.jpg"; n=$((n+1))
done
python3 - "$R/stills" <<'PY'
import glob, os, subprocess, sys
fs = sorted(glob.glob(os.path.join(sys.argv[1], 'still_[0-9]*.jpg')))
args = []
for f in fs: args += ['-i', f]
if fs:
    fc = ''.join('[%d]scale=768:432[s%d];' % (i, i) for i in range(len(fs))) + ''.join('[s%d]' % i for i in range(len(fs))) + 'xstack=inputs=%d:layout=%s' % (len(fs), '|'.join('%d_%d' % ((i % 5) * 768, (i // 5) * 432) for i in range(len(fs))))
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + args + ['-filter_complex', fc, '-q:v', '3', os.path.join(sys.argv[1], 'stills_sheet.jpg')], check=True)
PY
for f in fight_events.jsonl fight_beats.jsonl fight_summary.json fight_telemetry.csv; do cp "$MV/$f" "$R/ue/movie/$f"; done
gzip -c "$MV/fight_frames.jsonl" > "$R/ue/movie/fight_frames.jsonl.gz"
for f in fight_events.jsonl fight_beats.jsonl fight_summary.json; do cp "$W/sweep/seed$SEED/$f" "$R/ue/record/$f"; done
cp "$W/sweep/script_seed$SEED.json" "$R/ue/record/script_seed$SEED.json"
cp "$RD/replay_diff.txt" "$R/ue/" 2>/dev/null; cp "$RD/movie_diff.txt" "$R/ue/movie_diff.txt" 2>/dev/null
cp "$W/sweep/map_build.out" "$R/ue/map_build.out" 2>/dev/null
python3 "$HERE/sweep_report.py" $(ls -d "$W"/sweep/seed[0-9]* | grep -v "\.out$") > "$R/ue/seed_sweep.txt" 2>/dev/null
ls -la "$R"
