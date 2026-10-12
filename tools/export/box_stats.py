#!/usr/bin/env python3
"""(r11) share of pixels above Y 204 (+ mean / p95 / p99) of one box of a frame at 1920x1080 coordinates (a 4K frame is reduced first).
usage: box_stats.py <frame> x0 y0 x1 y1 [more frames...]    e.g. box_stats.py S8.png 1270 0 1640 300"""
import sys, cv2, numpy as np
a = sys.argv[1:]; x0, y0, x1, y1 = [int(v) for v in a[1:5]]; files = [a[0]] + a[5:]
for f in files:
    im = cv2.imread(f); im = im if im.shape[1] == 1920 else cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA)
    Y = 0.2126 * im[:, :, 2] + 0.7152 * im[:, :, 1] + 0.0722 * im[:, :, 0]; b = Y[y0:y1, x0:x1]
    print('%s box(%d,%d,%d,%d): > 204 %.2f %%  mean Y %.1f  p95 %.0f  p99 %.0f' % (f.split('/')[-1], x0, y0, x1, y1, (b > 204).mean() * 100, b.mean(), np.percentile(b, 95), np.percentile(b, 99)))
