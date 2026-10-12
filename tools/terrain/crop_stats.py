#!/usr/bin/env python3
"""Park-crop detail check (SPEC E1): high-pass standard deviation of 512 x 512 crops of pure grass.
For every image: luma Y (0..255), grass classifier (g > 1.02 r, g > 1.08 b, 40 <= Y <= 215), all windows of 512 px (stride 128) with >= 95 % grass pixels are candidates; the
3 candidates with the highest grass share (non-overlapping, ties by position) are the crops. hp-sd = std of Y - GaussianBlur(Y, sigma 6). Reports every crop plus the distribution
over ALL candidate windows (so nothing is cherry-picked). Exit code 0 always; the verdict is in the JSON (`pass_E1`: every selected crop >= 8 and >= 1 crop found).
usage: crop_stats.py out.json image [image ...]"""
import sys, json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, uniform_filter
SIZE, STRIDE, NSEL = 512, 128, 3
def luma(a): return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
def analyse(path):
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    Y = luma(im); r, g, b = im[..., 0], im[..., 1], im[..., 2]
    grass = (g > 1.02 * r) & (g > 1.08 * b) & (Y >= 40) & (Y <= 215)
    hp = Y - gaussian_filter(Y, 6.0)
    share = uniform_filter(grass.astype(np.float32), SIZE, mode='constant')[SIZE // 2::STRIDE, SIZE // 2::STRIDE]    # share of the window whose centre is at (i, j)
    cand = []
    for i in range(share.shape[0]):
        for j in range(share.shape[1]):
            y0, x0 = i * STRIDE, j * STRIDE
            if y0 + SIZE > Y.shape[0] or x0 + SIZE > Y.shape[1]: continue
            if share[i, j] >= 0.95: cand.append((float(share[i, j]), y0, x0))
    allsd = [float(hp[y0:y0 + SIZE, x0:x0 + SIZE].std()) for _, y0, x0 in cand]
    sel, taken = [], []
    for s, y0, x0 in sorted(cand, key=lambda c: (-c[0], c[1], c[2])):
        if any(abs(y0 - ty) < SIZE and abs(x0 - tx) < SIZE for ty, tx in taken): continue
        taken.append((y0, x0)); sd = float(hp[y0:y0 + SIZE, x0:x0 + SIZE].std())
        sel.append({'box_xywh': [x0, y0, SIZE, SIZE], 'grass_share': round(s, 3), 'hp_sd': round(sd, 2), 'mean_luma': round(float(Y[y0:y0 + SIZE, x0:x0 + SIZE].mean()), 1)})
        if len(sel) == NSEL: break
    return {'image': os.path.basename(path), 'size': [im.shape[1], im.shape[0]], 'grass_pixels_pct': round(100 * float(grass.mean()), 1), 'candidates': len(cand),
            'all_candidates_hp_sd': {'min': round(min(allsd), 2), 'median': round(float(np.median(allsd)), 2), 'max': round(max(allsd), 2)} if allsd else None, 'crops': sel}
out = sys.argv[1]; res = [analyse(p) for p in sys.argv[2:]]
flat = [c['hp_sd'] for r in res for c in r['crops']]
summary = {'pass_E1': bool(flat) and min(flat) >= 8.0, 'crops': len(flat), 'min_hp_sd': min(flat) if flat else None, 'images_without_crops': [r['image'] for r in res if not r['crops']]}
json.dump({'summary': summary, 'images': res}, open(out, 'w'), indent=1)
print(json.dumps(summary)); [print(r['image'], r['grass_pixels_pct'], '% grass px;', [c['hp_sd'] for c in r['crops']], 'candidates', r['candidates']) for r in res]
