#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: crop-level look check of a perf change (round-01 critic, "restore the reflections and lit windows"): SSIM / PSNR / warm-pixel
fraction / mean luma of named crops of the S1 / S2 4K stills, test vs reference (the as-found hardware-RT look).
SSIM = the same 8x8 box SSIM on luma as compare_stills.py, computed on the 1920x1080 area-downsample of each still (crop coordinates below
are in 1920x1080 space; multiply by 2 for the 3840x2160 file); `ssim_full` repeats it on the full-resolution crop (stricter).
Crops (1920x1080 space, from the round-01 stills): S1_glass = the glass tower left of the vanishing point, S2_windows = the lit windows of
the left stone tower, S2_gold = the gold glass tower on the right. A candidate PASSES when every crop of a view is >= --thr (default 0.97).
warm = fraction of crop pixels with R - B > 40 and R > 90 (8-bit, sRGB PNG): the "lit windows / warm reflections" measure of the critic.
usage: crop_ssim.py <ref_dir> <test_dir> [<test_dir> ...] [--json out.json] [--thr 0.97] [--views S1,S2] [--sbs <dir>]   (files view_S1.png / view_S2.png)"""
import argparse, json, os
import numpy as np, cv2

CROPSETS = {
    # round 02 (old city): S1 glass tower left of the vanishing point
    'r02': {'S1': {'S1_glass': (485, 0, 710, 490)}, 'S2': {'S2_windows': (0, 38, 576, 960), 'S2_gold': (1459, 0, 1920, 1056)}},
    # round 03 (rebuilt integrated city: street trees now cover the r02 S1 crop; the glass curtain wall + the window tower behind it sit at x 775-900, y 0-215; the street-tree crown enters the frame below y 215)
    'r03': {'S1': {'S1_glass': (775, 0, 900, 215)}, 'S2': {'S2_windows': (0, 38, 576, 960), 'S2_gold': (1459, 0, 1920, 1056)}},
}
CROPS = CROPSETS['r03']


def luma(img): return (0.2126 * img[..., 2] + 0.7152 * img[..., 1] + 0.0722 * img[..., 0]).astype(np.float64)


def ssim(a, b, k=8):
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    f = lambda x: cv2.blur(x, (k, k))
    ma, mb = f(a), f(b)
    va, vb, cov = f(a * a) - ma * ma, f(b * b) - mb * mb, f(a * b) - ma * mb
    s = ((2 * ma * mb + C1) * (2 * cov + C2)) / ((ma * ma + mb * mb + C1) * (va + vb + C2))
    return float(s.mean())


def warm(img):
    b, g, r = [img[..., i].astype(np.int16) for i in range(3)]
    return float(((r - b > 40) & (r > 90)).mean() * 100)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ref'); ap.add_argument('tests', nargs='+'); ap.add_argument('--json'); ap.add_argument('--thr', type=float, default=0.97)
    ap.add_argument('--views', default='S1,S2'); ap.add_argument('--sbs'); ap.add_argument('--set', default='r03', choices=sorted(CROPSETS))
    a = ap.parse_args()
    CROPS = CROPSETS[a.set]
    out = {}
    for t in a.tests:
        res = {}
        for v in a.views.split(','):
            fr, ft = os.path.join(a.ref, 'view_%s.png' % v), os.path.join(t, 'view_%s.png' % v)
            if not (os.path.exists(fr) and os.path.exists(ft)): continue
            A, B = cv2.imread(fr), cv2.imread(ft)
            if A is None or B is None or A.shape != B.shape: continue
            As, Bs = cv2.resize(A, (1920, 1080), interpolation=cv2.INTER_AREA), cv2.resize(B, (1920, 1080), interpolation=cv2.INTER_AREA)
            for name, (x0, y0, x1, y1) in CROPS[v].items():
                ca, cb = As[y0:y1, x0:x1], Bs[y0:y1, x0:x1]
                ya, yb = luma(ca), luma(cb)
                mse = float(((ca.astype(np.float64) - cb.astype(np.float64)) ** 2).mean())
                fa, fb = A[y0 * 2:y1 * 2, x0 * 2:x1 * 2], B[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
                res[name] = {'ssim': round(ssim(ya, yb), 4), 'ssim_full': round(ssim(luma(fa), luma(fb)), 4), 'psnr_db': round(10 * np.log10(255 ** 2 / max(mse, 1e-9)), 2),
                             'warm_ref_pct': round(warm(ca), 2), 'warm_test_pct': round(warm(cb), 2), 'meanY_ref': round(float(ya.mean()), 1), 'meanY_test': round(float(yb.mean()), 1)}
                if a.sbs:
                    os.makedirs(a.sbs, exist_ok=True)
                    cv2.imwrite(os.path.join(a.sbs, '%s_%s.jpg' % (os.path.basename(t.rstrip('/')), name)), np.concatenate([ca, cb], axis=1), [cv2.IMWRITE_JPEG_QUALITY, 88])
        res['_pass'] = bool(res) and all(v['ssim'] >= a.thr for k, v in res.items() if not k.startswith('_'))
        out[t] = res
        print(t)
        for k, v in res.items():
            if not k.startswith('_'): print('  %-11s ssim %.4f (full %.4f)  psnr %5.2f  warm %.2f -> %.2f %%  meanY %.1f -> %.1f' % (k, v['ssim'], v['ssim_full'], v['psnr_db'], v['warm_ref_pct'], v['warm_test_pct'], v['meanY_ref'], v['meanY_test']))
        print('  PASS (all crops >= %.2f): %s' % (a.thr, res['_pass']))
    if a.json: json.dump({'ref': a.ref, 'thr': a.thr, 'crops': CROPS, 'tests': out}, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
