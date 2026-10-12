#!/usr/bin/env python3
"""Lawn crop metrics (round 04): sigma-6 high-pass SD (luma 0-255) and mean HSV saturation of named crops (x, y, w, h) of an image.
Used for the r04 pass criteria (a, b) on the critic's crops and the like-for-like guard boxes, and for the reference frames (same tool, optional --scale to put a 1080p reference on the 4K output grid).
usage: lawn_stats.py out.json image:x,y,w,h[:label] ... [--scale 2]  (box given in the image's own pixels AFTER scaling)"""
import sys, json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
args = sys.argv[1:]; out = args.pop(0); scale = 1.0
if '--scale' in args:
    i = args.index('--scale'); scale = float(args[i + 1]); del args[i:i + 2]
def hsv_sat(a):
    mx = a.max(-1); mn = a.min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
cache = {}; res = []
for spec in args:
    parts = spec.split(':'); path = parts[0]; x, y, w, h = [int(v) for v in parts[1].split(',')]; label = parts[2] if len(parts) > 2 else ''
    if path not in cache:
        im = Image.open(path).convert('RGB')
        if scale != 1.0: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32); Y = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
        cache[path] = (a, Y, Y - gaussian_filter(Y, 6.0), Y - gaussian_filter(Y, 3.0))
    a, Y, hp6, hp3 = cache[path]
    c = a[y:y + h, x:x + w]
    res.append({'image': os.path.basename(path), 'box_xywh': [x, y, w, h], 'label': label, 'hp6_sd': round(float(hp6[y:y + h, x:x + w].std()), 2), 'hp3_sd': round(float(hp3[y:y + h, x:x + w].std()), 2),
                'mean_hsv_sat': round(float(hsv_sat(c / 255.0).mean()), 3), 'mean_luma': round(float(Y[y:y + h, x:x + w].mean()), 1), 'mean_rgb': [round(float(v), 1) for v in c.reshape(-1, 3).mean(0)]})
json.dump({'scale': scale, 'crops': res}, open(out, 'w'), indent=1)
for r in res: print(r['image'], r['box_xywh'], r['label'], 'hp6 %.2f hp3 %.2f sat %.3f luma %.1f rgb %s' % (r['hp6_sd'], r['hp3_sd'], r['mean_hsv_sat'], r['mean_luma'], r['mean_rgb']))
