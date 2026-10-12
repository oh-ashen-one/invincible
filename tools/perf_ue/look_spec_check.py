#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P4 numbers against docs/night1/look/SPEC.md for one folder of stills (<preset>_<S#>_<res>.jpg|png), round 03 version.
Same instrument as specs/tools/lum_by_tod.py (1920 px wide, luma .2126R+.7152G+.0722B of the 8-bit sRGB values, near-black Y < 10, clipped = any channel >= 250) plus
  L2  midday overcast (83..97, near-black <= 0.05 %, clipped 0.00 %, B-R -19..+8; replaces the old L4 line for the midday preset)
  L10 far-field of S4 (P1's CITY-SPEC boxes, docs/night1/city/spec_regions.json v1, 1080p coordinates): far-shore Y minus sky Y in -32..-15, far-shore B-R within +-10 of the sky's
  L11 midday S4: horizon_far band Y minus zenith (sky) band Y >= +3
  L8 / L14 night: B-R -13..+13; bottom third p10 15..30 and p90 >= 100 (street-level views S5 / S6)
  L17 glass p10 >= 20 in the glass-only boxes of the S-views (boxes of P1's spec_regions.json C1/C2 'glass' entries)
usage: look_spec_check.py --dir <stills dir> [--res 1920x1080] [--md out.md] [--json out.json]"""
import sys, os, re, json, glob, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

# (mean lo, mean hi, near-black max %, clipped max %, B-R lo, B-R hi)
SPEC = {'golden': ('L1', 61, 100, 8.0, 1.8, -55, -20), 'night': ('L3', 37, 60, 1.0, 1.7, -13, 13), 'midday': ('L2', 83, 97, 0.05, 0.005, -19, 8)}
SPEC_S7 = ('L5', 59, 118, 8.8, 0.7, -55, -20)
FAR = {'sky': (0, 0, 1650, 80), 'far_shore': (450, 192, 1350, 236), 'river': (720, 298, 1000, 338), 'horizon_far': (420, 160, 1400, 190)}
GLASS = {'S1': {'s1_left_glass': (510, 0, 700, 430)}, 'S2': {'s2_gold_glass': (1475, 60, 1900, 900)}, 'S5': {'s5_teal_glass': (1100, 230, 1330, 480)},
         'S7': {'s7_left_glass': (0, 0, 490, 1000)}, 'S8': {'s8_glass_right': (1270, 350, 1600, 1000), 's8_pale_glass': (370, 300, 560, 700)}}

def load(path):
    im = Image.open(path).convert('RGB')
    if im.width != 1920: im = im.resize((1920, int(round(im.height * 1920 / im.width))), Image.BOX if im.width % 1920 == 0 else Image.LANCZOS)
    return np.asarray(im, dtype=np.float32)

def luma(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

def box(a, b):
    x0, y0, x1, y1 = b; return a[y0:y1, x0:x1]

def stats(path):
    a = load(path); r, g, b = a[..., 0], a[..., 1], a[..., 2]; Y = luma(a); H = Y.shape[0]
    d = {'file': os.path.basename(path), 'mean': float(Y.mean()), 'near_black_pct': float((Y < 10).mean() * 100), 'lt25_pct': float((Y < 25).mean() * 100),
         'clipped_pct': float((a.max(axis=2) >= 250).mean() * 100), 'p99': float(np.percentile(Y, 99)), 'b_minus_r': float((b - r).mean()),
         'bottom_third_p90': float(np.percentile(Y[2 * H // 3:], 90)), 'bottom_third_p10': float(np.percentile(Y[2 * H // 3:], 10))}
    lab, n = ndi.label(ndi.gaussian_filter(Y, 12.0)[H // 2:] >= 100)
    areas = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) if n else []
    d['lit_blobs_bottom_half'] = int(sum(1 for x in areas if x >= 400))
    if d['file'].split('_')[1] == 'S4':
        reg = {}
        for k, bx in FAR.items():
            c = box(a, bx); reg[k] = {'Y': float(luma(c).mean()), 'BR': float((c[..., 2] - c[..., 0]).mean())}
        d['far'] = reg
    gl = GLASS.get(d['file'].split('_')[1])
    if gl: d['glass'] = {k: {'p10': float(np.percentile(luma(box(a, bx)), 10)), 'mean': float(luma(box(a, bx)).mean()), 'BR': float((box(a, bx)[..., 2] - box(a, bx)[..., 0]).mean())} for k, bx in gl.items()}
    return d

def verdict(name, d):
    m = re.match(r'(midday|golden|night)_(S\d)', name)
    if not m: return None
    pre, view = m.group(1), m.group(2)
    ln, lo, hi, nb, cl, bl, bh = SPEC_S7 if (pre == 'golden' and view == 'S7') else SPEC[pre]
    return ln, {'mean': lo <= d['mean'] <= hi, 'near_black': d['near_black_pct'] <= nb, 'clipped': d['clipped_pct'] <= cl, 'b_minus_r': bl <= d['b_minus_r'] <= bh}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='*'); ap.add_argument('--dir'); ap.add_argument('--res', default='1920x1080'); ap.add_argument('--json'); ap.add_argument('--md')
    a = ap.parse_args()
    files = list(a.files) or sorted(glob.glob(os.path.join(a.dir, '*_%s*.*' % a.res)))
    files = [f for f in files if f.lower().endswith(('.jpg', '.png')) and re.match(r'(midday|golden|night)_S\d', os.path.basename(f))]
    order = {'midday': 0, 'golden': 1, 'night': 2}
    files.sort(key=lambda f: (order[os.path.basename(f).split('_')[0]], os.path.basename(f).split('_')[1]))
    rows = []
    for f in files:
        d = stats(f); v = verdict(os.path.basename(f), d); d['spec_line'] = v[0] if v else None; d['within'] = v[1] if v else None; rows.append(d)
    L = ['| still | spec | mean Y | Y<10 % | clipped % | B-R | lit blobs (bottom half) | bottom-third p90 / p10 | within (mean / near-black / clipped / B-R) |', '|' + '---|' * 9]
    for d in rows:
        w = d['within']
        L.append('| %s | %s | %.1f | %.2f | %.2f | %+.1f | %d | %.0f / %.0f | %s |' % (d['file'], d['spec_line'] or '-', d['mean'], d['near_black_pct'], d['clipped_pct'], d['b_minus_r'], d['lit_blobs_bottom_half'], d['bottom_third_p90'], d['bottom_third_p10'],
                    ('%s / %s / %s / %s' % tuple('yes' if w[k] else 'NO' for k in ('mean', 'near_black', 'clipped', 'b_minus_r'))) if w else '-'))
    L += ['', '### Far field (S4, boxes of docs/night1/city/spec_regions.json v1, 1080p)', '',
          '| still | sky Y (B-R) | horizon_far Y (B-R) | far_shore Y (B-R) | river Y | L10 far-shore Y - sky Y (-32..-15) | L10 far-shore B-R - sky B-R (+-10) | L11 horizon_far - sky (>= +3, midday) | far-shore - river Y (P1 C14: 5..35) |', '|' + '---|' * 9]
    for d in rows:
        if 'far' not in d: continue
        f = d['far']; ok = lambda c: 'yes' if c else 'NO'
        dy = f['far_shore']['Y'] - f['sky']['Y']; dbr = f['far_shore']['BR'] - f['sky']['BR']; hz = f['horizon_far']['Y'] - f['sky']['Y']; fr = f['far_shore']['Y'] - f['river']['Y']
        L.append('| %s | %.1f (%+.1f) | %.1f (%+.1f) | %.1f (%+.1f) | %.1f | %+.1f %s | %+.1f %s | %+.1f %s | %+.1f %s |' % (d['file'], f['sky']['Y'], f['sky']['BR'], f['horizon_far']['Y'], f['horizon_far']['BR'], f['far_shore']['Y'], f['far_shore']['BR'], f['river']['Y'],
                    dy, ok(-32 <= dy <= -15), dbr, ok(abs(dbr) <= 10), hz, ok(hz >= 3) if d['file'].startswith('midday') else '(n/a)', fr, ok(5 <= fr <= 35)))
    L += ['', '### Glass p10 (L17: >= 20; glass-only boxes)', '', '| still | box | p10 Y | mean Y | B-R | L17 |', '|---|---|---|---|---|---|']
    for d in rows:
        if d['file'].startswith('night_'): continue   # L17 is a daylight line
        for k, g in (d.get('glass') or {}).items(): L.append('| %s | %s | %.1f | %.1f | %+.1f | %s |' % (d['file'], k, g['p10'], g['mean'], g['BR'], 'yes' if g['p10'] >= 20 else 'NO'))
    L += ['', '### Night street views (L13 / L14)', '', '| still | lit blobs (L13 >= 5) | bottom-third p10 (L14 15..30) | bottom-third p90 (L14 >= 100) |', '|---|---|---|---|']
    for d in rows:
        if d['file'].startswith('night_') and d['file'].split('_')[1] in ('S1', 'S5', 'S6'):
            L.append('| %s | %d %s | %.1f %s | %.1f %s |' % (d['file'], d['lit_blobs_bottom_half'], 'yes' if d['lit_blobs_bottom_half'] >= 5 else 'NO', d['bottom_third_p10'], 'yes' if 15 <= d['bottom_third_p10'] <= 30 else 'NO',
                        d['bottom_third_p90'], 'yes' if d['bottom_third_p90'] >= 100 else 'NO'))
    out = '\n'.join(L) + '\n'
    print(out)
    if a.json: json.dump(rows, open(a.json, 'w'), indent=1)
    if a.md: open(a.md, 'w').write(out)

if __name__ == '__main__':
    main()
