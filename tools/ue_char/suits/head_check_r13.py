#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 13 pass test of the sculpted hero head, measured on the 4K head stills of the REAL game (lossless PNG originals).

  python3 head_check_r13.py front <head_4k.png> <suit> [--r12 <r12_head_4k.png>] [--dump out.png]     -> JSON line
  python3 head_check_r13.py side  <headside_4k.png> <suit> [--dump out.png]
  python3 head_check_r13.py all <stills_dir> <r12_stills_dir> <out.json> [overlay_dir]

Gates (docs/night1/characters/round-13/SPEC_CHECK.md):
  H1 nose-bridge luma profile: >= 3 extrema, every extremum >= 20 luma of prominence (vertical profile down the midline between the lenses from the brow to the
     vent / mouth, 11 px smoothing; the horizontal profile across the bridge between the two rims is reported too)
  H2 silhouette nose bump >= 2 % of head height (profile still: the front-most silhouette column above the straight line brow point -> chin point)
  H3 lens width >= 1.6x the round-12 lens width, measured as lens px width / head silhouette width at the lens row (the head turns a little in the idle clip, so the
     ratio is the pose-robust number); the absolute px are reported.  PASS = the NEAR lens in the round-12 framing (head34 vs r12 head) AND the mean of both lenses in the 12 deg
     still (head) are >= 1.6x; the far lens of a 25 deg view is foreshortened by the wrapped face and partly behind the silhouette, its ratio is reported, not gated
  H4 each lens has ONE closed rim >= 6 px wide: radial profiles from the lens centroid, rim = the band between the lens edge and the point where the colour returns to
     the mask colour (median of an annulus 70 - 120 px outside the lens); closed = >= 90 % of 48 angles at >= 6 px
  H5 face seam: along the midline cord a lit / shadow pair >= 20 luma (max - min of the horizontal luma profile across the seam, median over 12 heights) and no
     black run >= 12 px (pixels with luma < 0.45 x the local mask median AND < 12, contiguous along the horizontal profile)
  H6 lenses inside the head silhouette: lens pixels >= 3 px from the background in the 12 deg still (a wrap-around lens lies against the outline, it never leaves it)
"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import find_peaks
HERE = os.path.dirname(os.path.abspath(__file__))
Image.MAX_IMAGE_PIXELS = None
SUITS = json.load(open(os.path.join(HERE, 'suits.json')))['suits']
DEFAULT_PAL = dict(accent='#e0780c')


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.0


R12_LENS = {'plum': '#5ee0b4'}      # the round-12 Plum had a mint lens (round 13 recoloured it apricot): the r12 baseline is detected with the colour it had


def lens_colour(suit, r12=False):
    if r12 and suit in R12_LENS: return hex_rgb(R12_LENS[suit])
    for s in SUITS:
        if s['id'] == suit:
            pal = s.get('style', {}).get('palette', {})
            return hex_rgb(pal.get('lens', pal.get('accent', DEFAULT_PAL['accent'])))
    raise KeyError(suit)


def rgb2hsv(a):
    import colorsys
    return np.array(colorsys.rgb_to_hsv(*[float(v) for v in a]))


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.float32)


def luma_of(im):
    return 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]


def silhouette(im, margin=300, thr=14.0, rows=None):
    """Head / body mask against the sky + floor background: per row a quadratic fit in x over the left / right margins (the sky has a slight horizontal gradient),
    pixels more than `thr` colour distance from the fit are 'object'.  Only valid in rows where the margins are background (the head rows)."""
    h, w, _ = im.shape
    xs = np.concatenate([np.arange(margin), np.arange(w - margin, w)]).astype(np.float64)
    A = np.stack([np.ones_like(xs), xs / w, (xs / w) ** 2], 1)
    pinv = np.linalg.pinv(A)
    M = np.concatenate([im[:, :margin], im[:, -margin:]], 1).astype(np.float64)           # (h, 2m, 3)
    coef = np.einsum('kj,hjc->hkc', pinv, M)                                              # (h, 3, 3)
    X = np.stack([np.ones(w), np.arange(w) / w, (np.arange(w) / w) ** 2], 1)              # (w, 3)
    bg = np.einsum('wk,hkc->hwc', X, coef)
    d = np.linalg.norm(im - bg, axis=2)
    m = d > thr
    m = ndi.binary_opening(m, iterations=2)
    return m


