#!/usr/bin/env python3
"""CITY-SPEC C1 / C2 facade brightness check. Facade-only mask = MPC_City.DebugMode 11 frame (facade material pixels red, everything else normal).
For each region of a 4K capture, the 400 x 400 crop with the most facade pixels (chosen from the mask only) is measured over its facade pixels:
share with Y > 204 (80 %), p95 Y, p99 Y, mean Y (Y = .2126R+.7152G+.0722B of the 8-bit sRGB frame; the spec measures 1920x1080 crops of refs, here 4K crops).
Targets (daylight): C1 <= 1.5 % above 204, p95 <= 192, p99 <= 206; C2 mean Y 52..119.
usage: facade_c1.py <lit_dir> <mask_dir> <out.json> [crop_dir]"""
import json, os, sys
import numpy as np
from PIL import Image
LIT, MASK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; CROPS = sys.argv[4] if len(sys.argv) > 4 else None
S = 400
ROIS = [('S1 right tower', 'S1', 2700, 0, 3500, 1000), ('S1 left buildings', 'S1', 0, 0, 1500, 800), ('S2 left stone tower', 'S2', 0, 60, 1560, 1900), ('S2 right glass tower', 'S2', 2300, 0, 3840, 1400),
        ('S7 left glass wall (sunset)', 'S7', 0, 0, 1000, 2160), ('S7 right masonry wall (sunset)', 'S7', 2600, 0, 3840, 2160), ('S8 brick towers centre', 'S8', 1450, 1100, 2550, 2000)]
res = []
for label, sid, x0, y0, x1, y1 in ROIS:
    def find(d):
        for n in (sid, {'S1': 'S1_avenue_street', 'S2': 'S2_avenue_swing', 'S7': 'S7_sunset_crosstown', 'S8': 'S8_aerial_midtown'}[sid]):
            f = f'{d}/{n}_3840x2160_00_t028.0.png'
            if os.path.exists(f): return f
        return None
    lp, mp = find(LIT), find(MASK)
    if not (lp and mp): print('missing', label); continue
    L = np.asarray(Image.open(lp).convert('RGB')).astype(np.float32); M = np.asarray(Image.open(mp).convert('RGB')).astype(np.float32)
    Rr, Gg, Bb = M[..., 0], M[..., 1], M[..., 2]; F = (Rr - Gg > 30) & (Rr - Bb > 30)
    best, bxy = -1, None
    for y in range(y0, max(y0 + 1, min(y1, 2160) - S + 1), 40):
        for x in range(x0, max(x0 + 1, min(x1, 3840) - S + 1), 40):
            c = int(F[y:y + S, x:x + S].sum())
            if c > best: best, bxy = c, (x, y)
    x, y = bxy; Y = (0.2126 * L[y:y + S, x:x + S, 0] + 0.7152 * L[y:y + S, x:x + S, 1] + 0.0722 * L[y:y + S, x:x + S, 2]); f = F[y:y + S, x:x + S]; v = Y[f]
    if v.size < 5000: print('too few facade pixels', label, v.size); continue
    r = {'region': label, 'crop_xywh': [x, y, S, S], 'facade_pixels': int(v.size), 'pct_above_204': round(100 * float((v > 204).mean()), 2), 'p95': round(float(np.percentile(v, 95)), 1),
         'p99': round(float(np.percentile(v, 99)), 1), 'mean_Y': round(float(v.mean()), 1)}
    r['C1_pass'] = bool(r['pct_above_204'] <= 1.5 and r['p95'] <= 192 and r['p99'] <= 206); r['C2_pass'] = bool(52 <= r['mean_Y'] <= 119)
    res.append(r); print(json.dumps(r))
    if CROPS:
        os.makedirs(CROPS, exist_ok=True); tag = label.split('(')[0].strip().replace(' ', '_')
        Image.fromarray(np.clip(L[y:y + S, x:x + S], 0, 255).astype(np.uint8)).save(f'{CROPS}/{tag}_crop.jpg', quality=90)
json.dump(res, open(OUT, 'w'), indent=1)
