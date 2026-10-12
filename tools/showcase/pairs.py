#!/usr/bin/env python3
"""Side-by-side comparison of matched-camera captures: for every shot of a --shot-cams run, pair_<name>.png = the author's reference (left) and ours (right), both scaled to 1920x1080
(one 3840x1080 PNG), plus pairs.json with the per-region mean LINEAR luminance (sky = top third, facade = middle third, street = bottom third; ours vs ref) and the sky probe (top 10 % rows,
x 40-60 %, the open sky above the avenue in the street views).
usage: pairs.py RUN_DIR [--cams shot_cams.json] [--name night]   (RUN_DIR holds <name>_<NN>_<shot>.png)"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

CAMS = Path.home() / 'sm2-n1/_scratch/night/ref/shot_cams.json'


def lin_luma(img_bgr):
    rgb = img_bgr[..., ::-1].astype(np.float32) / 255.0
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def regions(img):
    L = lin_luma(img)
    h, w = L.shape
    mid = L[h // 3:2 * h // 3]
    return {'sky_top_third': float(L[:h // 3].mean()), 'facade_mid_third': float(mid.mean()), 'street_bottom_third': float(L[2 * h // 3:].mean()),
            'sky_probe': float(L[:h // 10, int(w * 0.4):int(w * 0.6)].mean()), 'mean': float(L.mean()),
            'facade_mid_median': float(np.median(mid)), 'facade_mid_p95': float(np.percentile(mid, 95)), 'lit_fraction_mid_gt_0.1': float((mid > 0.1).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--cams', default=str(CAMS))
    ap.add_argument('--name', default='night')
    a = ap.parse_args()
    run = Path(a.run)
    cams = json.loads(Path(a.cams).read_text())
    res = {}
    for i, c in enumerate(cams):
        ours_f = run / f'{a.name}_{i:02d}_{c["name"]}.png'
        if not ours_f.is_file():
            res[c['name']] = {'error': 'missing ' + ours_f.name}
            continue
        ref = cv2.imread(c['ref'])
        ours = cv2.resize(cv2.imread(str(ours_f)), (1920, 1080), interpolation=cv2.INTER_AREA)
        ref = cv2.resize(ref, (1920, 1080), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(run / f'pair_{c["name"]}.png'), np.hstack([ref, ours]))
        r, o = regions(ref), regions(ours)
        res[c['name']] = {'ours': {k: round(v, 5) for k, v in o.items()}, 'ref': {k: round(v, 5) for k, v in r.items()},
                          'ratio_ours_over_ref': {k: round(o[k] / r[k], 3) if r[k] > 1e-6 else None for k in o}}
    (run / 'pairs.json').write_text(json.dumps(res, indent=1))
    for n, v in res.items():
        if 'error' in v:
            print(n, v['error'])
        else:
            print('%-26s ratio ours/ref: %s' % (n, {k: x for k, x in v['ratio_ours_over_ref'].items()}))


if __name__ == '__main__':
    main()
