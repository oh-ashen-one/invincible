#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r04: turn the capture work dir (final_r04.sh output) into docs/night1/combat/round-04/ (mp4 <= 15 MB, 4K stills as JPEG, measurements, logs).
# Runs OUTSIDE the GPU hold (ffmpeg + numpy + cv2 only).
#   package_r04.sh <work_dir>            (work_dir has movieA, movieB, stills, map_build.out, movieA_diff.txt ...)
set -uo pipefail
W="$1"; HERE="$(cd "$(dirname "$0")" && pwd)"; R="$HERE/round-04"
MA="$W/movieA"; MB="$W/movieB"; ST="$W/stills"; REC="$HERE/round-03/ue/record"
mkdir -p "$R/stills" "$R/ue/movie" "$R/hit_strips" "$R/flare_strips"
# published movie: skip the first 0.9 s (P3 chase camera + exposure adaptation before the fight starts), crf raised until <= 15 MB
for crf in 22 24 26 28 30 32; do
  ffmpeg -loglevel error -y -ss 0.9 -i "$MA/fight.mp4" -an -c:v libx264 -preset slow -crf $crf -pix_fmt yuv420p -movflags +faststart "$R/fight30_1080p60.mp4"
  SZ=$(stat -f %z "$R/fight30_1080p60.mp4"); echo "crf $crf -> $SZ bytes"
  [ "$SZ" -le 15000000 ] && break
done
ffmpeg -loglevel error -y -i "$R/fight30_1080p60.mp4" -vf "select='not(mod(n\,90))',scale=640:360,tile=4x5" -frames:v 1 -q:v 3 "$R/contact_sheet_1080p.jpg"
# r03 tests (hit-stop, frozen frames, camera, enemies ...) on the published file and on the master, the r04 round-target tests on the master pair
python3 "$HERE/measure_r03.py" "$MA" "$R/measure.md" "$R/measure.json" --video "$R/fight30_1080p60.mp4" --trim 54 --strips "$R/hit_strips" --sheet "$R/boxes_check.jpg" --label "published fight30_1080p60.mp4 (x264)" > "$R/measure.out" 2>&1
python3 "$HERE/measure_r03.py" "$MA" "$R/measure_master.md" "$R/measure_master.json" --label "master (crf 18)" > "$R/measure_master.out" 2>&1
python3 "$HERE/measure_r04.py" "$MA" "$R/measure_master.json" "$R/measure_r04.md" "$R/measure_r04.json" --noflare "$MB" --strips "$R/flare_strips" > "$R/measure_r04.out" 2>&1
python3 "$HERE/measure_r04.py" "$MA" "$R/measure.json" "$R/measure_r04_published.md" "$R/measure_r04_published.json" --video "$R/fight30_1080p60.mp4" > "$R/measure_r04_published.out" 2>&1
python3 "$HERE/sim_metrics.py" "$MA" "$R/sim_metrics.json" > /dev/null
for f in "$ST"/still_[0-9]*.png; do
  b=$(basename "$f" .png); ffmpeg -loglevel error -y -i "$f" -q:v 2 "$R/stills/$b.jpg"
done
python3 - "$R/stills" <<'PY'
import glob, os, subprocess, sys
fs = sorted(glob.glob(os.path.join(sys.argv[1], 'still_[0-9]*.jpg')))
args = []
for f in fs: args += ['-i', f]
if fs:
    fc = ''.join('[%d]scale=640:360[s%d];' % (i, i) for i in range(len(fs))) + ''.join('[s%d]' % i for i in range(len(fs))) + 'xstack=inputs=%d:layout=%s' % (len(fs), '|'.join('%d_%d' % ((i % 5) * 640, (i // 5) * 360) for i in range(len(fs))))
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + args + ['-filter_complex', fc, '-q:v', '3', os.path.join(sys.argv[1], 'stills_sheet.jpg')], check=True)
PY
for f in fight_events.jsonl fight_beats.jsonl fight_summary.json fight_telemetry.csv; do cp "$MA/$f" "$R/ue/movie/$f"; done
gzip -c "$MA/fight_frames.jsonl" > "$R/ue/movie/fight_frames.jsonl.gz"
for f in movieA_diff.txt movieB_diff.txt stills_diff.txt map_build.out; do cp "$W/$f" "$R/ue/$f" 2>/dev/null; done
{ echo "movie A:"; grep -h WH_CMB_RES "$MA/fight.log" | sed 's/^.*LogWebHomage: Display: //' | head -1; echo "movie B:"; grep -h WH_CMB_RES "$MB/fight.log" | sed 's/^.*LogWebHomage: Display: //' | head -1; echo "stills:"; grep -h WH_CMB_RES "$ST/still.log" | sed 's/^.*LogWebHomage: Display: //' | head -1; } > "$R/ue/render_res.txt"
cat "$R/ue/render_res.txt"
ls -la "$R"
