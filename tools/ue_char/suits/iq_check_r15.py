#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 15 image-quality checks of the critic r14 items, measured on the 4K stills of the REAL game (lossless PNG originals; the r14 stills as the baseline) + side-by-side crops
(a number never replaces looking at the crop):

  Q5  Ash sash end ("a lime cord floats 40 px off the Ash sash end, box 1490-1540 x 760-1150"): the accent pipe (thin lime blob left of the lime panel) must JOIN the end: per row of the pipe,
      the number of non-dark pixels between the pipe's right edge and the DEEP border cord (first pixel with luma < 55) is the gap; the gate is <= 5 px at the 90th percentile of the rows
      and no pipe pixel further than 5 px from the border; the same crop is saved for the eye
  Q6  Verdant armpit piping ("pinched, box 1160-1270 x 1150-1270"): the amber cord near the box: its vertical thickness per column along the cord's own run (first to last column, without the
      tapered ends); pinch = the smallest thickness / the median thickness (1 = even; a gap or a point = 0); the gate is >= 0.5.  Round 15 ends the cord at the shoulder cap's edge on the arm
      (cap.r_in 7.5 cm on the torso side) instead of running it over the armpit crease, so the report also says where the cord starts / ends
  Q7  texture stretch under the brow (headside stills): the hood trim line (the suit's accent colour) over the brow: the width of its 20 -> 80 % edge rise and its thickness (px, perpendicular to
      the line, median over the columns of a window 30 - 200 px behind the brow tip) against (a) the same measure on the trim 520 - 780 px behind it (the temple, no relief): gate brow / temple <= 1.5,
      and (b) the same suit's round-14 still: the brow edge rise r15 / r14 (the 4096 base colour at 0.7 - 1.0 mm per texel smeared the brow trim; the 8192 map of round 15 should sharpen it).
      The instrument is noisy (glints on the lens / a flash can enter a window): `windows_sane` says the window held the trim; read the crops `q7_brow_<suit>.jpg`

  python3 iq_check_r15.py <stills dir r15 (png)> <stills dir r14 (png or jpg)> <crop out dir>  -> JSON on stdout
