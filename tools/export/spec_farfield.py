#!/usr/bin/env python3
"""CITY-SPEC section 4 numbers (C11-C15) for an S4-type capture, same instrument as specs/tools/haze_regions.py:
the frame is downscaled to 1920x1080 (INTER_AREA); per region: mean RGB, B-R, luma Y = .2126R+.7152G+.0722B, RMS contrast (std Y / mean Y), mean |Laplacian|.
Regions are ours (S4_perch_skyline, 1920x1080 coordinates), placed like the reference boxes: sky band, horizon_far (far hinterland row),
far_shore (the buildings across the river), river, near_city.   usage: spec_farfield.py <S4 png> [out.json]"""
import sys, json
import cv2, numpy as np
im = cv2.resize(cv2.imread(sys.argv[1]), (1920, 1080), interpolation=cv2.INTER_AREA).astype(np.float32)
REG = {'sky': (0, 0, 1920, 100), 'horizon_far': (0, 150, 1920, 215), 'far_shore': (0, 215, 900, 300), 'river': (450, 330, 1250, 400), 'mid_city': (1450, 330, 1750, 480), 'near_city': (0, 700, 500, 1000)}
out = {}
for name, (x0, y0, x1, y1) in REG.items():
    c = im[y0:y1, x0:x1]; b, g, r = c[..., 0], c[..., 1], c[..., 2]; Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    lap = float(np.abs(cv2.Laplacian(Y, cv2.CV_32F)).mean())
    blocks = Y[:Y.shape[0] // 8 * 8, :Y.shape[1] // 8 * 8].reshape(Y.shape[0] // 8, 8, Y.shape[1] // 8, 8).std(axis=(1, 3))
    out[name] = dict(R=float(r.mean()), G=float(g.mean()), B=float(b.mean()), BminusR=float(b.mean() - r.mean()), Y=float(Y.mean()), rms=float(Y.std() / max(Y.mean(), 1)), lap=lap, flat8x8_pct=float((blocks < 1.5).mean() * 100))
sky = out['sky']
for k, v in out.items(): print(f"  {k:12s} RGB ({v['R']:5.1f},{v['G']:5.1f},{v['B']:5.1f}) B-R {v['BminusR']:+6.1f}  Y {v['Y']:5.1f}  rms {v['rms']:.3f}  lap {v['lap']:5.2f}  flat8x8 {v['flat8x8_pct']:4.1f} %")
fs, hz, rv, nc = out['far_shore'], out['horizon_far'], out['river'], out['near_city']
res = {
 'C11 far-shore lap / sky lap (target >= 6)': round(fs['lap'] / max(sky['lap'], 1e-6), 2), 'C11 horizon_far lap / sky lap': round(hz['lap'] / max(sky['lap'], 1e-6), 2),
 'C11 far-shore flat 8x8 blocks % (target <= 40)': round(fs['flat8x8_pct'], 1),
 'C12 far-shore (B-R) minus sky (B-R) (target within +-10)': round(fs['BminusR'] - sky['BminusR'], 1),
 'C13 far-shore Y minus sky Y (target -35..-25)': round(fs['Y'] - sky['Y'], 1), 'C13 near_city Y': round(nc['Y'], 1),
 'C14 far-shore Y minus river Y (target 5..35)': round(fs['Y'] - rv['Y'], 1),
 'C15 rms far_shore / near_city (target 0.25..0.45)': round(fs['rms'] / max(nc['rms'], 1e-6), 2)}
for k, v in res.items(): print(k, '=', v)
if len(sys.argv) > 2: json.dump({'regions': out, 'spec': res}, open(sys.argv[2], 'w'), indent=1)
