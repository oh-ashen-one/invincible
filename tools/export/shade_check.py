#!/usr/bin/env python3
"""P1 city round-09 shade tests (critic r08 'biggest gap': shadowed facades crushed).
usage: shade_check.py <round_dir> [--json out.json]
Test 1: S1_avenue_street 1920x1080, crops (0,0,480,300) and (1360,0,1740,400): mean Y >= 52 (CITY-SPEC C2 lower bound).
Test 2: share of pixels with Y < 25 over the WHOLE frame: S3 <= 25 %, S7 <= 30 % (also reported for every other view, 1080p and 4K).
Luma Y = .2126 R + .7152 G + .0722 B on the 8-bit sRGB frame (same as city_spec_check.py)."""
import glob, json, os, sys
import cv2
import numpy as np

def luma(c):
    c = c.astype(np.float32); return .2126 * c[..., 2] + .7152 * c[..., 1] + .0722 * c[..., 0]

def find(root, view, res):
    hits = [f for f in sorted(glob.glob(os.path.join(root, f'{view}_{res}.*'))) if f.lower().endswith(('.jpg', '.png'))]
    return hits[0] if hits else None

def main():
    a = sys.argv[1:]
    root = a[0]; jout = a[a.index('--json') + 1] if '--json' in a else None
    out = {'test1': [], 'test2': [], 'dark_share_all': []}
    p = find(root, 'S1_avenue_street', '1920x1080')
    if p:
        Y = luma(cv2.imread(p))
        for box, name in (((0, 0, 480, 300), 'S1 left crop'), ((1360, 0, 1740, 400), 'S1 right crop')):
            x0, y0, x1, y1 = box; c = Y[y0:y1, x0:x1]
            out['test1'].append(dict(name=name, box=box, meanY=round(float(c.mean()), 1), share_lt25=round(float((c < 25).mean() * 100), 1), ok=bool(c.mean() >= 52)))
    for view, lim in (('S3_rooftop_watertower', 25.0), ('S7_sunset_crosstown', 30.0)):
        p = find(root, view, '1920x1080')
        if p:
            Y = luma(cv2.imread(p)); s = float((Y < 25).mean() * 100)
            out['test2'].append(dict(view=view, share_lt25=round(s, 1), limit=lim, meanY=round(float(Y.mean()), 1), ok=bool(s <= lim)))
    for res in ('1920x1080', '3840x2160'):
        for f in sorted(glob.glob(os.path.join(root, f'S?_*_{res}.*'))):
            if not f.lower().endswith(('.jpg', '.png')): continue
            Y = luma(cv2.imread(f))
            out['dark_share_all'].append(dict(frame=os.path.basename(f), share_lt25=round(float((Y < 25).mean() * 100), 1), share_gt204=round(float((Y > 204).mean() * 100), 2), meanY=round(float(Y.mean()), 1)))
    print('Test 1 (S1 crops mean Y >= 52):')
    for r in out['test1']: print(f"  {r['name']:14s} {r['box']}  meanY {r['meanY']:6.1f}  share<25 {r['share_lt25']:5.1f}%  {'PASS' if r['ok'] else 'FAIL'}")
    print('Test 2 (share of Y<25, whole frame):')
    for r in out['test2']: print(f"  {r['view']:24s} {r['share_lt25']:5.1f}%  (limit {r['limit']}%)  frame meanY {r['meanY']}  {'PASS' if r['ok'] else 'FAIL'}")
    print('All frames (share Y<25 / share Y>204 / mean Y):')
    for r in out['dark_share_all']: print(f"  {r['frame']:38s} {r['share_lt25']:5.1f}%  {r['share_gt204']:5.2f}%  {r['meanY']:6.1f}")
    if jout:
        json.dump(out, open(jout, 'w'), indent=1)

main()
