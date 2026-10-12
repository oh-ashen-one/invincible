#!/usr/bin/env python3
"""r04: score t5 route probes (traversal telemetry CSVs) for 'the last 5 s cross park ground at 25-40 m'.
For every <dir>/*.csv: window = the last 5 s of the run (t >= tmax - 5, tmax = last row's t, default 15.4 s movie -> 10.4 .. 15.4 s); hero position (x_m, y_m) in UE metres (north = -y),
park rectangle x -234..234, y -2151..-569; height_above_floor_m in [25, 40] is the target band.
Reports share of window frames: hero in the park, in the park AND 25-40 m, in the park AND 20-45 m; min / median height over the in-park frames; camera in the park share. Sorted by the 25-40 m share.
usage: t5_score.py <dir> [out.json]"""
import sys, os, json, csv, glob
import numpy as np
PX0, PX1, PY0, PY1 = -234.0, 234.0, -2151.0, -569.0
d = sys.argv[1]; res = []
for f in sorted(glob.glob(os.path.join(d, '*.csv'))):
    rows = list(csv.DictReader(open(f)))
    if not rows: res.append({'name': os.path.basename(f)[:-4], 'error': 'empty'}); continue
    t = np.array([float(r['t']) for r in rows]); x = np.array([float(r['x_m']) for r in rows]); y = np.array([float(r['y_m']) for r in rows])
    haf = np.array([float(r['height_above_floor_m']) for r in rows]); cx = np.array([float(r['cam_x']) for r in rows]); cy = np.array([float(r['cam_y']) for r in rows])
    tmax = float(os.environ.get('T5_END', 15.4)); w = (t >= tmax - 5.0) & (t <= tmax)
    if not w.any(): res.append({'name': os.path.basename(f)[:-4], 'error': 'run ends at %.1f s' % t.max()}); continue
    inp = (x > PX0) & (x < PX1) & (y > PY0) & (y < PY1); cam = (cx > PX0) & (cx < PX1) & (cy > PY0) & (cy < PY1)
    n = float(w.sum()); b = inp & w
    res.append({'name': os.path.basename(f)[:-4], 'frames': int(n), 'run_end_s': round(float(t.max()), 2), 'in_park': round(float(b.sum()) / n, 3), 'in_park_25_40': round(float((b & (haf >= 25) & (haf <= 40)).sum()) / n, 3),
                'in_park_20_45': round(float((b & (haf >= 20) & (haf <= 45)).sum()) / n, 3), 'cam_in_park': round(float((cam & w).sum()) / n, 3),
                'haf_min_in_park': round(float(haf[b].min()), 1) if b.any() else None, 'haf_median_in_park': round(float(np.median(haf[b])), 1) if b.any() else None,
                'hero_end_xy': [round(float(x[w][-1]), 1), round(float(y[w][-1]), 1)], 'hero_start_window_xy': [round(float(x[w][0]), 1), round(float(y[w][0]), 1)]})
res.sort(key=lambda r: (-(r.get('in_park_25_40') or 0), -(r.get('in_park_20_45') or 0)))
for r in res: print(r)
if len(sys.argv) > 2: json.dump(res, open(sys.argv[2], 'w'), indent=1)
