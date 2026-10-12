#!/usr/bin/env python3
"""Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
Blind critic pack helper (piece E, r04): next to every pack image wider than 2048 px add a viewer-friendly copy `<name>_2048.jpg` (2048 px wide, same crop, metadata stripped).
The originals stay untouched (the critic's pixel measurements use them). usage: pack_small.py <pack_dir>"""
import os, sys
from PIL import Image
pack = sys.argv[1]; n = 0
for root, _, files in os.walk(pack):
    for f in sorted(files):
        if not f.lower().endswith('.jpg') or f.endswith('_2048.jpg'): continue
        p = os.path.join(root, f)
        im = Image.open(p)
        if im.width <= 2048: continue
        h = round(im.height * 2048 / im.width)
        im.convert('RGB').resize((2048, h), Image.LANCZOS).save(os.path.join(root, f[:-4] + '_2048.jpg'), quality=90)
        n += 1
print('added %d x _2048.jpg in %s' % (n, pack))