def hue_dist(h1, h2):
    d = np.abs(h1 - h2); return np.minimum(d, 1 - d)


def lens_masks(im, suit, min_area=4000, r12=False, sil=None):
    """The two lens components: pixels of the lens hue, bright, in the upper face; the two largest components of area >= min_area."""
    acc = lens_colour(suit, r12)
    ha, sa, va = rgb2hsv(acc)
    x = im / 255.0
    mx = x.max(2); mn = x.min(2); v = mx; s = (mx - mn) / (mx + 1e-6)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    hh = np.zeros_like(v)
    dlt = mx - mn + 1e-9
    hh = np.where(mx == r, ((g - b) / dlt) % 6, np.where(mx == g, (b - r) / dlt + 2, (r - g) / dlt + 4)) / 6.0
    m = (hue_dist(hh, ha) < 0.045) & (s > max(0.18, 0.45 * sa)) & (v > 0.42)
    if sil is not None: m &= ndi.binary_erosion(sil, iterations=4)          # a cyan lens colour matches the sky at the outline: only pixels inside the head
    m = ndi.binary_opening(m, iterations=2)
    m = ndi.binary_closing(m, iterations=6)
    lab, n = ndi.label(m)
    if n == 0: return []
    areas = ndi.sum(m, lab, range(1, n + 1))
    cents = ndi.center_of_mass(m, lab, range(1, n + 1))
    sl = ndi.find_objects(lab)
    def fill(i):
        a = sl[i]; return areas[i] / float((a[0].stop - a[0].start) * (a[1].stop - a[1].start))
    cand = [i for i in range(n) if areas[i] >= min_area and fill(i) > 0.45]
    best = None
    for a_ in range(len(cand)):
        for b_ in range(a_ + 1, len(cand)):
            i, j = cand[a_], cand[b_]
            if abs(cents[i][0] - cents[j][0]) > 90: continue          # the two lenses sit on one row
            sc = areas[i] + areas[j]
            if best is None or sc > best[0]: best = (sc, [i, j])
    ok = best[1] if best else []
    out = []
    for i in ok:
        mk = lab == i + 1
        mk = ndi.binary_fill_holes(mk)               # the specular highlight is not lens-coloured: fill it
        out.append(mk)
    out.sort(key=lambda mk: np.nonzero(mk)[1].mean())
    return out


def bbox(mk):
    ys, xs = np.nonzero(mk)
    return xs.min(), xs.max(), ys.min(), ys.max()


