#!/usr/bin/env python3
"""1920x1080 contact sheet of the PNGs matching a glob: sheet.py <dir> <glob> <out.png> [--cols 4] [--label-split _]
tiles of 1920/cols wide (16:9), rows as needed, black padding to 1080."""
import argparse
from pathlib import Path

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('dir'); ap.add_argument('glob'); ap.add_argument('out')
ap.add_argument('--cols', type=int, default=4)
a = ap.parse_args()
files = sorted(Path(a.dir).glob(a.glob))
w = 1920 // a.cols; h = w * 9 // 16
rows = (len(files) + a.cols - 1) // a.cols
sheet = np.zeros((max(1080, rows * h), 1920, 3), np.uint8)
for k, f in enumerate(files):
    im = cv2.resize(cv2.imread(str(f)), (w, h), interpolation=cv2.INTER_AREA)
    label = f.stem.split('_', 2)[-1] if f.stem.count('_') >= 2 else f.stem
    cv2.putText(im, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    sheet[(k // a.cols) * h:(k // a.cols + 1) * h, (k % a.cols) * w:(k % a.cols + 1) * w] = im
cv2.imwrite(a.out, sheet[:max(1080, rows * h)])
print(a.out, len(files), 'tiles', sheet.shape[1], 'x', sheet.shape[0])
