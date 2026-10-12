#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 11: exposure calibration helper for the skins stage (AEM_Manual: the stage's sun is 8 lux, so the bias that matches auto exposure's floor level is found by measurement).

  python3 tools/ue_char/suits/ev_calib.py luma  IMAGE            -> prints the mean sRGB luma of the bare-floor patch (bottom right of the front shot)
  python3 tools/ue_char/suits/ev_calib.py next  CALIB.txt [target] -> CALIB.txt has lines 'EV luma'; prints the next EV to try (secant / linear fit over the two nearest points), or 'DONE <ev>'
Target luma 170 = what auto exposure gave the same floor in the first round-11 chain (tessera front 170.3, plum front 171.5).
"""
import sys
from PIL import Image
import numpy as np


def luma(path):
    im = np.asarray(Image.open(path).convert('RGB')).astype(float)
    H, W = im.shape[:2]
    m = im[int(H * .86):int(H * .97), int(W * .72):int(W * .96)].reshape(-1, 3).mean(0)
    return float(0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2])


def nxt(path, target):
    pts = sorted({(float(a), float(b)) for a, b in (l.split()[:2] for l in open(path) if l.strip())})
    close = [p for p in pts if abs(p[1] - target) <= 8]
    if close: return 'DONE %.2f' % min(close, key=lambda p: abs(p[1] - target))[0]
    if len(pts) < 2: return '%.2f' % (pts[0][0] + (3.0 if pts[0][1] < target else -3.0))
    pts.sort(key=lambda p: abs(p[1] - target))
    (e1, l1), (e2, l2) = pts[0], pts[1]
    if abs(l2 - l1) < 1.0: return '%.2f' % (e1 + (1.5 if l1 < target else -1.5))
    e = e1 + (target - l1) * (e2 - e1) / (l2 - l1)
    return '%.2f' % max(5.0, min(13.0, e))


if __name__ == '__main__':
    if sys.argv[1] == 'luma': print('%.1f' % luma(sys.argv[2]))
    else: print(nxt(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 170.0))
