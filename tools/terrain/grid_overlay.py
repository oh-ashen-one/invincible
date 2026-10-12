#!/usr/bin/env python3
"""Half-size copy of a 4K still with a labelled grid (default 150 px cells, labels col,row) for picking crop boxes by eye. usage: grid_overlay.py in.jpg out.jpg [cell px]"""
import sys
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 150
im = Image.open(src).convert('RGB'); W, H = im.size
sc = 0.5
im2 = im.resize((int(W * sc), int(H * sc)), Image.LANCZOS); d = ImageDraw.Draw(im2)
for x in range(0, W, step):
    d.line([(x * sc, 0), (x * sc, H * sc)], fill=(255, 255, 0), width=1)
for y in range(0, H, step):
    d.line([(0, y * sc), (W * sc, y * sc)], fill=(255, 255, 0), width=1)
for i, x in enumerate(range(0, W - step + 1, step)):
    for j, y in enumerate(range(0, H - step + 1, step)):
        d.text((x * sc + 3, y * sc + 2), '%d,%d' % (i, j), fill=(255, 255, 255))
im2.save(out, quality=88)
print(im2.size)