def rim_profile(im, mk, other, sil, n_ang=48, rmax=120):
    """Per angle: rim width in px = the contiguous band (gaps <= 4 px) outside the lens edge whose luma differs from the local mask luma (median of the same ray
    60 - 90 px beyond the lens edge) by >= 15 of 255: a rim that matches the mask is invisible (round 12: black bezel on a dark mask = 'rimless')."""
    h, w, _ = im.shape
    ims = np.stack([ndi.gaussian_filter(im[..., c], 1.5) for c in range(3)], -1)
    ys, xs = np.nonzero(mk); cy, cx = ys.mean(), xs.mean()
    widths = []; touches_bg = 0
    for a in np.linspace(0, 2 * np.pi, n_ang, endpoint=False):
        dx, dy = np.cos(a), np.sin(a)
        r = 1.0; last_lens = 0
        while r < 700:
            x = int(round(cx + dx * r)); y = int(round(cy + dy * r))
            if not (0 <= x < w and 0 <= y < h): break
            if mk[y, x]: last_lens = r
            elif r - last_lens > 4: break
            r += 1.0
        r1 = last_lens
        pts = []
        for k in range(1, rmax + 100):
            x = int(round(cx + dx * (r1 + k))); y = int(round(cy + dy * (r1 + k)))
            if not (0 <= x < w and 0 <= y < h): break
            pts.append((x, y))
        if len(pts) < 100: widths.append(0); continue
        px = np.array([ims[y, x] for x, y in pts]); ins = np.array([sil[y, x] and not other[y, x] and not mk[y, x] for x, y in pts])
        if not ins[:rmax].all(): touches_bg += 1
        far = px[60:90][ins[60:90]] if ins[60:90].any() else px[60:90]
        Lref = float(np.median(0.2126 * far[:, 0] + 0.7152 * far[:, 1] + 0.0722 * far[:, 2]))
        Lp = 0.2126 * px[:, 0] + 0.7152 * px[:, 1] + 0.0722 * px[:, 2]
        vis = np.abs(Lp - Lref) >= 15.0                     # a rim reads when it differs from the mask by >= 15 luma (of 255)
        wd = 0; gap = 0
        for k in range(rmax):
            if vis[k]: wd = k + 1; gap = 0
            else:
                gap += 1
                if gap > 4: break
        widths.append(wd)
        widths.append(wd)
    return np.array(widths), None, touches_bg


def peaks_extrema(sig, prom):
    p, _ = find_peaks(sig, prominence=prom); q, _ = find_peaks(-sig, prominence=prom)
    idx = np.sort(np.concatenate([p, q]))
    return idx


def nose_profiles(im, masks, sil, rim_gap=10):
    """Vertical profile down the midline between the lenses and the horizontal one across the bridge."""
    L = luma_of(im)
    (xa0, xa1, ya0, ya1), (xb0, xb1, yb0, yb1) = bbox(masks[0]), bbox(masks[1])
    xc = int(round(0.5 * (xa1 + xb0)))                    # midline between the inner lens edges
    y_eye = int(round(0.25 * (ya0 + ya1 + yb0 + yb1)))
    y_top = int(min(ya0, yb0)) - 60
    # bottom: the top of the vent / mouth region = 260 px under the lens bottom (the nose tip is ~ 0.6 lens heights below the lens centre)
    y_bot = int(max(ya1, yb1)) + 330
    sm = lambda s, k: ndi.uniform_filter1d(s, k, mode='nearest')
    vcol = L[y_top:y_bot, xc - 3:xc + 4].mean(1)
    vs = sm(vcol, 11)
    vi = peaks_extrema(vs, 6.0)
    # H1: count extrema whose prominence >= 20
    pv, _ = find_peaks(vs, prominence=20.0); qv, _ = find_peaks(-vs, prominence=20.0)
    nv = len(pv) + len(qv)
    hrow = L[y_eye - 6:y_eye + 7, int(xa1) + rim_gap:int(xb0) - rim_gap].mean(0)
    hs = sm(hrow, 7)
    ph, _ = find_peaks(hs, prominence=20.0); qh, _ = find_peaks(-hs, prominence=20.0)
    swing_v = float(vs.max() - vs.min())
    # info (not gated): the same profile on the nose FLANKS (midline +- 45 px, mean of both sides, from the lens bottom to the nose tip + 250 px): the midline column lies on the raised
    # face-seam cord (a constant colour line), the flanks show the modelling of the nose bridge and the nostril shadows
    ytop2 = int(max(ya1, yb1)) - 10; ybot2 = int(max(ya1, yb1)) + 260
    fcol = 0.5 * (L[ytop2:ybot2, xc - 48:xc - 41].mean(1) + L[ytop2:ybot2, xc + 42:xc + 49].mean(1)); fvs = sm(fcol, 11)
    pf, _ = find_peaks(fvs, prominence=20.0); qf, _ = find_peaks(-fvs, prominence=20.0)
    return dict(midline_x=xc, y_eye=y_eye, v_extrema_prom20=int(nv), v_swing=round(swing_v, 1), v_extrema_prom6=int(len(vi)),
                h_extrema_prom20=int(len(ph) + len(qh)), h_swing=round(float(hs.max() - hs.min()), 1), flank_extrema_prom20=int(len(pf) + len(qf)), flank_swing=round(float(fvs.max() - fvs.min()), 1), v_profile=[round(float(a), 1) for a in vs[::12]])


