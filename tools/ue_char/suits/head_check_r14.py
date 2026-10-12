#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14 pass test of the finished mask sculpt, measured on the 4K head stills of the REAL game (lossless PNG originals).  It re-runs every round-13 gate (head_check_r13.py:
H1 nose-bridge luma, H2 nose bump, H3 lens >= 1.6x r12, H4 closed raised rim, H5 face-seam cord, H6 lenses inside the outline) and adds the three tests of the round-13 critic:

  G1 bridge recess   headside profile: the silhouette's front edge between the brow's front-most point and the nose tip dips >= 1.5 % of the head height (crown to chin) behind
                     the straight chord brow -> nose tip (rows of the whole silhouette: lens and rim included, they are part of the edge the critic sees)
  G2 brow overhang   headside profile: the brow's front-most point lies >= 1 % of the head height in front of the TOP OF THE LENS (the front-most pixel of the lens glass in the top
                     quarter of its rows) and, stricter, in front of the lens glass + a 3.1 mm rim allowance
  G3 cheek luma      front stills (head = 12 deg, headfront = 0 deg, head34 = 25 deg): horizontal luma lines through the cheek bones (the band between the lens bottom + 15 px and
                     + 200 px, every 15 px; 15 px smoothing; the head interior minus a 30 px margin) show >= 3 extrema of prominence >= 20 luma on >= 70 % of the lines and a
                     swing (max - min) >= 20 on every one of them
  python3 head_check_r14.py all <stills_dir> <r12_stills_dir> <out.json> [overlay_dir]
  python3 head_check_r14.py profile <headside_4k.png> <suit> [--dump out.jpg]
  python3 head_check_r14.py cheek <front_4k.png> <suit> [--dump out.jpg]
"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import find_peaks
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import head_check_r13 as H13  # noqa: E402
Image.MAX_IMAGE_PIXELS = None
SUITS = H13.SUITS


