#!/usr/bin/env python3
"""before/after pairs of two capture dirs (same file names): <out>/ab_<name>.png = A left, B right (each 1920x1080) and a stats line per pair: mean linear luma A / B, mean abs diff (sRGB 0..255), 99th percentile diff.
usage: ab_pair.py <dirA> <dirB> <out dir> [--glob 'night_*.png']"""
import json, sys
from pathlib import Path
import cv2, numpy as np
A, B, O = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); O.mkdir(parents=True, exist_ok=True)
pat = sys.argv[sys.argv.index('--glob') + 1] if '--glob' in sys.argv else 'night_*.png'
def lin(im): x = im[..., ::-1].astype(np.float32) / 255; x = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4); return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
out = {}
for f in sorted(A.glob(pat)):
    g = B / f.name
    if not g.exists(): continue
    a = cv2.resize(cv2.imread(str(f)), (1920, 1080), interpolation=cv2.INTER_AREA); b = cv2.resize(cv2.imread(str(g)), (1920, 1080), interpolation=cv2.INTER_AREA)
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).mean(2)
    def canopy(im):   # green-dominant pixels: mean linear luma and share (the perf round's canopy gate)
        x = im[..., ::-1].astype(np.float32) / 255; m = (x[..., 1] > x[..., 0] * 1.15) & (x[..., 1] > x[..., 2] * 1.15) & (x[..., 1] > 0.02)
        return (round(float(lin(im)[m].mean()), 4) if m.any() else None), round(float(m.mean()), 4)
    ca, cb = canopy(a), canopy(b)
    out[f.stem] = {'canopy_luma_A': ca[0], 'canopy_luma_B': cb[0], 'canopy_ratio_B_over_A': (round(cb[0] / ca[0], 3) if ca[0] and cb[0] else None), 'canopy_share_A': ca[1], 'canopy_share_B': cb[1], 'luma_A': round(float(lin(a).mean()), 4), 'luma_B': round(float(lin(b).mean()), 4), 'mean_abs_diff': round(float(d.mean()), 2), 'p99_diff': round(float(np.percentile(d, 99)), 1)}
    cv2.imwrite(str(O / ('ab_' + f.stem + '.png')), np.hstack([a, b]))
    print(f.stem, out[f.stem])
(O / 'ab_stats.json').write_text(json.dumps(out, indent=1))
