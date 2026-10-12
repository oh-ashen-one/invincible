#!/usr/bin/env python3
"""Frame statistics of a perf-window run (<name>_frames.csv written by the automation) + log facts + a 1080p contact sheet of the run's shots.
usage: perf_report.py <run dir> [--name NAME] [--shots-every 3] [--holder PID]
Reports frames, avg/p50/p95/p99/max frame ms, GPU ms avg/p95, frames > 33.3 / > 50 ms, the longest hitch (timestamp + the log lines around it), the last WH_CITYLIGHTS active count,
and the same statistics with the frames within 0.25 s of a screenshot request removed. Writes <name>_report.json and <name>_sheet.png."""
import argparse
import csv
import json
import re
from pathlib import Path

import cv2
import numpy as np


def stats(ms, gpu):
    a = np.array(ms)
    return {'frames': int(a.size), 'avg_ms': round(float(a.mean()), 2), 'p50_ms': round(float(np.percentile(a, 50)), 2), 'p95_ms': round(float(np.percentile(a, 95)), 2),
            'p99_ms': round(float(np.percentile(a, 99)), 2), 'max_ms': round(float(a.max()), 2), 'gpu_avg_ms': round(float(np.mean(gpu)), 2), 'gpu_p95_ms': round(float(np.percentile(gpu, 95)), 2),
            'over_33_3': int((a > 33.3).sum()), 'over_50': int((a > 50).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--name', default='route')
    ap.add_argument('--holder', default='')
    a = ap.parse_args()
    run = Path(a.run)
    rows = list(csv.DictReader((run / f'{a.name}_frames.csv').open()))
    t = np.array([float(r['t_s']) for r in rows]); ms = [float(r['frame_ms']) for r in rows]; gpu = [float(r['gpu_ms']) for r in rows]
    log = (run / f'{a.name}.log').read_text(errors='replace').splitlines()
    shots = [float(m.group(1)) for l in log for m in [re.search(r'_t(\d+\.\d)\.png', l)] if m and 'WH_SHOT ' in l]
    out = {'holder_pid': a.holder or None, 'contaminated_by': 'coexisting Qwen resident (holder pid %s)' % (a.holder or '?'), 'all_frames': stats(ms, gpu)}
    keep = np.ones(len(t), bool)
    for s in shots: keep &= np.abs(t - s) > 0.25
    if keep.sum() != len(t): out['excluding_shot_frames'] = stats(list(np.array(ms)[keep]), list(np.array(gpu)[keep]))
    k2 = np.array(ms) < 500   # screenshot frames hitch ~1 s each (4K PNG readback + write); the window statistics without them
    out['excluding_screenshot_hitches'] = dict(stats(list(np.array(ms)[k2]), list(np.array(gpu)[k2])), removed_frames=int((~k2).sum()), removed_ms=[round(m) for m in ms if m >= 500])
    i = int(np.argmax(ms)); out['longest_hitch'] = {'ms': ms[i], 't_s': float(t[i]), 'near_shot': any(abs(t[i] - s) <= 0.25 for s in shots)}
    out['hitches_over_50'] = [{'t_s': float(t[j]), 'ms': ms[j]} for j in range(len(ms)) if ms[j] > 50][:30]
    ctx = [l for l in log if re.search(r'WH_(TRAV|SHOT|PERF)|Warning|Error|LogStreaming|LogTexture|Shader', l)]
    out['log_hint_lines'] = ctx[:0]
    for k in ('WH_RES', 'WH_PERF ', 'WH_TRAV_SCRIPT', 'WH_CITYLIGHTS night'):
        L = [l for l in log if k in l]
        if L: out[k.strip()] = L[-1].split(']')[-1].strip()[:260] if k != 'WH_CITYLIGHTS night' else [x.split(']')[-1].strip()[:200] for x in L[-3:]]
    tf = run / f'{a.name}_telemetry.csv'
    if tf.is_file():
        T = list(csv.DictReader(tf.open()))
        f = lambda k: [float(r[k]) for r in T if r.get(k) not in (None, '')]
        sw0 = next((i for i, r in enumerate(T) if r['mode'] == 'swing'), None)
        out['telemetry'] = {'rows': len(T), 'sim_t_end': float(T[-1]['t']), 'x_m': [min(f('x_m')), max(f('x_m'))], 'y_m': [min(f('y_m')), max(f('y_m'))], 'z_m_max': max(f('z_m')),
                            'max_speed_mps': max(f('speed_mps')), 'modes': {m: sum(r['mode'] == m for r in T) for m in sorted({r['mode'] for r in T})},
                            'ground_rows_after_first_swing': sum(r['mode'] == 'ground' for r in T[sw0:]) if sw0 is not None else None,
                            'cam_in_geometry_rows': sum(float(r['cam_in_geometry'] or 0) > 0 for r in T), 'cam_enclosed_rows': sum(float(r['cam_enclosed'] or 0) > 0 for r in T),
                            'min_height_above_floor_m': min(f('height_above_floor_m')), 'setbacks': float(T[-1]['setbacks'] or 0), 'topouts': float(T[-1]['topouts'] or 0), 'tunnel_stops': float(T[-1]['tunnel_stops'] or 0)}
    out['shots_t'] = shots
    (run / f'{a.name}_report.json').write_text(json.dumps(out, indent=1))
    pngs = sorted(run.glob(f'{a.name}_[0-9][0-9]_t*.png'))
    if pngs:
        cols = 4; w, h = 480, 270; rws = (len(pngs) + cols - 1) // cols
        sheet = np.zeros((rws * h, cols * w, 3), np.uint8)
        for k, f in enumerate(pngs):
            im = cv2.resize(cv2.imread(str(f)), (w, h), interpolation=cv2.INTER_AREA)
            cv2.putText(im, f.stem.split('_t')[-1] + ' s', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            sheet[(k // cols) * h:(k // cols + 1) * h, (k % cols) * w:(k % cols + 1) * w] = im
        cv2.imwrite(str(run / f'{a.name}_sheet.png'), sheet)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