"""
import sys, os, json
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import head_check_r13 as H13  # noqa: E402
import iq_check_r14 as Q14  # noqa: E402
Image.MAX_IMAGE_PIXELS = None
luma, sat = Q14.luma, Q14.sat


def q5_pipe(im, accent=(168, 224, 90), box=(1300, 600, 2300, 1300)):       # wide box: the hero's x in the chest framing moves by ~100 px with the idle pose (r14: pipe at x 1495 - 1534, r15 1650)
    x0, y0, x1, y1 = box
    d = np.linalg.norm(im - np.array(accent, np.float32), axis=2)
    m = (d < 70) & (luma(im) > 90)
    m[:, :x0] = False; m[:, x1:] = False; m[:y0] = False; m[y1:] = False
    lab, n = ndi.label(m)      # no opening: the pipe is 1 mm = 4 - 5 px wide
    if n == 0: return dict(ok=False, why='no accent pixels')
    comps = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 150: continue
        comps.append((i, len(ys), xs.min(), xs.max(), ys.min(), ys.max()))
    if len(comps) < 2: return dict(ok=False, why='components %d' % len(comps), comps=[[int(v) for v in c[1:]] for c in comps])
    panel = max(comps, key=lambda c: c[1])
    # the pipe: the most elongated of the other components left of the panel (height >> width)
    cand = [c for c in comps if c[0] != panel[0] and c[3] < panel[3] and (c[5] - c[4]) > 4 * max(c[3] - c[2], 1)]
    if not cand: return dict(ok=False, why='no pipe component', comps=[[int(v) for v in c[1:]] for c in comps])
    pipe = max(cand, key=lambda c: c[5] - c[4])
    pm = lab == pipe[0]; Lm = luma(im)
    gaps = []; offs = []
    for r in range(pipe[4] + 6, pipe[5] - 5):
        xs = np.nonzero(pm[r])[0]
        if not len(xs): continue
        xr = int(xs.max()); g = 0; x = xr + 1
        while x < x1 and Lm[r, x] >= 55 and g < 80: g += 1; x += 1
        gaps.append(g)
    gaps = np.array(gaps, np.float64)
    ys, xs = np.nonzero(pm)
    return dict(ok=True, pipe_rows=[int(pipe[4]), int(pipe[5])], pipe_x=[int(pipe[2]), int(pipe[3])], pipe_width_px=round(float(np.median([np.ptp(np.nonzero(pm[r])[0]) + 1 for r in range(pipe[4] + 6, pipe[5] - 5) if pm[r].any()])), 1),
                panel_x_min=int(panel[2]), gap_to_border_median_px=round(float(np.median(gaps)), 1), gap_to_border_p90_px=round(float(np.percentile(gaps, 90)), 1), gap_to_border_max_px=int(gaps.max()),
                critic_box_accent_pixels=int(m[760:1150, 1490:1540].sum()), pipe_center_x=int((pipe[2] + pipe[3]) // 2),
                Q5_pipe_joins_end_le_5px=bool(np.percentile(gaps, 90) <= 5.0))


def q6_armpit(im, accent, box=(1160, 1150, 1270, 1270), wide=(1040, 1040, 1420, 1360)):
    """vertical thickness of the amber cord along its path through the critic's box (columns in which the cord exists on both sides of the box)"""
    H, S, V = 0, 1, 2
    x = im / 255.0; mx = x.max(2); mn = x.min(2); s = (mx - mn) / (mx + 1e-6)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]; dl = mx - mn + 1e-9
    hh = np.where(mx == r, ((g - b) / dl) % 6, np.where(mx == g, (b - r) / dl + 2, (r - g) / dl + 4)) / 6.0
    ha = H13.rgb2hsv(np.array(accent, np.float32) / 255.0)[0]
    m = (H13.hue_dist(hh, ha) < 0.05) & (s > 0.45) & (mx > 0.35)
    wx0, wy0, wx1, wy1 = wide
    mm = np.zeros_like(m); mm[wy0:wy1, wx0:wx1] = m[wy0:wy1, wx0:wx1]
    mm = ndi.binary_opening(mm, iterations=1)
    cols = range(box[0] - 80, box[2] + 80)
    th = []
    for c in cols:
        colm = mm[wy0:wy1, c]
        lab, n = ndi.label(colm)
        if not n: th.append(0); continue
        sizes = ndi.sum(colm, lab, range(1, n + 1)); th.append(int(sizes.max()))
    th = np.array(th, np.float64)
    nz = np.nonzero(th > 0)[0]
    med = float(np.median(th[th > 0])) if (th > 0).any() else 0.0
    if len(nz) < 20 or med <= 0:
        return dict(box=list(box), cord_columns=int(len(nz)), cord_found=False, Q6_unpinched_ge_0p5=False)
    first, last = int(nz[0]), int(nz[-1])
    inner = th[first + 8:max(last - 14, first + 9)]            # the cord's own run, without the tapered ends (the cord may END before the box: then it is not crossing the crease at all)
    pinch = float(inner.min() / med) if len(inner) else 0.0
    gaps = int((inner == 0).sum())
    ends_in_box = bool(box[0] - 80 + last < box[2])
    return dict(box=list(box), cord_found=True, cord_columns=int(len(nz)), first_col=box[0] - 80 + first, last_col=box[0] - 80 + last, cord_ends_before_box_right_edge=ends_in_box,
                median_thickness_px=round(med, 1), min_thickness_px=int(inner.min()) if len(inner) else 0, pinch_ratio=round(pinch, 2), gap_columns_in_run=gaps, Q6_unpinched_ge_0p5=bool(pinch >= 0.5))