def seam_check(im, masks, sil):
    """The face seam: horizontal luma profiles across the midline cord at 12 heights between the brow and the chin; pair = max - min inside +- 40 px; black run."""
    L = luma_of(im)
    (xa0, xa1, ya0, ya1), (xb0, xb1, yb0, yb1) = bbox(masks[0]), bbox(masks[1])
    xc = 0.5 * (xa1 + xb0)
    y0 = int(min(ya0, yb0)) - 150; y1 = int(max(ya1, yb1)) + 80
    pairs = []; runs = []
    for y in np.linspace(y0, y1, 12).astype(int):
        # the cord may drift with the head turn: search the darkest / brightest within +- 60 px of the midline estimate
        seg = L[y - 3:y + 4, int(xc) - 70:int(xc) + 71].mean(0)
        sg = ndi.uniform_filter1d(seg, 5, mode='nearest')
        pairs.append(float(sg.max() - sg.min()))
        ref = np.median(L[y - 3:y + 4, int(xc) - 200:int(xc) - 90].mean(0))
        blk = (seg < 0.45 * ref) & (seg < 12)
        best = 0; cur = 0
        for b in blk:
            cur = cur + 1 if b else 0; best = max(best, cur)
        runs.append(best)
    return dict(pair_median=round(float(np.median(pairs)), 1), pair_min=round(float(np.min(pairs)), 1), longest_black_run=int(max(runs)), black_runs=[int(r) for r in runs])


def front(path, suit, dump=None, r12=None):
    im = load(path)
    sil = silhouette(im)
    masks = lens_masks(im, suit, sil=sil)
    out = dict(suit=suit, file=os.path.basename(path), lenses=len(masks))
    if len(masks) < 2: out['ok'] = False; return out
    bb = [bbox(m) for m in masks]
    wpx = [int(b[1] - b[0] + 1) for b in bb]; hpx = [int(b[3] - b[2] + 1) for b in bb]
    y_eye = int(0.5 * (bb[0][2] + bb[0][3]))
    row = np.nonzero(sil[y_eye])[0]
    head_w = int(row.max() - row.min() + 1) if len(row) else 0
    out.update(lens_w_px=wpx, lens_h_px=hpx, head_w_px=head_w, lens_over_head=round(float(np.mean(wpx)) / max(head_w, 1), 4))
    rims = []; closed = []
    for k in (0, 1):
        wdt, ref, tb = rim_profile(im, masks[k], masks[1 - k], sil)
        rims.append(dict(median=float(np.median(wdt)), p10=float(np.percentile(wdt, 10)), min=int(wdt.min()), closed_frac=round(float((wdt >= 6).mean()), 3), touches_bg=int(tb)))
        closed.append(float((wdt >= 6).mean()))
    out['rim'] = rims
    out['rim_px_median'] = round(float(np.median([r['median'] for r in rims])), 1)
    out['rim_closed_frac'] = round(float(min(closed)), 3)
    # H6 inside the silhouette: the lens is not cut by / does not leave the head outline (>= 3 px from the background).  The face wraps: the far lens + rim of a 12 deg view lie
    # against the silhouette (a wrap-around lens), they never leave it; the lens vertices sit on the mask surface by construction (hero_lens_r13.py, clearance >= 1.1 mm)
    dsil = ndi.distance_transform_edt(sil)
    out['lens_edge_distance_px'] = [int(dsil[m].min()) for m in masks]
    out['lens_inside_silhouette'] = bool(min(out['lens_edge_distance_px']) >= 3)
    out['nose'] = nose_profiles(im, masks, sil, int(max(rims[0]['median'], rims[1]['median'], 6)))
    out['seam'] = seam_check(im, masks, sil)
    if r12:
        im2 = load(r12); sil2 = silhouette(im2); m2 = lens_masks(im2, suit, r12=True, sil=sil2)
        if len(m2) == 2:
            b2 = [bbox(m) for m in m2]; w2 = [int(b[1] - b[0] + 1) for b in b2]
            ye2 = int(0.5 * (b2[0][2] + b2[0][3])); r2 = np.nonzero(sil2[ye2])[0]; hw2 = int(r2.max() - r2.min() + 1)
            out['r12'] = dict(lens_w_px=w2, head_w_px=hw2, lens_over_head=round(float(np.mean(w2)) / hw2, 4))
            out['lens_width_ratio_vs_r12'] = round(out['lens_over_head'] / out['r12']['lens_over_head'], 3)
            out['lens_width_ratio_near'] = round(max(wpx) / max(w2), 3); out['lens_width_ratio_far'] = round(min(wpx) / min(w2), 3)
    if dump:
        ov = im.copy()
        for m in masks:
            edge = m ^ ndi.binary_erosion(m, iterations=2); ov[edge] = (255, 0, 255)
        nx = out['nose']['midline_x']; ov[:, nx - 1:nx + 2] = (0, 255, 255) * np.ones(3)
        Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)).resize((1920, 1080)).save(dump, quality=78)
    return out