def profile(path, suit, dump=None, cam_dist=1.25, aim_y=1.665, fov=26.0):
    """G1 + G2 on the headside still (see the module doc)."""
    im = H13.load(path); sil = H13.silhouette(im)
    h, w, _ = im.shape
    f = 1920.0 / np.tan(np.radians(fov / 2)) / cam_dist
    row_of = lambda y: int(round(1080 - (y - aim_y) * f))
    crown = int(np.nonzero(sil.any(1))[0].min())
    chin = row_of(1.5475)                                          # the chin's underside (mesh; the head is rigid, the idle bob moves it by < 3 mm)
    HH = float(chin - crown)
    y_nose = row_of(1.645); cx = int(np.nonzero(sil[row_of(1.74)])[0].mean())
    rr = np.nonzero(sil[y_nose])[0]
    sgn = 1 if (rr.max() - cx) > (cx - rr.min()) else -1
    rows = np.arange(row_of(1.745), row_of(1.60))
    fx = np.array([(np.nonzero(sil[r])[0].max() if sgn > 0 else np.nonzero(sil[r])[0].min()) for r in rows], np.float64)
    fx = ndi.uniform_filter1d(fx, 3, mode='nearest')
    at = lambda r: int(r - rows[0])
    sl = lambda ya, yb: slice(at(row_of(ya)), at(row_of(yb)) + 1)             # rows from y = ya (upper) down to yb
    i_b0 = at(row_of(1.735)); seg_b = fx[sl(1.735, 1.693)] * sgn; i_b = at(row_of(1.735)) + int(np.argmax(seg_b))       # brow: the front-most row of the band above the lens
    i_n0 = at(row_of(1.668)); seg_n = fx[sl(1.668, 1.615)] * sgn; i_n = at(row_of(1.668)) + int(np.argmax(seg_n))       # nose tip
    xb, xn = fx[i_b], fx[i_n]
    t = (np.arange(i_b, i_n + 1) - i_b) / max(i_n - i_b, 1)
    chord = xb + t * (xn - xb)
    dip = (chord - fx[i_b:i_n + 1]) * sgn
    k = int(np.argmax(dip))
    G1 = float(dip[k])
    # lens glass in the profile: hue / saturation / value of the lens colour inside the head, the biggest component near the front edge
    acc = H13.lens_colour(suit)
    ha, sa, va = H13.rgb2hsv(acc)
    x = im / 255.0; mx = x.max(2); mn = x.min(2); v = mx; s_ = (mx - mn) / (mx + 1e-6)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]; dl = mx - mn + 1e-9
    hh = np.where(mx == r, ((g - b) / dl) % 6, np.where(mx == g, (b - r) / dl + 2, (r - g) / dl + 4)) / 6.0
    m = (H13.hue_dist(hh, ha) < 0.045) & (s_ > max(0.18, 0.45 * sa)) & (v > 0.42) & ndi.binary_erosion(sil, iterations=3)
    m = ndi.binary_closing(ndi.binary_opening(m, iterations=2), iterations=6)
    lab, n = ndi.label(m)
    lens = None
    if n:
        areas = ndi.sum(m, lab, range(1, n + 1)); lens = lab == (1 + int(np.argmax(areas)))
        lens = ndi.binary_fill_holes(lens)
    out = dict(suit=suit, file=os.path.basename(path), face_dir=int(sgn), head_h_px=int(HH), crown_row=crown, chin_row=chin,
               brow=dict(row=int(rows[i_b]), x=int(xb)), nose_tip=dict(row=int(rows[i_n]), x=int(xn)), nasion=dict(row=int(rows[i_b + k]), x=int(fx[i_b + k])),
               G1_recess_px=round(G1, 1), G1_recess_pct_head_h=round(100 * G1 / HH, 2))
    if lens is not None and lens.sum() > 500:
        ys, xs = np.nonzero(lens)
        top = ys.min(); q = top + 0.25 * (ys.max() - top)
        sel = ys <= q
        xl = (xs[sel].max() if sgn > 0 else xs[sel].min())
        rim_px = 0.0031 * f
        g2 = (xb - xl) * sgn; g2r = g2 - rim_px
        out.update(lens=dict(rows=[int(ys.min()), int(ys.max())], x_front_top_quarter=int(xl)), G2_brow_over_lens_top_px=round(float(g2), 1), G2_pct_head_h=round(100 * g2 / HH, 2),
                   G2_with_rim_px=round(float(g2r), 1), G2_with_rim_pct_head_h=round(100 * g2r / HH, 2))
    else:
        out.update(lens=None, G2_pct_head_h=None, G2_with_rim_pct_head_h=None)
    # r13's H2 (nose bump over the brow -> chin chord) on the same still
    try: out['H2'] = H13.side(path, suit)['nose_bump_pct_head_h']
    except Exception as ex: out['H2'] = None
    if dump:
        from PIL import ImageDraw
        pim = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(pim)
        pts = [(float(fx[i]), float(rows[i])) for i in range(len(rows))]
        d.line(pts, fill=(255, 0, 255), width=4)
        d.line([(float(xb), float(rows[i_b])), (float(xn), float(rows[i_n]))], fill=(0, 255, 255), width=4)
        d.ellipse([xb - 10, rows[i_b] - 10, xb + 10, rows[i_b] + 10], outline=(255, 0, 0), width=4); d.ellipse([xn - 10, rows[i_n] - 10, xn + 10, rows[i_n] + 10], outline=(0, 255, 0), width=4)
        d.ellipse([fx[i_b + k] - 10, rows[i_b + k] - 10, fx[i_b + k] + 10, rows[i_b + k] + 10], outline=(0, 0, 255), width=4)
        if lens is not None and lens.sum() > 500:
            edge = lens ^ ndi.binary_erosion(lens, iterations=2)
            a = np.asarray(pim).copy(); a[edge] = (255, 255, 0); pim = Image.fromarray(a)
        pim.resize((1920, 1080)).save(dump, quality=80)
    return out