def trim_edge_width(im, accent, win):
    """median 20 -> 80 % edge rise and thickness (px, perpendicular to the trim) of the accent-coloured hood trim over the columns [x0, x1) of a window: per column the FIRST (top-most) accent run
    at or below row y0 (the trim is the top-most accent line under the brow flashes, above the lens)"""
    x0, x1, y0, y1 = win
    x = im / 255.0; mx = x.max(2); mn = x.min(2); s = (mx - mn) / (mx + 1e-6)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]; dl = mx - mn + 1e-9
    hh = np.where(mx == r, ((g - b) / dl) % 6, np.where(mx == g, (b - r) / dl + 2, (r - g) / dl + 4)) / 6.0
    ha = H13.rgb2hsv(np.array(accent, np.float32) / 255.0)[0]
    a = np.clip(1.0 - H13.hue_dist(hh, ha) / 0.07, 0, 1) * np.clip((s - 0.25) / 0.35, 0, 1) * np.clip((mx - 0.2) / 0.3, 0, 1)
    a = ndi.gaussian_filter(a, 0.7)
    cen = []; widths = []; rises = []
    for c in range(x0, x1):
        col = a[y0:y1, c]
        hit = np.nonzero(col > 0.45)[0]
        if not len(hit): continue
        k0 = int(hit[0]); k1 = k0
        while k1 + 1 < len(col) and col[k1 + 1] > 0.2: k1 += 1
        k0b = k0
        while k0b - 1 >= 0 and col[k0b - 1] > 0.2: k0b -= 1
        run = col[k0b:k1 + 1]; pk = run.max(); kp = int(np.argmax(run)) + k0b
        if k1 - k0b > 90: continue                                 # not a thin line (the lens / a flash)
        fw = np.nonzero(run > 0.5 * pk)[0]; fwhm = int(fw.max() - fw.min() + 1)
        up = col[:kp][::-1]; dn = col[kp + 1:]
        def edge(v):
            i20 = next((i for i, q in enumerate(v) if q < 0.2 * pk), None); i80 = next((i for i, q in enumerate(v) if q < 0.8 * pk), None)
            return None if i20 is None or i80 is None else i20 - i80
        eu, ed = edge(up), edge(dn)
        cen.append((c, kp + y0)); widths.append(fwhm)
        if eu is not None and ed is not None: rises.append(0.5 * (eu + ed))
    if len(cen) < 20: return None
    cen = np.array(cen, np.float64); A = np.stack([cen[:, 0], np.ones(len(cen))], 1)
    sl = np.linalg.lstsq(A, cen[:, 1], rcond=None)[0][0]; cs = 1.0 / np.sqrt(1 + sl * sl)
    return dict(columns=len(cen), slope=round(float(sl), 3), thickness_perp_px=round(float(np.median(widths) * cs), 2), edge_rise_perp_px=round(float(np.median(rises) * cs), 2) if rises else None)


def q7_brow_stretch(im, suit, accent):
    """brow window = the 260 px behind the brow's front-most column; temple window = 520 - 780 px behind it"""
    sil = H13.silhouette(im)
    f = 1920.0 / np.tan(np.radians(13.0)) / 1.25
    row_of = lambda y: int(round(1080 - (y - 1.665) * f))
    cx = int(np.nonzero(sil[row_of(1.74)])[0].mean()); rr = np.nonzero(sil[row_of(1.645)])[0]
    sgn = 1 if (rr.max() - cx) > (cx - rr.min()) else -1
    rows = np.arange(row_of(1.745), row_of(1.60)); fx = np.array([(np.nonzero(sil[r])[0].max() if sgn > 0 else np.nonzero(sil[r])[0].min()) for r in rows], np.float64)
    seg = fx[row_of(1.735) - rows[0]:row_of(1.693) - rows[0] + 1] * sgn
    ib = row_of(1.735) - rows[0] + int(np.argmax(seg)); xb = int(fx[ib]); rb = int(rows[ib])
    def win(a, b_): return (min(xb - sgn * a, xb - sgn * b_), max(xb - sgn * a, xb - sgn * b_), rb - 80, rb + 700)
    wb = trim_edge_width(im, accent, win(30, 200)); wt = trim_edge_width(im, accent, win(520, 780))
    if not wb or not wt or not wb.get('edge_rise_perp_px') or not wt.get('edge_rise_perp_px'): return dict(ok=False, brow=wb, temple=wt)
    ratio = wb['edge_rise_perp_px'] / max(wt['edge_rise_perp_px'], 0.5); rt = wb['thickness_perp_px'] / max(wt['thickness_perp_px'], 0.5)
    sane = (-1.0 <= wb['slope'] <= -0.2) and (-1.0 <= wt['slope'] <= -0.2)           # the window really holds the trim (it descends toward the temple), not a glint on the lens
    return dict(ok=True, brow_front_x=xb, brow=wb, temple=wt, edge_rise_ratio=round(ratio, 2), thickness_ratio=round(rt, 2), windows_sane=bool(sane),
                brow_temple_ratio_le_1p5=bool(sane and ratio <= 1.5 and rt <= 1.5))


