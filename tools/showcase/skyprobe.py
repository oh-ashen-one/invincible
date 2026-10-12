#!/usr/bin/env python3
"""sky calibration probe: linear luminance statistics of the top 10 % rows of one shot (reference vs our runs), median / mean / p10 / p90 and the median linear RGB.
usage: skyprobe.py <shot name> <run-name> [<run-name> ...]   (runs under ~/sm2-n1/_scratch/showcase/runs, matched-camera files night_<NN>_<shot>.png)"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

R = Path.home() / 'sm2-n1/_scratch/showcase/runs'
CAMS = json.loads((Path.home() / 'sm2-n1/_scratch/night/ref/shot_cams.json').read_text())


def lin(x):
    x = x.astype(np.float32) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def load(f):
    return cv2.resize(cv2.imread(str(f)), (1920, 1080), interpolation=cv2.INTER_AREA)


def main():
    shot, runs = sys.argv[1], sys.argv[2:]
    idx = [c['name'] for c in CAMS].index(shot)
    items = [('ref', load(CAMS[idx]['ref']))] + [(r, load(R / r / f'night_{idx:02d}_{shot}.png')) for r in runs]
    for lab, im in items:
        l = lin(im[..., ::-1])
        L = (0.2126 * l[..., 0] + 0.7152 * l[..., 1] + 0.0722 * l[..., 2])[:108]
        print('%-8s top10%%: median %.4f mean %.4f p10 %.4f p90 %.4f | median linear rgb %s' % (lab, np.median(L), L.mean(), np.percentile(L, 10), np.percentile(L, 90), np.round(np.median(l[:108].reshape(-1, 3), 0), 4)))


if __name__ == '__main__':
    main()
