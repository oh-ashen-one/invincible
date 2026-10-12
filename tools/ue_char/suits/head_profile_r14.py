#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14 CPU instrument for the sculpted hero mask: the silhouette of the head seen exactly from the side (+x), a front relief shading with the horizontal luma
lines of the cheek test, measured on the MESH of the hero GLB (mask + the two lens primitives) before any engine hold.  The real-game numbers come from
head_check_r14.py on the 4K stills; this tool is the design aid that tells the sculpt where the recess, the brow and the cheek bones have to be.

  python3 head_profile_r14.py <SK_Hero.glb> [--png out.png] [--json out.json] [--relief out.png]

Definitions (the r13 critic's three tests as a mesh silhouette; head height HH = crown to chin along y):
  T1  bridge recess: the front silhouette z_f(y) between the brow's front-most point and the nose tip dips behind the straight chord brow -> nose tip by >= 1.5 % HH
  T2  brow overhang: the brow's front-most point is >= 1 % HH in front of (a) the top of the lens + rim (front-most vertex of the rim in the top quarter of the lens rows)
      and (b) EVERY rim / lens vertex (T2b, stricter: reported)
  T3  (r13 H2 kept) nose bump >= 2 % HH over the brow -> chin chord; mouth bulge and chin plane: the silhouette z at the mouth / chin rows relative to the groove between them
"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'suit8')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import glbedit  # noqa: E402
import skinfit  # noqa: E402


def load(path):
    g = glbedit.Glb(path); j = g.j; raw = bytes(g.bin)
    body = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan')
    out = {}
    for p in j['meshes'][body['mesh']]['primitives']:
        name = j['materials'][p['material']]['name']
        P = skinfit.accessor(j, raw, p['attributes']['POSITION']).astype(np.float64)
        F = skinfit.accessor(j, raw, p['indices']).reshape(-1, 3).astype(int)
        out[name] = (P, F)
    return out


def comb(*prs):
    Ps = []; Fs = []; o = 0
    for P, F in prs:
        Ps.append(P); Fs.append(F + o); o += len(P)
    return np.vstack(Ps), np.vstack(Fs)


def front_profile(P, F, y0=1.50, y1=1.80, step=0.0005):
    """Exact front silhouette seen from the side: per height y the largest z over the surface (triangle slices at y).  Returns (ys, z_front, |x| of the front point);
    rows with no surface are interpolated."""
    ys = np.arange(y0, y1, step)
    T = P[F]
    tmin = T[:, :, 1].min(1); tmax = T[:, :, 1].max(1)
    keep = (tmax >= y0) & (tmin <= y1) & (T[:, :, 2].max(1) > 0.0)
    T = T[keep]; tmin = tmin[keep]; tmax = tmax[keep]
    zf = np.full(len(ys), np.nan); xa = np.full(len(ys), np.nan)
    for i, y in enumerate(ys):
        m = (tmin <= y) & (tmax >= y)
        if not m.any(): continue
        t = T[m]
        best = -9.0; bx = 0.0
        for a, b in ((0, 1), (1, 2), (2, 0)):
            pa, pb = t[:, a], t[:, b]
            dy = pb[:, 1] - pa[:, 1]
            ok = (np.abs(dy) > 1e-12) & (((pa[:, 1] - y) * (pb[:, 1] - y)) <= 0)
            if not ok.any(): continue
            u = (y - pa[ok, 1]) / dy[ok]
            z = pa[ok, 2] + u * (pb[ok, 2] - pa[ok, 2]); x = pa[ok, 0] + u * (pb[ok, 0] - pa[ok, 0])
            k = np.argmax(z)
            if z[k] > best: best = z[k]; bx = abs(x[k])
        if best > -9: zf[i] = best; xa[i] = bx
    ok = ~np.isnan(zf)
    zf = np.interp(ys, ys[ok], zf[ok])
    return ys, zf, xa


def lmax(ys, zf, a, b):
    m = (ys >= a) & (ys <= b)
    return int(np.nonzero(m)[0][np.argmax(zf[m])])


def analyse(path, png=None, relief=None):
    S = load(path)
    Pm, Fm = S['SpiderSuit']; Pf, Ff = S['LensFrame']; Pl, Fl = S['Lens']
    Pa, Fa = comb((Pm, Fm), (Pf, Ff), (Pl, Fl))
    crown = float(Pm[(np.abs(Pm[:, 0]) < 0.02) & (Pm[:, 1] > 1.7)][:, 1].max())
    ys_m, zf_m, _ = front_profile(Pm, Fm)
    ys, zf, xa = front_profile(Pa, Fa)
    # chin underside: going down from the chin's front (y 1.585) the first row where the mask's front z falls below 60 mm
    j = int(np.argmin(np.abs(ys_m - 1.585)))
    while j > 0 and zf_m[j] > 0.060: j -= 1
    chin = float(ys_m[j])
    HH = crown - chin
    i_n = lmax(ys, zf, 1.610, 1.668)                 # nose tip
    i_b = lmax(ys, zf, 1.693, 1.735)                 # brow
    chord = np.interp(ys, [ys[i_n], ys[i_b]], [zf[i_n], zf[i_b]])
    seg = np.arange(i_n, i_b + 1)
    dip = chord[seg] - zf[seg]
    k = int(seg[np.argmax(dip)])
    T1 = float(dip.max())
    lens_top = float(Pl[:, 1].max()); lens_bot = float(Pl[:, 1].min()); rim_top = float(Pf[:, 1].max()); rim_bot = float(Pf[:, 1].min())
    z_top_rim = float(Pf[Pf[:, 1] > rim_bot + 0.75 * (rim_top - rim_bot)][:, 2].max())
    z_top_lens = float(Pl[Pl[:, 1] > lens_bot + 0.75 * (lens_top - lens_bot)][:, 2].max())
    z_rim_all = float(Pf[:, 2].max())
    z_brow = float(zf[i_b])
    i_c = int(np.argmin(np.abs(ys - chin)))
    ch2 = np.interp(ys, [ys[i_c], ys[i_b]], [zf[i_c], zf[i_b]])
    bump = float((zf - ch2)[i_c:i_b + 1].max())
    i_m = lmax(ys, zf, 1.601, 1.624); i_ch = lmax(ys, zf, 1.560, 1.598)
    lo, hi = sorted((i_ch, i_m))
    groove = float(min(zf[i_ch], zf[i_m]) - zf[lo:hi + 1].min())
    res = dict(head_height_mm=round(HH * 1e3, 1), crown_y=round(crown, 4), chin_y=round(chin, 4),
               brow=dict(y=round(float(ys[i_b]), 4), z_mm=round(z_brow * 1e3, 1)), nose_tip=dict(y=round(float(ys[i_n]), 4), z_mm=round(float(zf[i_n]) * 1e3, 1)),
               nasion=dict(y=round(float(ys[k]), 4), z_mm=round(float(zf[k]) * 1e3, 1)),
               T1_bridge_recess_mm=round(T1 * 1e3, 2), T1_pct_HH=round(100 * T1 / HH, 2),
               T2_brow_over_rim_top_mm=round((z_brow - z_top_rim) * 1e3, 2), T2_pct_HH=round(100 * (z_brow - z_top_rim) / HH, 2),
               T2_brow_over_lens_top_mm=round((z_brow - z_top_lens) * 1e3, 2),
               T2b_brow_over_every_rim_vertex_mm=round((z_brow - z_rim_all) * 1e3, 2), T2b_pct_HH=round(100 * (z_brow - z_rim_all) / HH, 2),
               lens_y=[round(lens_bot, 4), round(lens_top, 4)], rim_y=[round(rim_bot, 4), round(rim_top, 4)],
               T3_nose_bump_mm=round(bump * 1e3, 2), T3_nose_bump_pct_HH=round(100 * bump / HH, 2),
               mouth=dict(y=round(float(ys[i_m]), 4), z_mm=round(float(zf[i_m]) * 1e3, 1)), chin_front=dict(y=round(float(ys[i_ch]), 4), z_mm=round(float(zf[i_ch]) * 1e3, 1)),
               mouth_chin_groove_mm=round(groove * 1e3, 2),
               profile_mm={'%.3f' % y: round(float(zf[int(np.argmin(np.abs(ys - y)))]) * 1e3, 1) for y in np.arange(1.55, 1.77, 0.01)})
    if png:
        import cv2
        sc = 8.0
        y_lo, y_hi = 1.535, 1.79
        Hh = int((y_hi - y_lo) * 1e3 * sc); Ww = int(150 * sc)
        im = np.full((Hh, Ww, 3), 255, np.uint8)
        row = lambda y: int((y_hi - y) * 1e3 * sc); col = lambda z: int(z * 1e3 * sc)
        for name, arr, c in (('mask', zf_m, (200, 120, 0)), ('chord', chord, (200, 200, 0)), ('chin chord', ch2, (200, 0, 200)), ('all', zf, (0, 0, 0))):
            pts = np.array([[col(z), row(y)] for y, z in zip(ys, arr) if y_lo < y < y_hi], np.int32)
            cv2.polylines(im, [pts], False, c, 2 if name == 'all' else 1, cv2.LINE_AA)
        for y in (lens_bot, lens_top):
            cv2.line(im, (0, row(y)), (Ww, row(y)), (0, 140, 255), 1)
        for yy in np.arange(1.54, 1.79, 0.01):
            cv2.line(im, (0, row(yy)), (12, row(yy)), (120, 120, 120), 1); cv2.putText(im, '%.2f' % yy, (14, row(yy) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
        for key, (p_, c) in dict(brow=((ys[i_b], zf[i_b]), (0, 0, 255)), nose=((ys[i_n], zf[i_n]), (0, 160, 0)), nasion=((ys[k], zf[k]), (255, 0, 0))).items():
            cv2.circle(im, (col(p_[1]), row(p_[0])), 6, c, -1); cv2.putText(im, key, (col(p_[1]) + 8, row(p_[0]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
        cv2.imwrite(png, im)
    if relief:
        res['relief'] = relief_lines(Pm, Fm, Pf, Ff, Pl, Fl, relief)
    return res


def side_extent(P, F, yaw_deg, y_list):
    """Silhouette extent (min, max of the projected coordinate u = x cos(yaw) + z sin(yaw)) of the surface at the heights y_list: exact, by triangle slicing."""
    c, s_ = np.cos(np.radians(yaw_deg)), np.sin(np.radians(yaw_deg))
    T = P[F]
    tmin = T[:, :, 1].min(1); tmax = T[:, :, 1].max(1)
    out = []
    for y in y_list:
        m = (tmin <= y) & (tmax >= y)
        t = T[m]
        lo, hi = 9.0, -9.0
        for a, b in ((0, 1), (1, 2), (2, 0)):
            pa, pb = t[:, a], t[:, b]
            dy = pb[:, 1] - pa[:, 1]
            ok = (np.abs(dy) > 1e-12) & (((pa[:, 1] - y) * (pb[:, 1] - y)) <= 0)
            if not ok.any(): continue
            u = (y - pa[ok, 1]) / dy[ok]
            X = pa[ok, 0] + u * (pb[ok, 0] - pa[ok, 0]); Z = pa[ok, 2] + u * (pb[ok, 2] - pa[ok, 2])
            proj = X * c + Z * s_
            lo = min(lo, float(proj.min())); hi = max(hi, float(proj.max()))
        out.append((lo, hi))
    return np.array(out)


def persp_render(path, yaw_deg, dist=1.0, aim=1.64, fov_h=26.0, w=3840, h=2160, ids=True):
    """Painter's-algorithm id render of the head as the 4K head stills see it (perspective camera `dist` m from (0, aim, 0), horizontal FOV, yawed yaw_deg around the
    vertical axis): returns (id image: 0 background, 1 mask, 2 rim, 3 glass).  Triangles sorted far to near; ~1 s."""
    import cv2
    S = load(path)
    f = (w / 2) / np.tan(np.radians(fov_h / 2))
    th = np.radians(yaw_deg)
    fwd = -np.array([np.sin(th), 0.0, np.cos(th)])          # the camera looks toward the head
    cam = np.array([0.0, aim, 0.0]) - fwd * dist
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    img = np.zeros((h, w), np.uint8)
    tris = []
    for ident, name in ((1, 'SpiderSuit'), (2, 'LensFrame'), (3, 'Lens')):
        P, F = S[name]
        d = P - cam
        X = d @ right; Y = d @ up; Z = d @ fwd
        px = w / 2 + f * X / Z; py = h / 2 - f * Y / Z
        T = F
        cen = Z[T].mean(1)
        # backface cull: the triangle faces the camera when the cross product of its projected corners is positive (y down image coords)
        a_ = np.stack([px[T[:, 0]], py[T[:, 0]]], 1); b_ = np.stack([px[T[:, 1]], py[T[:, 1]]], 1); c_ = np.stack([px[T[:, 2]], py[T[:, 2]]], 1)
        area = (b_[:, 0] - a_[:, 0]) * (c_[:, 1] - a_[:, 1]) - (b_[:, 1] - a_[:, 1]) * (c_[:, 0] - a_[:, 0])
        inview = (np.maximum(np.maximum(a_[:, 0], b_[:, 0]), c_[:, 0]) > 0) & (np.minimum(np.minimum(a_[:, 0], b_[:, 0]), c_[:, 0]) < w) & (np.maximum(np.maximum(a_[:, 1], b_[:, 1]), c_[:, 1]) > 0) & (np.minimum(np.minimum(a_[:, 1], b_[:, 1]), c_[:, 1]) < h)
        for i in np.nonzero(inview)[0]:
            tris.append((cen[i], ident, a_[i], b_[i], c_[i], area[i]))
    tris.sort(key=lambda t: -t[0])
    for cz, ident, a_, b_, c_, ar in tris:
        pts = np.array([a_, b_, c_]).round().astype(np.int32)
        cv2.fillConvexPoly(img, pts, int(ident))
    return img


def persp_clearance(path, yaw_deg, **kw):
    """H6 on the mesh the way head_check_r13 measures it on the stills: the glass pixels' minimum distance (px, 4K) to the background of the head silhouette."""
    from scipy import ndimage as ndi
    im = persp_render(path, yaw_deg, **kw)
    sil = im > 0
    dsil = ndi.distance_transform_edt(sil)
    out = {}
    for name, ident in (('glass', 3), ('rim', 2)):
        m = im == ident
        out[name] = round(float(dsil[m].min()), 1) if m.any() else None
    return out


# ---------------------------------------------------------------------------------------------------- front relief shading (design aid for the cheek test)
def height_map(P, F, step=2.5e-4, x0=-0.10, x1=0.10, y0=1.54, y1=1.78):
    """Front-most z of the triangles on a regular (x, y) grid (the mask, lens and rim together)."""
    nx = int(round((x1 - x0) / step)); ny = int(round((y1 - y0) / step))
    Z = np.full((ny, nx), np.nan, np.float32)
    tri = P[F]
    keep = (tri[:, :, 1].max(1) > y0) & (tri[:, :, 1].min(1) < y1) & (np.abs(tri[:, :, 0]).min(1) < x1)
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); keep &= fn[:, 2] > 0
    for t in tri[keep]:
        px = (t[:, 0] - x0) / step; py = (t[:, 1] - y0) / step
        xa, xb = max(int(np.floor(px.min())), 0), min(int(np.ceil(px.max())), nx - 1)
        ya, yb = max(int(np.floor(py.min())), 0), min(int(np.ceil(py.max())), ny - 1)
        if xb < xa or yb < ya: continue
        gx, gy = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
        a, b, c = np.stack([px, py], 1)
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12: continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.01) & (w1 >= -0.01) & (w2 >= -0.01)
        z = w0 * t[0, 2] + w1 * t[1, 2] + w2 * t[2, 2]
        sl = (slice(ya, yb + 1), slice(xa, xb + 1))
        cur = Z[sl]
        Z[sl] = np.where(m & (np.isnan(cur) | (z > cur)), z, cur)
    return Z, (x0, y0, step)


def relief_lines(Pm, Fm, Pf, Ff, Pl, Fl, out_png):
    """Shade the front height map with a key light from the upper left front (like the stage key) and read horizontal luma lines under the lenses.
    Returns the number of >= 8-luma-prominence extrema of the lines (a CPU proxy for the 4K-still test: the real number is measured on the stills)."""
    import cv2
    from scipy import ndimage as ndi
    from scipy.signal import find_peaks
    Z, (x0, y0, step) = height_map(*comb((Pm, Fm), (Pf, Ff), (Pl, Fl)))
    Zf = np.where(np.isnan(Z), 0.0, Z).astype(np.float64)
    Zs = ndi.gaussian_filter(Zf, 1.0)
    gy, gx = np.gradient(Zs, step)
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.45, 0.55, 0.70]); L /= np.linalg.norm(L)
    lam = np.clip(n @ L, 0, 1)
    fill = np.clip(n @ np.array([0.5, 0.2, 0.85]), 0, 1) * 0.25
    lum = 255 * np.clip(0.12 + 0.75 * lam + fill, 0, 1)
    lum = np.where(np.isnan(Z), 0, lum)
    cv2.imwrite(out_png, cv2.resize(np.flipud(lum).astype(np.uint8), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
    lens_bot = float(Pf[:, 1].min())
    rows = {}
    for dy in (-0.004, 0.0, 0.006, 0.012, 0.018, 0.024):
        y = lens_bot + dy
        r = int(round((y - y0) / step))
        line = ndi.uniform_filter1d(lum[r - 2:r + 3].mean(0), 9, mode='nearest')
        xs = (np.arange(len(line)) * step + x0)
        sel = np.abs(xs) < 0.065
        pk, _ = find_peaks(line[sel], prominence=8.0); vl, _ = find_peaks(-line[sel], prominence=8.0)
        rows['%+.0f mm' % (dy * 1e3)] = dict(extrema=int(len(pk) + len(vl)), swing=round(float(line[sel].max() - line[sel].min()), 1))
    return rows


if __name__ == '__main__':
    a = sys.argv
    r = analyse(a[1], a[a.index('--png') + 1] if '--png' in a else None, a[a.index('--relief') + 1] if '--relief' in a else None)
    if '--brief' in a: r.pop('profile_mm', None)
    if '--h6' in a:
        r['H6_clearance_px'] = {str(yw): persp_clearance(a[1], yw) for yw in (12.0, -12.0)}
    print(json.dumps(r, indent=1))
    if '--json' in a: json.dump(r, open(a[a.index('--json') + 1], 'w'), indent=1)
