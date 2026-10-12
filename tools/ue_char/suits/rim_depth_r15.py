#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 15 pass test of the critic r14 line "the lens rim sits 18 px proud of the brow (2273 against 2255), so the brow does not overhang the lens", measured on the 4K
`headside` stills of the REAL game (lossless PNG originals):

  R1 rim depth   the front-most pixel of the lens RIM (in the face direction, over every row of the rim) lies >= 1 % of the head height (crown to chin; >= 16 px at 1590 px)
                 BEHIND the front-most pixel of the brow (the front-most silhouette pixel of the band above the lens, head_check_r14.py's definition).

The rim is segmented from the glass: the glass mask (lens-colour hue, as head_check_r14) is dilated by RIM_MAX px; the rim is the connected band of that ring (inside the head
silhouette, outside the glass) whose colour is NOT the fabric colour (median of the annulus 90 - 160 px from the glass) and not the glass: a metallic rim is low in saturation and differs
from the fabric by >= 22 in max-channel distance or >= 18 luma.  The overlay (--dump) draws the glass edge (yellow), the rim mask (cyan), the brow x (red line) and the rim front x (green line).

  python3 rim_depth_r15.py all <stills_dir> <out.json> [overlay_dir]
  python3 rim_depth_r15.py one <headside_4k.png> <suit> [--dump out.jpg]
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import head_check_r13 as H13  # noqa: E402
Image.MAX_IMAGE_PIXELS = None
SUITS = H13.SUITS
RIM_MAX = 34          # px: the rim band is <= 3.4 mm * 6650 px/m = 23 px wide face-on; the profile view foreshortens it, a pale glint can reach further
GATE_PCT = 1.0        # % of the head height the rim must lie behind the brow


def measure(path, suit, dump=None, cam_dist=1.25, aim_y=1.665, fov=26.0):
    im = H13.load(path); sil = H13.silhouette(im)
    h, w, _ = im.shape
    f = 1920.0 / np.tan(np.radians(fov / 2)) / cam_dist
    row_of = lambda y: int(round(1080 - (y - aim_y) * f))
    crown = int(np.nonzero(sil.any(1))[0].min()); chin = row_of(1.5475); HH = float(chin - crown)
    cx = int(np.nonzero(sil[row_of(1.74)])[0].mean())
    rr = np.nonzero(sil[row_of(1.645)])[0]
    sgn = 1 if (rr.max() - cx) > (cx - rr.min()) else -1
    rows = np.arange(row_of(1.745), row_of(1.60))
    fx = np.array([(np.nonzero(sil[r])[0].max() if sgn > 0 else np.nonzero(sil[r])[0].min()) for r in rows], np.float64)
    fx = ndi.uniform_filter1d(fx, 3, mode='nearest')
    at = lambda r: int(r - rows[0])
    seg_b = fx[at(row_of(1.735)):at(row_of(1.693)) + 1] * sgn
    i_b = at(row_of(1.735)) + int(np.argmax(seg_b)); xb = float(fx[i_b])
    # glass
    acc = H13.lens_colour(suit); ha, sa, va = H13.rgb2hsv(acc)
    x = im / 255.0; mx = x.max(2); mn = x.min(2); v = mx; s_ = (mx - mn) / (mx + 1e-6)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]; dl = mx - mn + 1e-9
    hh = np.where(mx == r, ((g - b) / dl) % 6, np.where(mx == g, (b - r) / dl + 2, (r - g) / dl + 4)) / 6.0
    m = (H13.hue_dist(hh, ha) < 0.045) & (s_ > max(0.18, 0.45 * sa)) & (v > 0.42) & ndi.binary_erosion(sil, iterations=3)
    m = ndi.binary_closing(ndi.binary_opening(m, iterations=2), iterations=6)
    lab, n = ndi.label(m)
    out = dict(suit=suit, file=os.path.basename(path), face_dir=int(sgn), head_h_px=int(HH), brow_front_x=int(xb), brow_row=int(rows[i_b]))
    if n == 0:
        out.update(ok=False, why='no glass'); return out
    areas = ndi.sum(m, lab, range(1, n + 1)); glass = ndi.binary_fill_holes(lab == (1 + int(np.argmax(areas))))
    if glass.sum() < 500:
        out.update(ok=False, why='glass too small'); return out
    gy, gx = np.nonzero(glass)
    dist = ndi.distance_transform_edt(~glass)
    ring = (dist > 0) & (dist <= RIM_MAX) & sil
    fab = (dist > 90) & (dist <= 160) & sil & ~glass
    # the fabric colour: median of the annulus; a ray through the rim in the profile lands on the fabric within ~ 60 px of the glass, so 90 - 160 px is clean fabric
    if fab.sum() < 500:
        out.update(ok=False, why='no fabric annulus'); return out
    fc = np.median(im[fab], axis=0)
    fl = float(H13.luma_of(fc[None, None, :])[0, 0])
    Lm = H13.luma_of(im)
    dmax = np.abs(im - fc[None, None, :]).max(2)
    sat = (im.max(2) - im.min(2)) / (im.max(2) + 1.0)
    glasslike = (H13.hue_dist(hh, ha) < 0.045) & (s_ > 0.25)
    fsat = float(np.median(sat[fab]))
    cand = ring & ((dmax >= 22.0) | (np.abs(Lm - fl) >= 18.0)) & ~glasslike
    if fsat > 0.30: cand &= sat < 0.5 * fsat + 0.12            # a saturated fabric: the metal rim is the grey part
    # the fabric's own relief / tone variation inside the ring: keep the band connected to the glass edge within 4 px
    cand = ndi.binary_opening(cand, structure=np.ones((3, 3)), iterations=3)      # the rim is a band >= 7 px wide: shaded fabric specks and glints thinner than that are not rim
    lab2, n2 = ndi.label(cand)
    keep = np.zeros_like(cand)
    if n2:
        touch = np.unique(lab2[(dist <= 5) & cand]); touch = touch[touch > 0]
        for t in touch: keep |= lab2 == t
    # the rim is one closed band: close small gaps (specular breaks), fill, remove what lies beyond RIM_MAX
    rim = ndi.binary_closing(keep, iterations=3) & ring
    if rim.sum() < 300:
        out.update(ok=False, why='no rim pixels'); return out
    ry, rx = np.nonzero(rim)
    xr = float(rx.max() if sgn > 0 else rx.min())
    k = int(np.argmax(rx * sgn)); rim_row = int(ry[k])
    # the rim's front-most pixel BELOW the brow band only (every rim row is below the brow anyway: the rim is part of the eye frame)
    gap = (xb - xr) * sgn                                    # + = rim BEHIND the brow
    out.update(ok=True, rim_front_x=int(xr), rim_front_row=rim_row, glass_front_x=int(gx.max() if sgn > 0 else gx.min()),
               rim_px_area=int(rim.sum()), fabric_sat=round(fsat, 2), fabric_rgb=[int(c) for c in fc],
               rim_behind_brow_px=round(float(gap), 1), rim_behind_brow_pct_head_h=round(100 * gap / HH, 2),
               R1_rim_ge_1pct_behind_brow=bool(100 * gap / HH >= GATE_PCT))
    if dump:
        pim = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)); a = np.asarray(pim).copy()
        a[glass ^ ndi.binary_erosion(glass, iterations=2)] = (255, 255, 0)
        a[rim ^ ndi.binary_erosion(rim, iterations=1)] = (0, 255, 255)
        pim = Image.fromarray(a); d = ImageDraw.Draw(pim)
        d.line([(xb, rows[i_b] - 400), (xb, rows[i_b] + 400)], fill=(255, 0, 0), width=3)
        d.line([(xr, rim_row - 400), (xr, rim_row + 400)], fill=(0, 255, 0), width=3)
        x0 = int(min(xb, xr)) - (700 if sgn > 0 else -100); y0 = int(rows[i_b]) - 300
        pim.crop((max(x0, 0), max(y0, 0), max(x0, 0) + 800, max(y0, 0) + 800)).save(dump, quality=85)
    return out


def run_all(sd, out_json, ov=None):
    res = {}
    for s in SUITS:
        sid = s['id']
        p = os.path.join(sd, 'skin_%s_headside_4k.png' % sid)
        if not os.path.exists(p): p = p.replace('.png', '.jpg')
        if not os.path.exists(p): continue
        if ov: os.makedirs(ov, exist_ok=True)
        res[sid] = measure(p, sid, os.path.join(ov, 'rim_%s.jpg' % sid) if ov else None)
        r = res[sid]
        print(sid, r.get('rim_behind_brow_px'), r.get('rim_behind_brow_pct_head_h'), r.get('R1_rim_ge_1pct_behind_brow'), r.get('why', ''))
    json.dump(res, open(out_json, 'w'), indent=1)
    return res


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'all': run_all(a[2], a[3], a[4] if len(a) > 4 else None)
    else: print(json.dumps(measure(a[2], a[3], a[a.index('--dump') + 1] if '--dump' in a else None), indent=1))