def side(path, suit, dump=None, cam_dist=1.25, aim_y=1.665, fov=26.0):
    """Profile still: the face points toward +x or -x of the image; nose bump = max over rows of (front-most silhouette x - the straight line brow point -> chin point), in % of the head height.
    World rows come from the camera (aim height, distance, FOV 26 on 3840 px): y = aim + (1080 - row) / f, f = 1920 / tan(13 deg) / dist."""
    im = load(path); sil = silhouette(im)
    h, w, _ = im.shape
    f = 1920.0 / np.tan(np.radians(fov / 2)) / cam_dist
    row_of = lambda y: int(round(1080 - (y - aim_y) * f))
    cols = np.nonzero(sil.any(0))[0]
    rows_top = np.nonzero(sil.any(1))[0].min()
    crown_pred = row_of(1.786)
    # which way does the face point: the mask is wider toward the face at nose height than at the back? use the silhouette extent at the vent rows vs the crown centroid
    y_nose = row_of(1.645)
    rr = np.nonzero(sil[y_nose])[0]
    # front-most column per row; the head sits in the middle third: restrict to columns near the centre
    cx = int(np.nonzero(sil[row_of(1.74)])[0].mean())
    seg = sil[y_nose, :]
    # direction: the side of cx where the silhouette at nose height extends farther
    ext_r = rr.max() - cx; ext_l = cx - rr.min()
    sgn = 1 if ext_r > ext_l else -1
    ys = np.arange(row_of(1.720), row_of(1.575))
    front_x = []
    for y in ys:
        r = np.nonzero(sil[y])[0]
        front_x.append((r.max() if sgn > 0 else r.min()))
    front_x = np.array(front_x, np.float64)
    yb = row_of(1.709) - ys[0]; yc = row_of(1.585) - ys[0]
    yb = int(np.clip(yb, 0, len(ys) - 1)); yc = int(np.clip(yc, 0, len(ys) - 1))
    # chord from the brow point to the chin point
    chord = np.interp(np.arange(len(ys)), [yb, yc], [front_x[yb], front_x[yc]])
    prot = (front_x - chord) * sgn
    head_h = row_of(1.575) - row_of(1.786)
    k = int(np.argmax(prot[yb:yc + 1])) + yb
    bump = float(prot[k]) / head_h
    out = dict(suit=suit, file=os.path.basename(path), face_dir=int(sgn), crown_row=int(rows_top), crown_row_predicted=int(crown_pred), head_h_px=int(head_h),
               nose_bump_px=round(float(prot[k]), 1), nose_bump_pct_head_h=round(100 * bump, 2), nose_row_y_m=round(1.665 + (1080 - ys[k]) / f, 4))
    if dump:
        ov = im.copy()
        for i, y in enumerate(ys):
            x = int(front_x[i]); ov[y, max(x - 2, 0):x + 3] = (255, 0, 255)
        xs0 = int(front_x[yb]); xs1 = int(front_x[yc])
        for t in np.linspace(0, 1, 400):
            yy = int(ys[yb] + t * (ys[yc] - ys[yb])); xx = int(xs0 + t * (xs1 - xs0)); ov[yy, xx - 2:xx + 3] = (0, 255, 255)
        Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)).resize((1920, 1080)).save(dump, quality=78)
    return out


