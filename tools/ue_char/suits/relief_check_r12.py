#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 12 checkers on the REAL-GAME 4K chest stills (S3), the critic's three numbers:

  relief  every panel / net line shows a lit / shadow edge pair with luma difference >= 20
          lines = thin structures that differ from their 31 px median background (Lab dE > 16, removed by a 21 px opening), half width 2.5 - 14 px
          (stitch dashes are thinner and excluded); on every centre-line pixel the luma is read at +-0.5 half widths across the line (structure-tensor
          normal) -> delta = |L+ - L-|.  Lines are scored in 64 px cells (>= 25 centre-line pixels): cell = median delta.  Reported: share of cells >= 20,
          median, worst cells.  A flat print has delta ~ 0 (both flanks the same colour); a raised cord lit from one side has one bright and one dark flank.
  sash    inside any sash / chevron panel (the large accent-hue regions, holes filled, eroded 8 px from the border) no run longer than 10 px of pixels darker
          than the panel median - 15 (median over the panel pixels within 61 px: lighting falloff across a curved panel is not a defect), rows and columns.
  jog     sash / chevron edge continuity in a region: the top and bottom boundary of the accent panel per column, deviation from a smooth (61 px quadratic)
          fit; max deviation and the largest column-to-column jump beyond the local slope (critic: Verdant chevron jog 24 px at (1333-1357, 1610-1680)).

  python3 relief_check_r12.py relief IMG [--accent '#rrggbb'] [--roi x0 y0 x1 y1] [--overlay OUT.jpg]
  python3 relief_check_r12.py sash IMG --accent '#rrggbb' [--roi ...] [--overlay OUT.jpg] [--probe x y ...]
  python3 relief_check_r12.py jog IMG --accent '#rrggbb' --roi x0 y0 x1 y1
