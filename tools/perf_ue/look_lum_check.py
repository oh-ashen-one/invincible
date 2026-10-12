#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P4 numbers against docs/night1/look/SPEC.md (LOOK-SPEC L1..L8, L13..L14). Same definitions as the director's specs/tools/lum_by_tod.py:
stills are resized to 1920 px wide (INTER_AREA), luma Y = .2126 R + .7152 G + .0722 B of the 8-bit sRGB values, near-black = Y < 10,
clipped = any channel >= 250. Night street views also get the L13 / L14 blob and bottom-third numbers.
usage: look_lum_check.py <still.jpg|png> ...   or   look_lum_check.py --dir <stills dir> [--res 1920x1080] [--json out.json] [--md out.md]
File names are <preset>_<S#>_<res>.<ext> (capture_looks.py); other names are treated as preset 'night' when they contain 'night'."""
import sys, os, re, json, glob, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

# spec lines: (mean lo, mean hi, near-black max %, clipped max %, B-R lo, B-R hi)
SPEC = {'golden': ('L1', 61, 100, 8.0, 1.8, -55, -20), 'night': ('L3', 37, 60, 1.0, 1.7, -13, 13), 'midday': ('L4', 55, 89, 12.7, 0.3, -19, 8)}
SPEC_S7 = ('L5', 59, 118, 8.8, 0.7, -55, -20)   # sun-facing golden view (S7 on the golden preset)

def load(path):
    im = Image.open(path).convert('RGB')
    if im.width != 1920: im = im.resize((1920, int(round(im.height * 1920 / im.width))), Image.BOX if im.width % 1920 == 0 else Image.LANCZOS)
    return np.asarray(im, dtype=np.float32)

def stats(path):
    a = load(path); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b; H = Y.shape[0]
    d = {'file': os.path.basename(path), 'mean': float(Y.mean()), 'near_black_pct': float((Y < 10).mean() * 100), 'lt25_pct': float((Y < 25).mean() * 100),
         'clipped_pct': float((a.max(axis=2) >= 250).mean() * 100), 'p99': float(np.percentile(Y, 99)), 'p50': float(np.median(Y)), 'b_minus_r': float((b - r).mean()),
         'bottom_third_p90': float(np.percentile(Y[2 * H // 3:], 90)), 'bottom_third_p10': float(np.percentile(Y[2 * H // 3:], 10))}
    sm = ndi.gaussian_filter(Y, 12.0)             # L13: blobs in the bottom half (sigma 12 px at 1080p, Y >= 100, area >= 400 px)
    lab, n = ndi.label(sm[H // 2:] >= 100)
    areas = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) if n else []
    d['lit_blobs_bottom_half'] = int(sum(1 for x in areas if x >= 400))
    return d

def verdict(name, d):
    m = re.match(r'(midday|golden|night)_(S\d)', name)
    if not m: return None
    pre, view = m.group(1), m.group(2)
    line = SPEC_S7 if (pre == 'golden' and view == 'S7') else SPEC[pre]
    ln, lo, hi, nb, cl, bl, bh = line
    ok = {'mean': lo <= d['mean'] <= hi, 'near_black': d['near_black_pct'] <= nb, 'clipped': d['clipped_pct'] <= cl, 'b_minus_r': bl <= d['b_minus_r'] <= bh}
    return ln, ok

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='*'); ap.add_argument('--dir'); ap.add_argument('--res', default='1920x1080'); ap.add_argument('--json'); ap.add_argument('--md')
    a = ap.parse_args()
    files = list(a.files) or sorted(glob.glob(os.path.join(a.dir, '*_%s.*' % a.res)))
    rows = []
    for f in files:
        d = stats(f); v = verdict(os.path.basename(f), d)
        d['spec_line'] = v[0] if v else None; d['within'] = v[1] if v else None; rows.append(d)
    L = ['| still | spec | mean Y | Y<10 % | Y<25 % | clipped % | p99 | B-R | lit blobs (bottom half) | bottom-third p90 / p10 | within spec (mean / near-black / clipped / B-R) |', '|' + '---|' * 11]
    for d in rows:
        w = d['within']
        L.append('| %s | %s | %.1f | %.2f | %.1f | %.2f | %.0f | %+.1f | %d | %.0f / %.0f | %s |' % (d['file'], d['spec_line'] or '-', d['mean'], d['near_black_pct'], d['lt25_pct'], d['clipped_pct'], d['p99'], d['b_minus_r'], d['lit_blobs_bottom_half'],
                    d['bottom_third_p90'], d['bottom_third_p10'], ('%s / %s / %s / %s' % tuple('yes' if w[k] else 'NO' for k in ('mean', 'near_black', 'clipped', 'b_minus_r'))) if w else '-'))
    out = '\n'.join(L) + '\n'
    print(out)
    if a.json: json.dump(rows, open(a.json, 'w'), indent=1)
    if a.md: open(a.md, 'w').write(out)

if __name__ == '__main__':
    main()
