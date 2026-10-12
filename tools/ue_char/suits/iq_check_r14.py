#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14 image-quality checks of the four defects the round-13 critic named (IQ 5), measured on the 4K stills of the REAL game (PNG originals of this round,
the committed round-13 JPEGs as the baseline) + side-by-side crops for the eye (a number never replaces looking at the crop).

  Q1  Ash sash ends ("raw end (1410-1440, 700-1050)"): the lime panel's end edge: straightness (rms deviation of the end line from its fit, px) and the number of light stitch dashes
      in a 70 px strip beyond the end (a finished end has the border cord + 2 stitch rows + an accent pipe)
  Q2  Ash armpit stitches ("zigzag (1120-1200, 1530-1600)"): light stitch-dash blobs in the armpit box (1050-1300 x 1400-1700): count, and the spread of their orientations
      (a zigzag = dashes at several angles); the box (1120-1200 x 1530-1600) itself
  Q3  Sage trapezius ("torn groove, head34"): dark thin-line pixels (local luma 12 px high-pass < -10) in the trapezius box (770-1040 x 1630-1830): fraction + the longest connected line
  Q4  Cinder shoulders ("faceted"): the left shoulder's silhouette contour (chest still), simplified with epsilon 4 px: vertices per 1000 px of arc, the longest straight segment

  python3 iq_check_r14.py <stills dir r14 (png or jpg)> <stills dir r13 (jpg)> <crop out dir>  -> JSON on stdout
