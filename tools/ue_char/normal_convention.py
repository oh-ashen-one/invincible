#!/usr/bin/env python3
"""Decide whether a tangent-space normal map is OpenGL (+Y, glTF) or DirectX (-Y, Unreal) convention.
A normal map baked from a height field h has gradient field (dh/dcol, dh/drow) = (-nx/nz, +ny/nz) for OpenGL
(green points up the image) or (-nx/nz, -ny/nz) for DirectX. Only the right one is curl-free; we compare the
mean |curl| of both candidates. usage: normal_convention.py map.png [...]   (fan homage project)"""
import sys, numpy as np
from PIL import Image
for p in sys.argv[1:]:
    im = Image.open(p).convert('RGB')
    if max(im.size) > 2048:
        im = im.resize((2048, 2048), Image.BILINEAR)
    a = np.asarray(im).astype(np.float64) / 127.5 - 1.0
    nx, ny, nz = a[..., 0], a[..., 1], np.clip(a[..., 2], 0.2, None)
    res = {}
    for name, sy in (('OpenGL(+Y)', 1.0), ('DirectX(-Y)', -1.0)):
        gx = -nx / nz; gy = sy * ny / nz
        curl = np.gradient(gy, axis=1) - np.gradient(gx, axis=0)
        res[name] = float(np.mean(np.abs(curl)))
    best = min(res, key=res.get)
    print(p, {k: round(v, 5) for k, v in res.items()}, '->', best, 'ratio %.2f' % (max(res.values()) / max(1e-9, min(res.values()))))
