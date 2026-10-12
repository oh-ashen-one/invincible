#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Per-frame colour / exposure numbers of a swing clip (mp4): same definitions as look_spec_check.py (luma .2126R+.7152G+.0722B of the 8-bit sRGB values, near-black Y < 10,
clipped = any channel >= 250, B-R = mean(B) - mean(R)), measured on frames decoded at 960x540 (ffmpeg). Prints the clip-level line for the spec rows: night swing B-R within
+-13 (L8), mean Y (L3 / L2 / L1 by preset), share of frames outside the B-R band.
usage: clip_check.py <clip.mp4> [--every 3] [--json out.json]"""
import argparse, json, subprocess, sys
import numpy as np
from scipy import ndimage as ndi

def frames(path, every):
    W, H = 960, 540
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', path, '-vf', 'scale=%d:%d:flags=area,select=not(mod(n\\,%d))' % (W, H, every), '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, dtype=np.uint8).reshape(H, W, 3).astype(np.float32)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('clip'); ap.add_argument('--every', type=int, default=3); ap.add_argument('--json')
    a = ap.parse_args()
    rows = []
    for f in frames(a.clip, a.every):
        Y = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
        lap = np.abs(ndi.laplace(ndi.gaussian_filter(Y, 0.8)))          # L18: motion blur = edge sharpness / centre sharpness (mean |Laplacian|; centre = middle 40 % x 40 %, edge = outer 20 % on each side)
        H, W = lap.shape; cen = lap[int(H * .3):int(H * .7), int(W * .3):int(W * .7)].mean()
        edge = np.concatenate([lap[:, :int(W * .2)].ravel(), lap[:, int(W * .8):].ravel(), lap[:int(H * .2), int(W * .2):int(W * .8)].ravel(), lap[int(H * .8):, int(W * .2):int(W * .8)].ravel()]).mean()
        rows.append({'mean': float(Y.mean()), 'br': float((f[..., 2] - f[..., 0]).mean()), 'lt10': float((Y < 10).mean() * 100), 'clip': float((f.max(axis=2) >= 250).mean() * 100), 'ec': float(edge / max(cen, 1e-6))})
    if not rows: sys.exit('no frames decoded')
    A = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    out = {'clip': a.clip, 'frames_measured': len(rows), 'every': a.every,
           'mean_Y': {'mean': float(A['mean'].mean()), 'min': float(A['mean'].min()), 'max': float(A['mean'].max())},
           'B_minus_R': {'mean': float(A['br'].mean()), 'min': float(A['br'].min()), 'max': float(A['br'].max()), 'p10': float(np.percentile(A['br'], 10)), 'p90': float(np.percentile(A['br'], 90))},
           'frames_outside_pm13_pct': float(((A['br'] < -13) | (A['br'] > 13)).mean() * 100), 'near_black_pct_mean': float(A['lt10'].mean()), 'clipped_pct_mean': float(A['clip'].mean()),
           'L18_edge_over_centre_sharpness': {'p10': float(np.percentile(A['ec'], 10)), 'p50': float(np.percentile(A['ec'], 50)), 'p90': float(np.percentile(A['ec'], 90))}}
    print(json.dumps(out, indent=1))
    if a.json: json.dump({**out, 'per_frame': rows}, open(a.json, 'w'), indent=1)

if __name__ == '__main__':
    main()
