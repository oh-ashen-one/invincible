#!/usr/bin/env python3
"""nullrhi probe of every case of a clip (fixed 1/60 s, 1.5 s pre-roll), merged like run_clip.py into <out>/<clip>_telemetry.csv (+ case / clip_t columns), then final_check.py -> <out>/<clip>_CHECK.txt.
usage: probe_clip.py <clip>[,<clip>...] [--out DIR] [--map island|island-night]"""
import argparse, csv, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
ap = argparse.ArgumentParser(); ap.add_argument('clips'); ap.add_argument('--out', default=str(Path.home() / 'sm2-n1/_scratch/final/swing/r01')); ap.add_argument('--map')
a = ap.parse_args()
clips = json.loads((ROOT / 'docs/night1/traversal/scripts/final/clips.json').read_text())
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
for clip in a.clips.split(','):
    rows = []; t0 = 0.0; frame = 0
    for name, q in clips[clip]:
        r = subprocess.run([sys.executable, str(ROOT / 'tools/final/swing/probe.py'), str(ROOT / 'docs/night1/traversal/scripts/final' / (name + '.json')), '--out', str(out / 'cases')] + (['--map', a.map] if a.map else []), capture_output=True, text=True)
        p = out / 'cases' / name / 'route_telemetry.csv'
        if not p.exists(): print(name, 'NO TELEMETRY', r.stdout[-200:], r.stderr[-200:]); continue
        rr = list(csv.DictReader(p.open()))
        for i, x in enumerate(rr): x['case'] = name; x['clip_t'] = '%.4f' % (t0 + float(x['t'])); x['clip_frame'] = str(frame + i)
        rows += rr; frame += len(rr); t0 += float(rr[-1]['t']) + 1 / 60
    with (out / (clip + '_telemetry.csv')).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    c = subprocess.run([sys.executable, str(ROOT / 'tools/final/swing/final_check.py'), str(out / (clip + '_telemetry.csv')), '--label', clip], capture_output=True, text=True)
    (out / (clip + '_CHECK.txt')).write_text(c.stdout)
    print(c.stdout)
