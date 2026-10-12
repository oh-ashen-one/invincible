#!/usr/bin/env python3
"""Luminance statistics on masks picked in the REFERENCE image (matched cameras: the same pixels in ours).
  boards  : TS / sign boards = pixels of the reference above a linear-luminance threshold (default 0.25), cleaned by a 5 px opening, keeping connected components of at least MINPX px;
            ours/ref = mean linear luminance of ours over the same mask / of the reference over the mask (target ~1.0)
  leaves  : green-dominant pixels of the reference (G > 1.15 R and G > 1.15 B, luminance > 0.004) cleaned the same way, same measure
  windows : the lit-window pixels of the reference middle third (luma > 0.1): median luminance ours vs ref over their own > 0.1 pixels, plus the share of the middle third
usage: regions.py <run dir> <shot name> [<shot name> ...] [--thr 0.25] [--min 300]"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

CAMS = json.loads((Path.home() / 'sm2-n1/_scratch/night/ref/shot_cams.json').read_text())


def lin(img):
    x = img[..., ::-1].astype(np.float32) / 255
    x = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2], x


def load(f):
    return cv2.resize(cv2.imread(str(f)), (1920, 1080), interpolation=cv2.INTER_AREA)


def clean(mask, minpx):
    m = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= minpx:
            keep[lab == i] = 1
    return keep.astype(bool)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('shots', nargs='+')
    ap.add_argument('--thr', type=float, default=0.25)
    ap.add_argument('--min', type=int, default=300)
    ap.add_argument('--name', default='night')
    a = ap.parse_args()
    out = {}
    for shot in a.shots:
        i = [c['name'] for c in CAMS].index(shot)
        ref = load(CAMS[i]['ref'])
        ours = load(Path(a.run) / f'{a.name}_{i:02d}_{shot}.png')
        Lr, Xr = lin(ref)
        Lo, _ = lin(ours)
        r = {}
        bm = clean(Lr > a.thr, a.min)
        r['boards'] = {'pixels': int(bm.sum()), 'ref_mean': round(float(Lr[bm].mean()), 4) if bm.any() else None, 'ours_mean': round(float(Lo[bm].mean()), 4) if bm.any() else None,
                       'ratio': round(float(Lo[bm].mean() / Lr[bm].mean()), 3) if bm.any() else None}
        lm = clean((Xr[..., 1] > Xr[..., 0] * 1.15) & (Xr[..., 1] > Xr[..., 2] * 1.15) & (Lr > 0.004), a.min)
        r['leaves'] = {'pixels': int(lm.sum()), 'ref_mean': round(float(Lr[lm].mean()), 4) if lm.any() else None, 'ours_mean': round(float(Lo[lm].mean()), 4) if lm.any() else None,
                       'ratio': round(float(Lo[lm].mean() / Lr[lm].mean()), 3) if lm.any() else None}
        h = Lr.shape[0]
        mr, mo = Lr[h // 3:2 * h // 3], Lo[h // 3:2 * h // 3]
        wr, wo = mr[mr > 0.1], mo[mo > 0.1]
        r['windows'] = {'share_ref': round(float((mr > 0.1).mean()), 4), 'share_ours': round(float((mo > 0.1).mean()), 4),
                        'median_lit_ref': round(float(np.median(wr)), 4) if wr.size else None, 'median_lit_ours': round(float(np.median(wo)), 4) if wo.size else None,
                        'median_ratio': round(float(np.median(wo) / np.median(wr)), 3) if wr.size and wo.size else None}
        out[shot] = r
        cv2.imwrite(str(Path(a.run) / f'mask_boards_{shot}.png'), (bm * 255).astype(np.uint8))
    print(json.dumps(out, indent=1))
    Path(a.run, 'regions.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