def cheek_lines(path, suit, dump=None):
    """G3: horizontal luma lines through the cheek bones of a front still."""
    im = H13.load(path); sil = H13.silhouette(im)
    masks = H13.lens_masks(im, suit, sil=sil)
    out = dict(suit=suit, file=os.path.basename(path), lenses=len(masks))
    if len(masks) < 2: out['ok'] = False; return out
    L = H13.luma_of(im)
    bb = [H13.bbox(mk) for mk in masks]
    y_bot = int(max(bb[0][3], bb[1][3]))
    rows = list(range(y_bot + 15, y_bot + 201, 15))
    res = []
    for y in rows:
        xs = np.nonzero(sil[y])[0]
        if len(xs) < 200: continue
        a, b_ = int(xs.min()) + 30, int(xs.max()) - 30
        row = L[y - 3:y + 4].mean(0)
        seg = ndi.uniform_filter1d(row, 15, mode='nearest')[a:b_]
        p, _ = find_peaks(seg, prominence=20.0); q, _ = find_peaks(-seg, prominence=20.0)
        res.append(dict(row=int(y), extrema=int(len(p) + len(q)), swing=round(float(seg.max() - seg.min()), 1), width_px=int(b_ - a)))
    n_ok = sum(1 for r_ in res if r_['extrema'] >= 3)
    out.update(lens_bottom_row=y_bot, lines=res, lines_ge3=n_ok, lines_total=len(res), frac_ge3=round(n_ok / max(len(res), 1), 2),
               min_swing=min((r_['swing'] for r_ in res), default=0), median_extrema=float(np.median([r_['extrema'] for r_ in res])) if res else 0)
    out['G3_pass'] = bool(res and out['frac_ge3'] >= 0.7 and out['min_swing'] >= 20)
    if dump:
        ov = im.copy()
        for r_ in res:
            ov[r_['row'] - 1:r_['row'] + 2, :] = (255, 0, 255) if r_['extrema'] >= 3 else (255, 255, 0)
        Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)).resize((1920, 1080)).save(dump, quality=78)
    return out


def verdict(fr, f34, fz, sd, ch):
    """fr = 12 deg head still, f34 = 25 deg, fz = 0 deg (headfront), sd = profile, ch = {view: cheek_lines}."""
    v = H13.verdict(fr, f34, {'nose_bump_pct_head_h': (sd.get('H2') if sd.get('H2') is not None else 0.0)} if sd else None)
    v['G1_recess_ge_1.5pct'] = bool(sd and sd.get('G1_recess_pct_head_h') is not None and sd['G1_recess_pct_head_h'] >= 1.5)
    v['G2_brow_over_lens_top_ge_1pct'] = bool(sd and sd.get('G2_pct_head_h') is not None and sd['G2_pct_head_h'] >= 1.0)
    v['G2b_brow_over_lens_plus_rim_ge_1pct'] = bool(sd and sd.get('G2_with_rim_pct_head_h') is not None and sd['G2_with_rim_pct_head_h'] >= 1.0)
    v['G3_cheek_lines_head_12deg'] = bool(ch.get('head', {}).get('G3_pass', False))
    v['G3_cheek_lines_headfront_0deg'] = bool(ch.get('headfront', {}).get('G3_pass', False))
    v['G3_cheek_lines_head34_25deg'] = bool(ch.get('head34', {}).get('G3_pass', False))
    return v


def run_all(sd_, r12d, outp, ovd=None):
    if ovd: os.makedirs(ovd, exist_ok=True)
    res = {}
    only = os.environ.get('HEAD_SUITS', '').split(',') if os.environ.get('HEAD_SUITS') else None
    for s in SUITS:
        sid = s['id']
        if only and sid not in only: continue
        ov = lambda t: os.path.join(ovd, '%s_%s.jpg' % (t, sid)) if ovd else None
        P = lambda view: os.path.join(sd_, 'skin_%s_%s_4k.png' % (sid, view))
        r12p = os.path.join(r12d, 'skin_%s_head_4k.png' % sid)
        fr = H13.front(P('head'), sid, ov('head'), r12p if os.path.exists(r12p) else None)
        f34 = H13.front(P('head34'), sid, ov('head34'), r12p if os.path.exists(r12p) else None)
        fz = H13.front(P('headfront'), sid, ov('headfront')) if os.path.exists(P('headfront')) else {}
        sd = profile(P('headside'), sid, ov('profile')) if os.path.exists(P('headside')) else None
        ch = {}
        for view in ('head', 'headfront', 'head34'):
            if os.path.exists(P(view)): ch[view] = cheek_lines(P(view), sid, ov('cheek_' + view))
        res[sid] = dict(head=fr, head34=f34, headfront=fz, side=sd, cheek=ch, verdict=verdict(fr, f34, fz, sd, ch))
        print(sid, json.dumps(res[sid]['verdict']))
        json.dump(res, open(outp, 'w'), indent=1)
    return res


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'all': run_all(a[2], a[3], a[4], a[5] if len(a) > 5 else None)
    elif a[1] == 'profile': print(json.dumps(profile(a[2], a[3], a[a.index('--dump') + 1] if '--dump' in a else None)))
    elif a[1] == 'cheek': print(json.dumps(cheek_lines(a[2], a[3], a[a.index('--dump') + 1] if '--dump' in a else None)))
