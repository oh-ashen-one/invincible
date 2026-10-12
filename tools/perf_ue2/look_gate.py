#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F (round 04): the look gate of the round-03 critic, test stills vs the PRE-OPTIMISATION stills of the same map (as found: no preset,
content untouched; round 03 `_scratch/perf/r03/before`, 3840x2160 PNG). Every measure is taken on the 1920x1080 area-downsample.
  crops     crop SSIM of the ROUND-02 crop set (crop_ssim.py --set r02: S1_glass (485,0,710,490), S2_windows, S2_gold), unchanged coordinates. Line: >= 0.97.
  canopy    mean luma of the CANOPY pixels, mask taken from the REFERENCE still only (green-dominant: G > R + 5 and G > B + 5, 8-bit), the same pixel
            positions read in the test still. Line: test / ref within +-10 % (only stills whose mask covers >= 1 % of the frame are gated).
  sat       mean HSV saturation (OpenCV 0-255) of the whole frame. Line: route stills (route_t*) within +-5 % of the reference.
  sky       top 15 % of the frame (sky only in the route stills): luma standard deviation and mean Sobel gradient magnitude ("cloud detail");
            reported as test / ref, not gated (the cumulus that the 4 km cloud distance erased at t42 shows here).
usage: look_gate.py <ref_dir> <test_dir> [<test_dir> ...] [--json out.json] [--md out.md]"""
import argparse, json, os, sys
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crop_ssim import CROPSETS, luma, ssim  # noqa: E402

CROPS = CROPSETS['r02']
STILLS = ['view_S1', 'view_S2', 'view_S7', 'route_t20', 'route_t28', 'route_t38', 'route_t42']


def load(p):
    im = cv2.imread(p)
    return None if im is None else cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA)


def canopy_mask(img):
    b, g, r = [img[..., i].astype(np.int16) for i in range(3)]
    return (g > r + 5) & (g > b + 5)


def sat(img): return float(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 1].mean())


def sky(img):
    y = luma(img)[:int(1080 * 0.15)]
    gx, gy = cv2.Sobel(y, cv2.CV_64F, 1, 0, ksize=3), cv2.Sobel(y, cv2.CV_64F, 0, 1, ksize=3)
    return float(y.std()), float(np.sqrt(gx * gx + gy * gy).mean())


def gate(ref, test):
    out = {'stills': {}, 'crops': {}}
    for s in STILLS:
        A, B = load(os.path.join(ref, s + '.png')), load(os.path.join(test, s + '.png'))
        if A is None or B is None: continue
        m = canopy_mask(A); ya, yb = luma(A), luma(B)
        frac = float(m.mean())
        r = {'meanY_ref': round(float(ya.mean()), 1), 'meanY_test': round(float(yb.mean()), 1), 'canopy_frac_pct': round(frac * 100, 2)}
        if frac >= 0.01:
            ca, cb = float(ya[m].mean()), float(yb[m].mean())
            r.update(canopy_ref=round(ca, 1), canopy_test=round(cb, 1), canopy_ratio=round(cb / ca, 3), canopy_pass=bool(abs(cb / ca - 1) <= 0.10))
        sa, sb = sat(A), sat(B)
        r.update(sat_ref=round(sa, 1), sat_test=round(sb, 1), sat_ratio=round(sb / sa, 3))
        if s.startswith('route_'): r['sat_pass'] = bool(abs(sb / sa - 1) <= 0.05)
        (sda, ga), (sdb, gb) = sky(A), sky(B)
        r.update(sky_std_ref=round(sda, 2), sky_std_test=round(sdb, 2), sky_grad_ref=round(ga, 2), sky_grad_test=round(gb, 2), sky_grad_ratio=round(gb / ga, 3) if ga else None)
        out['stills'][s] = r
        v = s.split('_')[1] if s.startswith('view_') else None
        if v in CROPS:
            for name, (x0, y0, x1, y1) in CROPS[v].items():
                out['crops'][name] = round(ssim(luma(A[y0:y1, x0:x1]), luma(B[y0:y1, x0:x1])), 4)
    st = out['stills']
    out['pass'] = {'crops_r02_ge_0.97': bool(out['crops']) and all(x >= 0.97 for x in out['crops'].values()),
                   'canopy_within_10pct': all(r.get('canopy_pass', True) for r in st.values()),
                   'route_sat_within_5pct': all(r.get('sat_pass', True) for r in st.values())}
    return out


def md(res):
    L = []
    for t, o in res.items():
        L.append('### %s' % t)
        L.append('crop SSIM (round-02 crops): ' + ', '.join('%s %.4f' % kv for kv in o['crops'].items()) + '  | pass: ' + ', '.join('%s %s' % kv for kv in o['pass'].items()))
        L.append('')
        L.append('| still | mean Y ref -> test | canopy px % | canopy Y ref -> test (ratio) | saturation ref -> test (ratio) | sky std ref -> test | sky gradient ref -> test (ratio) |')
        L.append('|---|---|---|---|---|---|---|')
        for s, r in o['stills'].items():
            can = '%.1f -> %.1f (%.3f%s)' % (r['canopy_ref'], r['canopy_test'], r['canopy_ratio'], '' if r['canopy_pass'] else ' FAIL') if 'canopy_ref' in r else 'n/a (< 1 %)'
            sa = '%.1f -> %.1f (%.3f%s)' % (r['sat_ref'], r['sat_test'], r['sat_ratio'], ' FAIL' if r.get('sat_pass') is False else '')
            L.append('| %s | %.1f -> %.1f | %.2f | %s | %s | %.2f -> %.2f | %.2f -> %.2f (%s) |' % (s, r['meanY_ref'], r['meanY_test'], r['canopy_frac_pct'], can, sa,
                     r['sky_std_ref'], r['sky_std_test'], r['sky_grad_ref'], r['sky_grad_test'], r['sky_grad_ratio']))
        L.append('')
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ref'); ap.add_argument('tests', nargs='+'); ap.add_argument('--json'); ap.add_argument('--md')
    a = ap.parse_args()
    res = {t: gate(a.ref, t) for t in a.tests}
    txt = md(res); print(txt)
    if a.json: json.dump({'ref': a.ref, 'crops': CROPS, 'tests': res}, open(a.json, 'w'), indent=1)
    if a.md: open(a.md, 'w').write(txt + '\n')


if __name__ == '__main__':
    main()
