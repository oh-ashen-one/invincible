#!/usr/bin/env python3
"""Window-glass brightness numbers for a round (critic P1 r03 test): for each region of interest of the 4K captures, the 400 x 400 px crop with
the MOST window pixels (chosen from the mask frame only, so brightness never influences the choice) is measured: share of window pixels above
80 % / 60 % luminance, median and mean luminance (Rec.709 luma of the 8-bit sRGB frame, 0..1).

usage: window_stats_round.py <lit_dir> <mask_dir> <out_json> [out_dir_for_crops]
  lit_dir : <id>_3840x2160_00_t028.0.png (normal frames)      mask_dir : same names, facade debug mode 3 (MPC_City.DebugMode = 3)
"""
import json, os, sys
import numpy as np
from PIL import Image

LIT, MASK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CROPS = sys.argv[4] if len(sys.argv) > 4 else None
S = 400
# (label, shot id, ROI x0, y0, x1, y1 in 4K pixels)
ROIS = [
    ('S1 right facade (tower right of the avenue)', 'S1_avenue_street', 2700, 0, 3500, 1000),
    ('S8 brick tower (centre right)', 'S8_aerial_midtown', 1950, 1150, 2550, 2000),
    ('S8 brick tower (left)', 'S8_aerial_midtown', 1450, 1100, 1950, 1700),
    ('S2 left stone tower', 'S2_avenue_swing', 0, 60, 1560, 1900),
    ('S7 left glass wall', 'S7_sunset_crosstown', 0, 0, 1000, 2160),
    ('S7 right masonry wall', 'S7_sunset_crosstown', 2600, 0, 3840, 2160),
]

def window_mask(m):
    return (m[..., 0] > 40.0) & (m[..., 0] > 2.0 * np.maximum(m[..., 1], m[..., 2]) + 8.0)

res = []
for label, sid, x0, y0, x1, y1 in ROIS:
    def find(d):  # capture_round.sh names frames <id>_3840x2160_..., capture_one.sh <short id>_3840x2160_...
        for n in (sid, sid.split('_')[0]):
            f = f'{d}/{n}_3840x2160_00_t028.0.png'
            if os.path.exists(f): return f
        return f
    lp, mp = find(LIT), find(MASK)
    if not (os.path.exists(lp) and os.path.exists(mp)): print('missing', sid); continue
    L = np.asarray(Image.open(lp).convert('RGB')).astype(np.float32); M = np.asarray(Image.open(mp).convert('RGB')).astype(np.float32)
    W = window_mask(M)
    best, bxy = -1, None
    for y in range(y0, max(y0 + 1, y1 - S + 1), 40):
        for x in range(x0, max(x0 + 1, x1 - S + 1), 40):
            c = int(W[y:y + S, x:x + S].sum())
            if c > best: best, bxy = c, (x, y)
    x, y = bxy
    lum = (0.2126 * L[y:y + S, x:x + S, 0] + 0.7152 * L[y:y + S, x:x + S, 1] + 0.0722 * L[y:y + S, x:x + S, 2]) / 255.0
    w = W[y:y + S, x:x + S]; lw = lum[w]
    r = {'region': label, 'shot': sid, 'crop_xywh': [x, y, S, S], 'window_pixels': int(w.sum()), 'window_share_of_crop_pct': round(100.0 * w.sum() / (S * S), 1),
         'above_80pct_luminance_pct': round(100.0 * float((lw > 0.8).mean()), 2), 'above_60pct_luminance_pct': round(100.0 * float((lw > 0.6).mean()), 2),
         'median_luminance': round(float(np.median(lw)), 3), 'mean_luminance': round(float(lw.mean()), 3), 'p95_luminance': round(float(np.percentile(lw, 95)), 3)}
    res.append(r); print(json.dumps(r))
    if CROPS:
        os.makedirs(CROPS, exist_ok=True)
        tag = sid.split('_')[0] + '_' + label.split('(')[0].strip().replace(' ', '_')
        Image.fromarray(np.clip(L[y:y + S, x:x + S], 0, 255).astype(np.uint8)).save(f'{CROPS}/{tag}_crop.jpg', quality=90)
        ov = L[y:y + S, x:x + S].copy(); hi = w & (lum > 0.8); ov[hi] = (255, 0, 255)
        Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)).save(f'{CROPS}/{tag}_over80.jpg', quality=90)
json.dump(res, open(OUT, 'w'), indent=1)
