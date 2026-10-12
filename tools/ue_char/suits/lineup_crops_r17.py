#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17: crop sheet of the weapon / garment regions of the 4K lineup, previous clean (r14) | r16 (corrupted) | r17, for the 'no duplicate weapon, no copper blotches' read.
  python3 tools/ue_char/suits/lineup_crops_r17.py OUT.jpg r14.jpg r16.jpg r17.jpg"""
import sys, cv2, numpy as np
out, *paths = sys.argv[1:]
BOXES = [('bat', (2860, 1000, 3260, 1240)), ('pistol L', (1020, 1020, 1320, 1250)), ('brute hands', (2060, 1010, 2760, 1200)), ('tee', (1380, 760, 1760, 1160)), ('hoodie', (2480, 760, 2880, 1160))]
ims = [cv2.imread(p) for p in paths]
rows = []
for nm, (x0, y0, x1, y1) in BOXES:
    row = []
    for im in ims:
        c = im[y0:y1, x0:x1]; s = 360.0 / c.shape[0]
        row.append(cv2.resize(c, (int(c.shape[1] * s), 360), interpolation=cv2.INTER_AREA))
    w = max(r.shape[1] for r in row)
    rows.append(np.hstack([cv2.copyMakeBorder(r, 0, 0, 0, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in row]))
W = max(r.shape[1] for r in rows)
sheet = np.vstack([cv2.copyMakeBorder(r, 0, 4, 0, W - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows])
cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
print(out, sheet.shape)