All print one JSON object."""
import sys, json
import numpy as np
import cv2
from scipy import ndimage as ndi


def opt(a, k, n=1, d=None, cast=float):
    if k in a:
        i = a.index(k); v = a[i + 1:i + 1 + n]
        return [cast(x) for x in v] if n > 1 else cast(v[0])
    return d


def luma(bgr):
    f = bgr.astype(np.float32)
    return 0.0722 * f[..., 0] + 0.7152 * f[..., 1] + 0.2126 * f[..., 2]


def relief(img, roi=None, overlay=None):
    im = cv2.imread(img)
    if roi: im = im[roi[1]:roi[3], roi[0]:roi[2]]
    L = luma(im)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    bg = np.stack([cv2.medianBlur(np.ascontiguousarray(lab[..., c]).astype(np.uint8), 31).astype(np.float32) for c in range(3)], -1)
    dE = np.linalg.norm(lab - bg, axis=-1)
    m = (dE > 16).astype(np.uint8)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    thin = m & (1 - cv2.morphologyEx(m, cv2.MORPH_OPEN, ker))
    thin = cv2.morphologyEx(thin, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    dt = cv2.distanceTransform(thin, cv2.DIST_L2, 5)
    # orientation of the line from the structure tensor of the mask
    mf = ndi.gaussian_filter(thin.astype(np.float32), 2.0)
    gy, gx = np.gradient(mf)
    Jxx = ndi.gaussian_filter(gx * gx, 4); Jyy = ndi.gaussian_filter(gy * gy, 4); Jxy = ndi.gaussian_filter(gx * gy, 4)
    ang = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)          # direction of the strongest gradient = the line's normal
    nx, ny = np.cos(ang), np.sin(ang)
    H, W = L.shape
    yy, xx = np.mgrid[0:H, 0:W]
    # centre line = distance-transform ridge along the normal
    def at(a, x, y): return ndi.map_coordinates(a, [y, x], order=1, mode='nearest')
    ys, xs = np.nonzero((dt >= 2.5) & (dt <= 14))
    d0 = dt[ys, xs]
    dp = at(dt, xs + nx[ys, xs], ys + ny[ys, xs]); dm = at(dt, xs - nx[ys, xs], ys - ny[ys, xs])
    ridge = (d0 >= dp) & (d0 >= dm)
    ys, xs, d0 = ys[ridge], xs[ridge], d0[ridge]
    off = 0.5 * d0
    lp = at(L, xs + off * nx[ys, xs], ys + off * ny[ys, xs]); lm = at(L, xs - off * nx[ys, xs], ys - off * ny[ys, xs])
    delta = np.abs(lp - lm)
    cells = {}
    for y, x, dv in zip(ys // 64, xs // 64, delta):
        cells.setdefault((int(y), int(x)), []).append(float(dv))
    rows = [(k, float(np.median(v)), len(v)) for k, v in cells.items() if len(v) >= 25]
    med = np.array([r[1] for r in rows]) if rows else np.zeros(0)
    res = dict(image=img, roi=roi, centre_pixels=int(len(delta)), cells=len(rows), cells_ge20=int((med >= 20).sum()),
               share_cells_ge20=round(float((med >= 20).mean()), 3) if len(med) else None,
               median_cell_delta=round(float(np.median(med)), 1) if len(med) else None,
               p10_cell_delta=round(float(np.percentile(med, 10)), 1) if len(med) else None,
               median_pixel_delta=round(float(np.median(delta)), 1) if len(delta) else None,
               worst_cells=[dict(x=k[1] * 64 + 32 + (roi[0] if roi else 0), y=k[0] * 64 + 32 + (roi[1] if roi else 0), delta=round(v, 1), n=n) for k, v, n in sorted(rows, key=lambda r: r[1])[:8]])
    if overlay:
        ov = im.copy()
        for k, v, n in rows:
            c = (0, 200, 0) if v >= 20 else (0, 0, 255)
            cv2.rectangle(ov, (k[1] * 64, k[0] * 64), (k[1] * 64 + 63, k[0] * 64 + 63), c, 2)
            cv2.putText(ov, '%.0f' % v, (k[1] * 64 + 4, k[0] * 64 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
        cv2.imwrite(overlay, ov)
    return res


def accent_mask(im, accent, tol_h=14.0):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV_FULL).astype(np.float32)
    h = hsv[..., 0] / 255 * 360; s = hsv[..., 1] / 255; v = hsv[..., 2] / 255
    a = np.uint8([[[int(accent[5:7], 16), int(accent[3:5], 16), int(accent[1:3], 16)]]])
    ah = cv2.cvtColor(a, cv2.COLOR_BGR2HSV_FULL)[0, 0].astype(np.float32); ahue = ah[0] / 255 * 360; asat = ah[1] / 255
    dh = np.abs((h - ahue + 180) % 360 - 180)
    # the hero only (the stage background is the per-row median colour): a pale accent would otherwise match the sky / floor
    med = np.median(im, axis=1, keepdims=True)
    hero = np.abs(im.astype(np.float32) - med.astype(np.float32)).max(-1) > 38
    hero = cv2.morphologyEx(hero.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8)) > 0
    if asat < 0.25:      # a pale accent (bone): match by low saturation + high value
        return ((s < 0.30) & (v > 0.55) & hero).astype(np.uint8)
    return ((dh < tol_h) & (s > 0.30) & (v > 0.35) & hero).astype(np.uint8)


def panels(im, accent, min_frac=0.004, inner=True):
    m = accent_mask(im, accent)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19)))     # accent NETS / piping (thin) are not panels
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))    # a dark line crossing a panel stays inside it
    hole = ndi.binary_fill_holes(m) & (m == 0)          # only SMALL holes (a dot of dark inside a panel) are filled; a ring / net cell is not a panel
    hl_n, hl, hst, _ = cv2.connectedComponentsWithStats(hole.astype(np.uint8), 8)
    small = np.isin(hl, [i for i in range(1, hl_n) if hst[i, 4] < 2500])
    m = (m | small).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    H, W = m.shape
    if n < 2: return keep
    inner_ok = [i for i in range(1, n) if (not inner) or (st[i, 0] > 0 and st[i, 0] + st[i, 2] < W and st[i, 1] > 0)]      # a panel lies inside the hero: a region touching the frame edge is background / a cut-off limb
    if not inner_ok: return keep
    big = int(max(st[i, 4] for i in inner_ok))
    for i in inner_ok:
        x, y, w, h, area = st[i]
        # the sash / chevron = the largest accent panel (+ any other at least half its size: a double sash); the chest glyph, sleeves and rings are smaller
        if area >= min_frac * H * W and area >= 0.5 * big:
            keep[lab == i] = 1
    return keep


def sash(img, accent, roi=None, overlay=None, probes=()):
    im = cv2.imread(img)
    ox, oy = (roi[0], roi[1]) if roi else (0, 0)
    if roi: im = im[roi[1]:roi[3], roi[0]:roi[2]]
    L = luma(im)
    pm = panels(im, accent)
    inner = cv2.erode(pm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))      # 12 px in from the border strip / cut end
    if inner.sum() == 0:
        return dict(image=img, accent=accent, panel_px=0, note='no accent panel found')
    k = 61
    num = cv2.boxFilter(L * inner, -1, (k, k), normalize=False); den = cv2.boxFilter(inner.astype(np.float32), -1, (k, k), normalize=False)
    ref = num / np.maximum(den, 1)
    dark = (inner > 0) & (L < ref - 15)
    def runs(mask):
        best = 0; where = None
        for axis in (0, 1):
            mm = (mask if axis == 1 else mask.T).astype(np.int8)
            pad = np.pad(mm, ((0, 0), (1, 1)))
            d = np.diff(pad, axis=1)
            rs, cs = np.nonzero(d == 1); re_, ce = np.nonzero(d == -1)
            if len(rs) == 0: continue
            ln = ce - cs; j = int(np.argmax(ln))
            if ln[j] > best:
                best = int(ln[j]); where = (int(cs[j]), int(rs[j])) if axis == 1 else (int(rs[j]), int(cs[j]))
        return best, where
    best, where = runs(dark)
    n_long = 0
    lab_n, lab, stt, cen = cv2.connectedComponentsWithStats(dark.astype(np.uint8), 8)
    comps = []
    for i in range(1, lab_n):
        ext = max(stt[i, 2], stt[i, 3])
        if ext > 10:
            n_long += 1; comps.append(dict(x=int(cen[i, 0]) + ox, y=int(cen[i, 1]) + oy, extent_px=int(ext), px=int(stt[i, 4])))
    pr = []
    for (px, py) in probes:
        x, y = px - ox, py - oy
        if 0 <= x < L.shape[1] and 0 <= y < L.shape[0]:
            pr.append(dict(x=px, y=py, luma=round(float(L[y, x]), 1), local_panel_median=round(float(ref[y, x]), 1), inside_panel=bool(inner[y, x])))
    res = dict(image=img, accent=accent, panel_px=int(inner.sum()), panel_luma_median=round(float(np.median(L[inner > 0])), 1),
               longest_dark_run_px=best, longest_run_at=[where[0] + ox, where[1] + oy] if where else None, dark_components_gt10px=n_long,
               worst_components=sorted(comps, key=lambda c: -c['extent_px'])[:6], probes=pr, verdict='PASS' if best <= 10 else 'FAIL')
    if overlay:
        ov = im.copy(); ov[inner > 0] = (0.6 * ov[inner > 0] + 0.4 * np.array([255, 160, 0])).astype(np.uint8); ov[dark] = (0, 0, 255)
        cv2.imwrite(overlay, ov)
    return res


def jog(img, accent, roi, overlay=None):
    """Continuity of the sash / chevron LOWER EDGE: per column the end of the longest run of warm accent pixels (luma > 60, R - B > 40), 9-column running median; the track is compared with a 61 px quadratic fit; jumps are measured between neighbouring columns only, beyond the local slope.
    A fold or a jog of the border shows as one large jump (round 11 Verdant: the 24 px step at x 1333-1357)."""
    im = cv2.imread(img)[roi[1]:roi[3], roi[0]:roi[2]]
    L = luma(im); H, W = L.shape
    f = im.astype(np.float32)
    panel = ((L > 60) & (f[..., 2] - f[..., 0] > 40)).astype(np.int8)    # the warm accent panel (R - B > 40): its lower edge meets the dark border strip
    xs, ys = [], []
    for x in range(W):
        c_ = np.concatenate([[0], panel[:, x], [0]]); d_ = np.diff(c_)
        st_, en_ = np.nonzero(d_ == 1)[0], np.nonzero(d_ == -1)[0]
        if len(st_) == 0: continue
        k = int(np.argmax(en_ - st_))
        if en_[k] - st_[k] < 12 or en_[k] >= H: continue                        # the panel's lower edge must lie inside the crop
        xs.append(x); ys.append(float(en_[k]))
    xs = np.array(xs); ys = np.array(ys, float)
    if len(xs) < 60: return dict(image=img, roi=roi, columns=int(len(xs)), verdict='n/a')
    ys = ndi.median_filter(ys, size=9, mode='nearest')      # isolated twill / shading pixels go, a real step (a run of columns) stays
    fit = np.zeros_like(ys)
    for i in range(len(xs)):
        sel = np.abs(xs - xs[i]) <= 30
        fit[i] = np.polyval(np.polyfit(xs[sel], ys[sel], 2), xs[i]) if sel.sum() >= 5 else ys[i]
    dev = np.abs(ys - fit); slope = np.gradient(fit, xs)
    adj = np.diff(xs) == 1
    jump = np.where(adj, np.abs(np.diff(ys) - slope[:-1]), 0.0)
    jump[:15] = 0; jump[-15:] = 0                         # the first / last 15 columns of the track: the panel's cut end and the crop border
    k = int(np.argmax(jump))
    if overlay:
        ov = im.copy()
        for x_, y_ in zip(xs, ys): cv2.circle(ov, (int(x_), int(y_)), 1, (255, 0, 255), -1)
        cv2.imwrite(overlay, ov)
    sel = (xs[:-1] + roi[0] >= 1320) & (xs[:-1] + roi[0] <= 1400)       # the critic's round-11 jog columns (1333-1357) +- margin
    jr = float(jump[sel].max()) if sel.any() else None
    return dict(image=img, roi=roi, columns=int(len(xs)), max_dev_px=round(float(dev.max()), 2), max_jump_px=round(float(jump.max()), 2),
                jump_at=[int(xs[k] + roi[0]), int(ys[k] + roi[1])], jump_at_critic_x1320_1400=None if jr is None else round(jr, 2),
                verdict='PASS' if jump.max() <= 2.0 else 'FAIL', verdict_at_critic_x='PASS' if (jr is not None and jr <= 2.0) else 'FAIL')


def main():
    a = sys.argv[1:]
    cmd, img = a[0], a[1]
    roi = opt(a, '--roi', 4, None, int); acc = opt(a, '--accent', 1, None, str); ov = opt(a, '--overlay', 1, None, str)
    if cmd == 'relief': r = relief(img, roi, ov)
    elif cmd == 'sash':
        pr = []
        if '--probe' in a:
            v = a[a.index('--probe') + 1:]
            v = [int(t) for t in v if t.lstrip('-').isdigit()]
            pr = list(zip(v[0::2], v[1::2]))
        r = sash(img, acc, roi, ov, pr)
    elif cmd == 'jog': r = jog(img, acc, roi, ov)
    else: raise SystemExit(__doc__)
    print(json.dumps(r))


if __name__ == '__main__':
    main()
