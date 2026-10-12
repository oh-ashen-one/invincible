#!/usr/bin/env python3
"""(r11) settle-frames check: every capture takes two screenshots (the first at t = 34 s, the second at t = 38 s of game time). If assets were still compiling / streaming / the exposure still adapting, the pair differs.
Reports per view: mean absolute luma difference and the share of pixels differing by > 8 levels (TSR jitter and cloud drift give ~0.3-1.5 levels / < 1 %; a streaming pop-in gives clusters).
usage: settle_check.py <raw_dir> [--json out.json]     (files <ID>_<WxH>_00_t034.0.png / _01_t038.0.png)"""
import sys, os, glob, json
import numpy as np, cv2
raw = sys.argv[1]; out = []
for a in sorted(glob.glob(os.path.join(raw, '*_00_t0*.png'))):
    g = glob.glob(a.split('_00_t0')[0] + '_01_t0*.png')
    if not g: continue
    b = g[0]
    A = cv2.imread(a).astype(np.float32); B = cv2.imread(b).astype(np.float32)
    ya = 0.2126 * A[:, :, 2] + 0.7152 * A[:, :, 1] + 0.0722 * A[:, :, 0]; yb = 0.2126 * B[:, :, 2] + 0.7152 * B[:, :, 1] + 0.0722 * B[:, :, 0]
    d = np.abs(ya - yb); name = os.path.basename(a).split('_00_t0')[0]
    r = dict(view=name, mean_abs_luma_diff=round(float(d.mean()), 3), pct_gt8=round(float((d > 8).mean() * 100), 3), mean_luma_t24=round(float(ya.mean()), 2), mean_luma_t28=round(float(yb.mean()), 2))
    out.append(r); print('%-34s mean|dY| %.3f  >8 levels %.3f %%  mean Y %.1f -> %.1f' % (name, r['mean_abs_luma_diff'], r['pct_gt8'], r['mean_luma_t24'], r['mean_luma_t28']))
if '--json' in sys.argv: json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