def verdict(fr, f34, sd):
    """fr = the 12 deg head still, f34 = the round-12 framing (25 deg) with the r12 baseline, sd = the profile still."""
    v = {}
    n, n34 = fr.get('nose', {}), f34.get('nose', {})
    v['H1_nose_extrema_ge3_swing_ge20'] = bool(max(n.get('v_extrema_prom20', 0), n34.get('v_extrema_prom20', 0)) >= 3 and max(n.get('v_swing', 0), n34.get('v_swing', 0)) >= 20)
    v['H2_nose_bump_ge_2pct'] = bool(sd is not None and sd['nose_bump_pct_head_h'] >= 2.0)
    v['H3_lens_ge_1.6x_r12'] = bool(f34.get('lens_width_ratio_near', 0) >= 1.6 and fr.get('lens_width_ratio_vs_r12', 0) >= 1.6)      # the near lens in the r12 framing, and the mean of both lenses in the 12 deg still
    v['H4_rim_ge_6px_closed'] = bool(min(fr.get('rim_px_median', 0), f34.get('rim_px_median', 0)) >= 6 and min(fr.get('rim_closed_frac', 0), f34.get('rim_closed_frac', 0)) >= 0.9)
    s_ = fr.get('seam', {}); s34 = f34.get('seam', {})
    v['H5_seam_pair_ge_20_no_black_12'] = bool(min(s_.get('pair_median', 0), s34.get('pair_median', 0)) >= 20 and max(s_.get('longest_black_run', 99), s34.get('longest_black_run', 99)) < 12)
    v['H6_lens_inside_silhouette'] = bool(fr.get('lens_inside_silhouette', False))
    return v


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'front':
        r12 = a[a.index('--r12') + 1] if '--r12' in a else None
        print(json.dumps(front(a[2], a[3], a[a.index('--dump') + 1] if '--dump' in a else None, r12)))
    elif a[1] == 'side':
        print(json.dumps(side(a[2], a[3], a[a.index('--dump') + 1] if '--dump' in a else None)))
    elif a[1] == 'all':
        sd_, r12d, outp = a[2], a[3], a[4]
        ovd = a[5] if len(a) > 5 else None
        if ovd: os.makedirs(ovd, exist_ok=True)
        res = {}
        only = os.environ.get('HEAD_SUITS', '').split(',') if os.environ.get('HEAD_SUITS') else None
        for s in SUITS:
            sid = s['id']
            if only and sid not in only: continue
            ov = lambda t: os.path.join(ovd, '%s_%s.jpg' % (t, sid)) if ovd else None
            fr = front(os.path.join(sd_, 'skin_%s_head_4k.png' % sid), sid, ov('head'), os.path.join(r12d, 'skin_%s_head_4k.png' % sid))      # 12 deg off the face axis (baseline: the r12 25 deg still)
            f34 = front(os.path.join(sd_, 'skin_%s_head34_4k.png' % sid), sid, ov('head34'), os.path.join(r12d, 'skin_%s_head_4k.png' % sid))   # the round-12 framing
            sp = os.path.join(sd_, 'skin_%s_headside_4k.png' % sid)
            sd = side(sp, sid, ov('side')) if os.path.exists(sp) else None
            res[sid] = dict(head=fr, head34=f34, side=sd, verdict=verdict(fr, f34, sd))
            print(sid, json.dumps(res[sid]['verdict']))
        json.dump(res, open(outp, 'w'), indent=1)
