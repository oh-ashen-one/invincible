#!/usr/bin/env python3
"""Park-crop detail (SPEC E1) on hand-picked lawn crops: hp-sd = std of Y - GaussianBlur(Y, sigma 6) on 512 x 512 boxes from docs/night1/terrain/crops.json.
usage: crop_manual.py <stills dir> <crops.json> <out.json>"""
import sys, json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
d, cj, out = sys.argv[1:4]; C = json.load(open(cj))['crops']; res = []
for f, boxes in C.items():
    p = os.path.join(d, f)
    if not os.path.exists(p): continue
    im = np.asarray(Image.open(p).convert('RGB')).astype(np.float32); Y = 0.299 * im[..., 0] + 0.587 * im[..., 1] + 0.114 * im[..., 2]; hp = Y - gaussian_filter(Y, 6.0)
    for x, y in boxes:
        c = hp[y:y + 512, x:x + 512]; res.append({'image': f, 'box_xywh': [x, y, 512, 512], 'hp_sd': round(float(c.std()), 2), 'mean_luma': round(float(Y[y:y + 512, x:x + 512].mean()), 1)})
s = {'pass_E1': bool(res) and min(r['hp_sd'] for r in res) >= 8.0, 'crops': len(res), 'min_hp_sd': min((r['hp_sd'] for r in res), default=None), 'max_hp_sd': max((r['hp_sd'] for r in res), default=None)}
json.dump({'summary': s, 'crops': res}, open(out, 'w'), indent=1); print(json.dumps(s)); [print(r['image'], r['box_xywh'][:2], r['hp_sd'], r['mean_luma']) for r in res]
