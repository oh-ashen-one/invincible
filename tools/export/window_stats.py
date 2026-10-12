#!/usr/bin/env python3
"""Window-glass brightness test (critic P1 r03 -> r04): share of WINDOW pixels above 80 % luminance inside a crop of a 4K capture.

The window mask comes from a second capture of the same view with the facade material in debug mode 3 (MPC_City.DebugMode = 3:
facade base colour black, no specular, emissive = red where the pixel is window glass). Both frames are rendered by the real game
at 3840x2160 from the same camera at the same game time.

usage: window_stats.py <lit.png> <mask.png> x,y,w,h [out_prefix]
prints: window pixel count, share > 80 % / > 60 % luminance, median luminance (Rec.709 luma of the 8-bit sRGB frame, 0..255 -> 0..1)
"""
import sys
import numpy as np
from PIL import Image

lit = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
mask = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32)
x, y, w, h = (int(v) for v in sys.argv[3].split(','))
L = lit[y:y + h, x:x + w]; M = mask[y:y + h, x:x + w]
# window pixel: red clearly above the other channels and above the noise floor of the masked (black) frame
win = (M[..., 0] > 40.0) & (M[..., 0] > 2.0 * np.maximum(M[..., 1], M[..., 2]) + 8.0)
lum = (0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]) / 255.0
n = int(win.sum())
if n == 0:
    print('window pixels: 0 (check the mask frame)'); sys.exit(1)
lw = lum[win]
print(f'crop {w}x{h} at {x},{y}: window pixels {n} ({100.0 * n / (w * h):.1f} % of the crop)')
print(f'  above 80 % luminance: {100.0 * (lw > 0.8).mean():.2f} %   above 60 %: {100.0 * (lw > 0.6).mean():.2f} %   '
      f'median {np.median(lw):.3f}   mean {lw.mean():.3f}   p95 {np.percentile(lw, 95):.3f}')
if len(sys.argv) > 4:
    ov = L.copy(); ov[win & (lum > 0.8)] = (255, 0, 255); ov[win & (lum <= 0.8)] = ov[win & (lum <= 0.8)] * 0.85 + np.array([0, 40, 0])
    Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)).save(sys.argv[4] + '_overlay.png')
    Image.fromarray(np.clip(L, 0, 255).astype(np.uint8)).save(sys.argv[4] + '_crop.png')