def main():
    cur, base, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    cfg = json.load(open(os.path.join(HERE, 'suits.json')))
    acc = {s['id']: s.get('style', {}).get('palette', {}).get('accent', '#e0780c') for s in cfg['suits']}
    rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    res = {}
    def L_(name):
        p = Q14.find(cur, name); q = Q14.find(base, name)
        return (H13.load(p) if p else None), (H13.load(q) if q else None)
    a15, a14 = L_('skin_ash_chest_4k')
    if a15 is not None:
        res['Q5_ash_pipe'] = dict(r15=q5_pipe(a15, rgb(acc['ash'])), r14=q5_pipe(a14, rgb(acc['ash'])) if a14 is not None else None)
        if a14 is not None: Q14.crop_pair(a14, a15, (1380, 640, 1720, 1260), os.path.join(out, 'q5_ash_sash_end.jpg'), 1.0, ('round 14', 'round 15'))
    v15, v14 = L_('skin_verdant_chest_4k')
    if v15 is not None:
        res['Q6_verdant_armpit'] = dict(r15=q6_armpit(v15, rgb(acc['verdant'])), r14=q6_armpit(v14, rgb(acc['verdant'])) if v14 is not None else None)
        if v14 is not None: Q14.crop_pair(v14, v15, (1040, 1040, 1420, 1360), os.path.join(out, 'q6_verdant_armpit.jpg'), 2.0, ('round 14', 'round 15'))
    q7 = {}
    for s in cfg['suits']:
        c15, c14 = L_('skin_%s_headside_4k' % s['id'])
        if c15 is None: continue
        try:
            q7[s['id']] = dict(r15=q7_brow_stretch(c15, s['id'], rgb(acc[s['id']])), r14=q7_brow_stretch(c14, s['id'], rgb(acc[s['id']])) if c14 is not None else None)
            a_, b_ = q7[s['id']]['r15'], q7[s['id']]['r14']
            if a_ and b_ and a_.get('brow') and b_.get('brow') and a_['brow'].get('edge_rise_perp_px') and b_['brow'].get('edge_rise_perp_px'):
                q7[s['id']]['brow_edge_rise_r15_over_r14'] = round(a_['brow']['edge_rise_perp_px'] / b_['brow']['edge_rise_perp_px'], 2)
                q7[s['id']]['brow_thickness_r15_over_r14'] = round(a_['brow']['thickness_perp_px'] / max(b_['brow']['thickness_perp_px'], 0.5), 2)
            if c14 is not None and s['id'] in ('verdant', 'tessera', 'cinder', 'plum'):
                bx = (q7[s['id']]['r15'] or {}).get('brow_front_x', 2260) if q7[s['id']]['r15'] else 2260
                Q14.crop_pair(c14, c15, (bx - 420, 560, bx + 80, 1060), os.path.join(out, 'q7_brow_%s.jpg' % s['id']), 1.0, ('round 14', 'round 15'))
        except Exception as e:
            q7[s['id']] = dict(error=str(e)[:200])
    res['Q7_brow_stretch'] = q7
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
