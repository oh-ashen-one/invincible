#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: quality check of a perf change by capture comparison. For every still present in both dirs (same camera, same
deterministic route frame): PSNR, SSIM (luma, 8x8 Gaussian-free box SSIM on a 1920x1080 downsample), mean |dY|, the fraction
of pixels with |dY| > 12 (8-bit luma), mean luma of each, and a 1920x540 side-by-side JPG (ref left, test right) + a 4x
amplified difference image. usage: compare_stills.py <ref_dir> <test_dir> <out_dir> [--label name]"""
import sys, os, json, argparse
import numpy as np, cv2


def luma(img): return (0.2126 * img[..., 2] + 0.7152 * img[..., 1] + 0.0722 * img[..., 0]).astype(np.float64)


def ssim(a, b, k=8):
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    f = lambda x: cv2.blur(x, (k, k))
    ma, mb = f(a), f(b)
    va, vb, cov = f(a * a) - ma * ma, f(b * b) - mb * mb, f(a * b) - ma * mb
    s = ((2 * ma * mb + C1) * (2 * cov + C2)) / ((ma * ma + mb * mb + C1) * (va + vb + C2))
    return float(s.mean())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ref'); ap.add_argument('test'); ap.add_argument('out'); ap.add_argument('--label', default='')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    res = {}
    for f in sorted(os.listdir(a.ref)):
        if not f.endswith('.png') or not os.path.exists(os.path.join(a.test, f)): continue
        A, B = cv2.imread(os.path.join(a.ref, f)), cv2.imread(os.path.join(a.test, f))
        if A is None or B is None or A.shape != B.shape: continue
        As, Bs = cv2.resize(A, (1920, 1080), interpolation=cv2.INTER_AREA), cv2.resize(B, (1920, 1080), interpolation=cv2.INTER_AREA)
        ya, yb = luma(As), luma(Bs)
        mse = float(((As.astype(np.float64) - Bs.astype(np.float64)) ** 2).mean())
        d = np.abs(ya - yb)
        lt10 = lambda y: round(float((y < 10).mean() * 100), 2)
        clip = lambda im: round(float((im.max(axis=2) >= 250).mean() * 100), 2)  # look-spec L1-L5 columns: near-black Y < 10, any channel >= 250
        res[f[:-4]] = {'lt10_ref': lt10(ya), 'lt10_test': lt10(yb), 'clip_ref': clip(As), 'clip_test': clip(Bs), 'psnr_db': round(10 * np.log10(255 ** 2 / max(mse, 1e-9)), 2), 'ssim_luma': round(ssim(ya, yb), 4),
                       'mean_abs_dY': round(float(d.mean()), 2), 'frac_dY_gt12': round(float((d > 12).mean()), 4),
                       'meanY_ref': round(float(ya.mean()), 1), 'meanY_test': round(float(yb.mean()), 1)}
        sbs = np.concatenate([cv2.resize(As, (960, 540)), cv2.resize(Bs, (960, 540))], axis=1)
        cv2.imwrite(os.path.join(a.out, '%s_sbs.jpg' % f[:-4]), sbs, [cv2.IMWRITE_JPEG_QUALITY, 85])
        dd = np.clip(np.abs(As.astype(np.int16) - Bs.astype(np.int16)) * 4, 0, 255).astype(np.uint8)
        cv2.imwrite(os.path.join(a.out, '%s_diff4x.jpg' % f[:-4]), cv2.resize(dd, (960, 540)), [cv2.IMWRITE_JPEG_QUALITY, 80])
    json.dump({'ref': a.ref, 'test': a.test, 'label': a.label, 'stills': res}, open(os.path.join(a.out, 'compare.json'), 'w'), indent=1)
    for k, v in res.items(): print('%-12s %s' % (k, v))


if __name__ == '__main__':
    main()
