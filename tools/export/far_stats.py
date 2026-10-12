#!/usr/bin/env python3
"""Far-field numbers for the round-06 test (critic r05 gap: S4 / far skyline), from a 4K frame + a mask frame (MPC_City.DebugMode = 3:
coast / far-land = red, water = blue, far-shore blocks (M_CityFarMass) = green; every other material renders normally).
Reports inside the crop x0-x1, y0-y1 (default the critic's strip 0-2800, 550-700):
  shore-strip mean luma vs water mean luma (Rec.709 of the 8-bit sRGB frame, 0..1); mean R, G, B and |R-B| of far-shore-block pixels;
  and, for the whole far-field band, mean RGB / |R-B| of the non-water, non-sky pixels in the band y0-y1.
usage: far_stats.py <lit.png> <mask.png> [x0 y0 x1 y1]"""
import sys, numpy as np
from PIL import Image
lit = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32); m = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32)
x0, y0, x1, y1 = [int(v) for v in sys.argv[3:7]] if len(sys.argv) >= 7 else (0, 550, 2800, 700)
L = lit[y0:y1, x0:x1]; M = m[y0:y1, x0:x1]
# haze / aerial perspective add a grey-blue veil (~75 / 255) to every pixel, so the masks are detected by channel differences, not absolute levels
Rr, Gg, Bb = M[..., 0], M[..., 1], M[..., 2]
red = (Rr - Gg > 30) & (Rr - Bb > 25); blue = (Bb - Rr > 45) & (Bb - Gg > 40); green = (Gg - Rr > 30) & (Gg - Bb > 25)
lum = (0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]) / 255.0
def rep(name, k):
    n = int(k.sum())
    if n == 0: print(f'{name}: 0 px'); return None
    v = lum[k]; c = L[k].mean(0)
    print(f'{name}: {n} px, mean luma {v.mean():.3f} (median {np.median(v):.3f}), mean RGB ({c[0]:.0f}, {c[1]:.0f}, {c[2]:.0f}), |R-B| {abs(c[0]-c[2]):.1f}')
    return v.mean()
a = rep('shore strip (coast / far land)', red); b = rep('water', blue); rep('far-shore blocks (farCityMass)', green)
if a is not None and b is not None: print(f'shore strip {"DARKER" if a < b else "LIGHTER"} than water by {abs(a-b):.3f}')