"""
import sys, os, json
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import head_check_r13 as H13  # noqa: E402
Image.MAX_IMAGE_PIXELS = None


def find(d, name):
    for ext in ('png', 'jpg'):
        p = os.path.join(d, name + '.' + ext)
        if os.path.exists(p): return p
    return None


def luma(im): return 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]


def sat(im):
    mx = im.max(2); mn = im.min(2); return (mx - mn) / (mx + 1e-6)


def q1_sash_end(im, accent=(168, 224, 90)):
    d = np.linalg.norm(im - np.array(accent, np.float32), axis=2)
    m = (d < 55) & (luma(im) > 110)
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m)
    if n == 0: return dict(ok=False)
    areas = ndi.sum(m, lab, range(1, n + 1)); big = lab == (1 + int(np.argmax(areas)))
    ys, xs = np.nonzero(big)
    x0 = xs.min(); end_rows = []
    # the end = the left-most 80 px of the component: per row the left-most pixel (rows with the component in the end zone)
    zone = big[:, x0:x0 + 80]
    rows = np.nonzero(zone.any(1))[0]
    lx = np.array([np.nonzero(zone[r])[0].min() + x0 for r in rows], np.float64)
    # robust line fit of the end (x as a function of y), exclude rows where the panel's slanted long edge takes over (x far from the median)
    med = np.median(lx); keep = np.abs(lx - med) < 25
    if keep.sum() < 10: return dict(ok=False, rows=int(len(rows)))
    A = np.stack([rows[keep], np.ones(keep.sum())], 1)
    coef, *_ = np.linalg.lstsq(A, lx[keep], rcond=None)
    res = lx[keep] - A @ coef
    # stitch dashes beyond the end (left of it): light, low-saturation blobs in a strip 6 - 76 px left of the end line
    L = luma(im); S = sat(im)
    lt = ((L > 130) & (S < 0.30))
    cnt = 0
    r0, r1 = int(rows[keep].min()), int(rows[keep].max())
    strip = np.zeros_like(lt)
    for r in range(r0, r1 + 1, 1):
        x_end = int(coef[0] * r + coef[1])
        strip[r, max(x_end - 76, 0):max(x_end - 6, 0)] = True
    lab2, n2 = ndi.label(lt & strip)
    areas2 = ndi.sum(lt & strip, lab2, range(1, n2 + 1)) if n2 else []
    cnt = int(sum(1 for a in areas2 if 12 <= a <= 600))
    return dict(ok=True, panel_x_min=int(x0), end_rows=[r0, r1], end_rms_px=round(float(np.sqrt((res ** 2).mean())), 2), end_max_dev_px=round(float(np.abs(res).max()), 1),
                end_slope_px_per_row=round(float(coef[0]), 3), stitch_dashes_beyond_end=cnt)


def q2_armpit(im, box=(1050, 1400, 1300, 1700), probe=(1120, 1530, 1200, 1600)):
    x0, y0, x1, y1 = box
    Lf = luma(im).astype(np.float32); L = Lf[y0:y1, x0:x1]; S = sat(im)[y0:y1, x0:x1]
    hp = (Lf - ndi.gaussian_filter(Lf, 9))[y0:y1, x0:x1]
    m = (hp > 18) & (L > 50) & (S < 0.35)              # the dashes are light grey on a near-black wedge: local contrast, not an absolute luma
    m = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(m)
    blobs = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if not (10 <= len(ys) <= 900): continue
        c = np.cov(np.stack([xs, ys])) if len(ys) > 3 else None
        if c is None: continue
        w, v = np.linalg.eigh(c); ang = float(np.degrees(np.arctan2(v[1, 1], v[0, 1])) % 180)
        el = float(np.sqrt(max(w[1], 1e-6) / max(w[0], 1e-6)))
        blobs.append((float(xs.mean() + x0), float(ys.mean() + y0), len(ys), ang, el))
    dashes = [b for b in blobs if b[4] > 1.8]                 # elongated blobs = stitch dashes
    angs = np.array([b[3] for b in dashes]);
    # circular spread of the orientations (axial data, period 180)
    spread = float(np.degrees(np.sqrt(-2 * np.log(max(np.hypot(np.cos(np.radians(2 * angs)).mean(), np.sin(np.radians(2 * angs)).mean()), 1e-6))) / 2)) if len(angs) > 1 else 0.0
    px0, py0, px1, py1 = probe
    inprobe = [b for b in dashes if px0 <= b[0] <= px1 and py0 <= b[1] <= py1]
    return dict(box=list(box), dashes_in_box=len(dashes), orientation_spread_deg=round(spread, 1), dashes_in_critic_box=len(inprobe), dash_angles=[round(float(a)) for a in angs[:24]])


def q3_trapezius(im, box=(770, 1630, 1040, 1830)):
    x0, y0, x1, y1 = box
    L = luma(im).astype(np.float32)
    hp = L - ndi.gaussian_filter(L, 12)
    dark = (hp < -10)[y0:y1, x0:x1]
    dark = ndi.binary_opening(dark, structure=np.ones((2, 2)))
    lab, n = ndi.label(dark)
    longest = 0
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i); ext = max(ys.max() - ys.min(), xs.max() - xs.min()) + 1
        longest = max(longest, int(ext))
    return dict(box=list(box), dark_line_fraction_pct=round(100.0 * float(dark.mean()), 3), longest_dark_line_px=longest, components=int(n))


def q4_shoulder(im):
    sil = H13.silhouette(im, margin=300, thr=14.0).astype(np.uint8)
    cnts, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)[:, 0, :]
    # the left shoulder: the contour points with x < 1100 and 150 < y < 1000
    sel = (c[:, 0] < 1100) & (c[:, 1] > 150) & (c[:, 1] < 1000) & (c[:, 0] > 5)
    pts = c[sel]
    if len(pts) < 50: return dict(ok=False)
    # order is the contour order: take the longest run of consecutive selected points
    idx = np.nonzero(sel)[0]
    runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1); run = max(runs, key=len)
    pts = c[run].astype(np.float32)
    arc = float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
    ap = cv2.approxPolyDP(pts.reshape(-1, 1, 2), 4.0, False)[:, 0, :]
    seg = np.linalg.norm(np.diff(ap, axis=0), axis=1)
    turn = []
    for k in range(1, len(ap) - 1):
        a = ap[k] - ap[k - 1]; b = ap[k + 1] - ap[k]
        turn.append(abs(np.degrees(np.arctan2(a[0] * b[1] - a[1] * b[0], a @ b))))
    return dict(ok=True, arc_px=round(arc), vertices_eps4=int(len(ap)), vertices_per_1000px=round(1000.0 * len(ap) / max(arc, 1), 2), longest_segment_px=round(float(seg.max()), 1),
                median_segment_px=round(float(np.median(seg)), 1), max_turn_deg=round(float(max(turn)), 1) if turn else 0.0)


def crop_pair(a, b, box, out, scale=1.0, labels=('round 13', 'round 14')):
    x0, y0, x1, y1 = box
    ca = a[y0:y1, x0:x1]; cb = b[y0:y1, x0:x1]
    im = np.concatenate([ca, np.full((ca.shape[0], 8, 3), 255, np.float32), cb], 1)
    im = cv2.resize(np.clip(im, 0, 255).astype(np.uint8), None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    cv2.putText(im, labels[0], (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2); cv2.putText(im, labels[1], (int(ca.shape[1] * scale) + 18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    Image.fromarray(im).save(out, quality=88)


def main():
    cur, base, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    res = {}
    def L_(name):
        p = find(cur, name); q = find(base, name)
        return (H13.load(p) if p else None), (H13.load(q) if q else None)
    # Q1 / Q2: Ash chest
    a14, a13 = L_('skin_ash_chest_4k')
    if a14 is not None and a13 is not None:
        res['Q1_ash_sash_end'] = dict(r13=q1_sash_end(a13), r14=q1_sash_end(a14))
        res['Q2_ash_armpit'] = dict(r13=q2_armpit(a13), r14=q2_armpit(a14))
        crop_pair(a13, a14, (1000, 500, 1700, 1100), os.path.join(out, 'q1_ash_sash_end.jpg'), 1.0)
        crop_pair(a13, a14, (1000, 1380, 1360, 1720), os.path.join(out, 'q2_ash_armpit.jpg'), 2.0)
    s14, s13 = L_('skin_sage_head34_4k')
    if s14 is not None and s13 is not None:
        res['Q3_sage_trapezius'] = dict(r13=q3_trapezius(s13), r14=q3_trapezius(s14))
        crop_pair(s13, s14, (600, 1550, 1400, 2050), os.path.join(out, 'q3_sage_trapezius.jpg'), 1.0)
    c14, c13 = L_('skin_cinder_chest_4k')
    if c14 is not None and c13 is not None:
        res['Q4_cinder_shoulder'] = dict(r13=q4_shoulder(c13), r14=q4_shoulder(c14))
        crop_pair(c13, c14, (500, 300, 1600, 1300), os.path.join(out, 'q4_cinder_shoulder.jpg'), 0.8)
    # the other suits' sash ends for the eye (contact crops, no numbers): tessera, verdant, plum, saffron
    for sid in ('tessera', 'verdant', 'plum', 'saffron', 'glacier'):
        x14, x13 = L_('skin_%s_chest_4k' % sid)
        if x14 is not None and x13 is not None: crop_pair(x13, x14, (700, 300, 2900, 1900), os.path.join(out, 'chest_%s.jpg' % sid), 0.45)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
