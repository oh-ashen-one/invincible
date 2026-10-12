#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17 lineup instrument (critic r16 test): at the same camera, the share of pixels whose luma differs by more than 20 (of 255) between a capture and the previous CLEAN lineup,
plus a duplicate-weapon (ghost geometry) probe and the per-region split (the characters' bounding band vs the backdrop).

  python3 tools/ue_char/suits/lineup_diff_r17.py A.png REF.jpg [--thr 20] [--json OUT.json] [--diff-png OUT.png] [--band x0,y0,x1,y1]

Luma = Rec.601 of the 8-bit RGB (cv2 gray).  Both images are brought to the same size first (the committed lineups are 3840x2160 JPEG).  JPEG noise floor of the reference: measured
by `--floor` as the share of pixels > thr between the reference and itself re-encoded at the committed quality (q = 90 by default), so a pass is not flattered by compression.
The default character band is the lineup's: x 480-3400, y 640-1500 at 3840x2160 (the seven enemies stand in it; the wall panels and the floor are outside).
"""
import sys, json
import numpy as np, cv2


def luma(p):
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    return im, cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.int16)


def main():
    a = sys.argv[1]; b = sys.argv[2]
    thr = int(sys.argv[sys.argv.index('--thr') + 1]) if '--thr' in sys.argv else 20
    band = [480, 640, 3400, 1500]
    if '--band' in sys.argv: band = [int(v) for v in sys.argv[sys.argv.index('--band') + 1].split(',')]
    ia, la = luma(a); ib, lb = luma(b)
    if la.shape != lb.shape:
        ib = cv2.resize(ib, (ia.shape[1], ia.shape[0]), interpolation=cv2.INTER_AREA); lb = cv2.cvtColor(ib, cv2.COLOR_BGR2GRAY).astype(np.int16)
    d = np.abs(la - lb)
    m = d > thr
    x0, y0, x1, y1 = band
    inb = np.zeros_like(m); inb[y0:y1, x0:x1] = True
    out = dict(a=a, ref=b, thr=thr, size=[int(ia.shape[1]), int(ia.shape[0])], pct_over=round(100.0 * float(m.mean()), 3),
               pct_over_in_band=round(100.0 * float(m[inb].mean()), 3), pct_over_outside_band=round(100.0 * float(m[~inb].mean()), 3),
               p50=int(np.percentile(d, 50)), p99=int(np.percentile(d, 99)), mean_abs=round(float(d.mean()), 3), band=band)
    # tiles of 240 px: how many tiles hold > 20 % changed pixels (a blotch map)
    T = 240; H, W = m.shape
    tiles = [(x, y, round(float(m[y:y + T, x:x + T].mean()), 3)) for y in range(0, H - T + 1, T) for x in range(0, W - T + 1, T)]
    out['tiles_over_20pct'] = int(sum(1 for t in tiles if t[2] > 0.2)); out['tiles'] = len(tiles)
    if '--diff-png' in sys.argv:
        vis = np.clip(d * 4, 0, 255).astype(np.uint8)
        cv2.imwrite(sys.argv[sys.argv.index('--diff-png') + 1], cv2.resize(vis, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
    if '--json' in sys.argv: json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    print(json.dumps(out))


if __name__ == '__main__':
    main()
