#!/usr/bin/env python3
"""Tree-crown detail check (round-01 critic's biggest gap; round-02 PASS test), CPU only.
  1. crown crops: high-pass SD = std of (Y - GaussianBlur(Y, sigma 3)) on hand-picked 150 x 150 crops of pure crown (luma Y 0..255); boxes are pixel boxes on the 3840 x 2160 stills,
     listed in docs/night1/terrain/round-NN/crops.json  {"crowns": {"p1_south.jpg": [[x, y], ...]}, "reference": {"<ref image path>": [[x, y], ...]}}.  PASS: every crop >= 9.
  2. flat-shaded hull faces: foliage-coloured pixels whose local luma variation is almost zero form flat patches (what a smooth-shaded low-poly hull looks like); a patch's width
     is the diameter of its largest inscribed circle (distance transform). PASS: no patch wider than 40 px in p1_south / p10_lawn_eye.
  3. (r03) crown silhouette: the longest straight segment on the foliage-mask boundary where it meets the sky (a hull facet edge reads as a straight line against the sky).
     The foliage / sky masks are cleaned (3 px opening / closing), the boundary is traced as contours, only contour points with sky within 3 px are kept, every run of them is
     simplified by Douglas-Peucker with a 1.5 px tolerance and the longest resulting segment is reported (image borders excluded). Segments within 4 deg of horizontal / vertical
     are building / lamp-post edges (the cameras have no roll); a segment whose foliage-side strip (5 px in) is dark (median luma < 55: lamp heads, trunks, bare limbs),
     thin (median mask thickness < 3.5 px: twigs) or outside the canopy hue range 32-170 deg (brick / facades) is not a crown edge either. All set-aside segments are listed with
     the reason, never scored. PASS: <= 40 px in p10_lawn_eye.
  r03: the flat-patch test also counts dark pockets (luma < 40, any hue) that touch foliage (within 15 px), so a crushed black shadow pocket cannot hide from it.
usage: crown_stats.py <stills dir> <crops.json> <out.json> [--flat image.jpg ...] [--silhouette image.jpg ...] [--preview preview.png]"""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, uniform_filter, distance_transform_edt, label, binary_opening, binary_closing, binary_dilation

CROP = 150
def luma(a): return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)

def hp_sd(Y, x, y, size=CROP, sigma=3.0):
    # blur the whole image once per call site (cached by the caller); here a local window with margin to avoid edge effects
    m = int(sigma * 4)
    y0, x0 = max(0, y - m), max(0, x - m); y1, x1 = min(Y.shape[0], y + size + m), min(Y.shape[1], x + size + m)
    blur = gaussian_filter(Y[y0:y1, x0:x1], sigma)
    hp = (Y[y0:y1, x0:x1] - blur)[y - y0:y - y0 + size, x - x0:x - x0 + size]
    return float(hp.std())

def crop_stats(path, boxes):
    im = load(path); Y = luma(im); out = []
    for x, y in boxes:
        c = im[y:y + CROP, x:x + CROP]
        r, g, b = c[..., 0].mean(), c[..., 1].mean(), c[..., 2].mean()
        mx = c.max(axis=2); mn = c.min(axis=2); sat = float(np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0).mean())   # r05: mean HSV saturation of the crop (target median >= 0.65)
        out.append({'box_xywh': [x, y, CROP, CROP], 'hp_sd': round(hp_sd(Y, x, y), 2), 'mean_luma': round(float(Y[y:y + CROP, x:x + CROP].mean()), 1), 'mean_hsv_sat': round(sat, 3), 'rgb_mean': [round(float(v), 1) for v in (r, g, b)]})
    return out

def flat_faces(path, var_thr=1.4, min_w=40):
    """flat foliage patches: local luma std (7 x 7) <= var_thr on foliage-coloured pixels; opened by 3 px so single smooth pixels do not count"""
    im = load(path); Y = luma(im); r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mx = im.max(axis=2); mn = im.min(axis=2); sat = (mx - mn) / np.maximum(mx, 1.0)
    # olive / green / yellow-green foliage, not sky / buildings / road; the mown lawn (vivid green, G/R > 1.15, smooth by design) is excluded: it is not a hull face
    foliage = (g >= 0.92 * r) & (g > 1.08 * b) & (sat > 0.35) & (Y > 20) & (Y < 235) & (g <= 1.15 * r)
    dark = (Y < 40) & binary_dilation(foliage, iterations=15)          # r03: crushed shadow pockets inside / next to the canopy count too (any hue)
    cand = foliage | dark
    m1 = uniform_filter(Y, 7); m2 = uniform_filter(Y * Y, 7); lstd = np.sqrt(np.maximum(m2 - m1 * m1, 0))
    flat = cand & (lstd <= var_thr)
    flat = binary_opening(flat, iterations=3)
    dt = distance_transform_edt(flat)
    lab, n = label(flat)
    wide = []
    if n:
        mxd = np.zeros(n + 1); np.maximum.at(mxd, lab.ravel(), dt.ravel())
        for i in range(1, n + 1):
            w = 2 * mxd[i]
            if w > min_w:
                ys, xs = np.nonzero(lab == i); wide.append({'width_px': round(float(w), 1), 'area_px': int(len(ys)), 'centre_xy': [int(xs.mean()), int(ys.mean())]})
    wide.sort(key=lambda d: -d['width_px'])
    return {'image': os.path.basename(path), 'foliage_pct': round(100 * float(foliage.mean()), 1), 'dark_pocket_pct': round(100 * float(dark.mean()), 2), 'flat_pct_of_foliage': round(100 * float(flat.sum()) / max(1, float(foliage.sum())), 2),
            'max_flat_width_px': round(float(2 * dt.max()), 1), 'patches_wider_than_%d_px' % min_w: len(wide), 'widest': wide[:6]}

def foliage_sky_masks(im):
    Y = luma(im); r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mx = im.max(axis=2); mn = im.min(axis=2); sat = (mx - mn) / np.maximum(mx, 1.0)
    m1 = uniform_filter(Y, 7); m2 = uniform_filter(Y * Y, 7); lstd = np.sqrt(np.maximum(m2 - m1 * m1, 0))
    # sky (incl. the warm golden-hour haze and clouds): bright, weakly saturated, smooth, and connected to the top edge of the frame
    sky0 = (Y > 120) & (sat < 0.36) & (lstd < 3.5)
    lab, n = label(binary_closing(sky0, iterations=1))
    top = set(np.unique(lab[0:6, :])) - {0}
    sky = np.isin(lab, list(top)) if top else np.zeros_like(sky0)
    # crown side of the skyline: everything that is not sky and is coloured like foliage (yellow-green .. olive .. autumn brown); buildings pass the colour test too,
    # their axis-aligned edges are set aside in silhouette()
    d = np.maximum(mx - mn, 1e-3)
    hue = np.where(mx == r, (60 * (g - b) / d) % 360, np.where(mx == g, 60 * (b - r) / d + 120, 60 * (r - g) / d + 240))
    foliage = ~sky & (sat > 0.18) & (hue > 15) & (hue < 170)
    foliage = binary_closing(binary_opening(foliage, iterations=1), iterations=1)
    return foliage, sky

def silhouette(path, tol=1.5, near_sky=3, min_report=40, axis_tol=4.0):
    """longest straight run on the foliage boundary against the sky (see the module docstring)"""
    import cv2
    im = load(path); H, W = im.shape[:2]
    foliage, sky = foliage_sky_masks(im)
    skyd = binary_dilation(sky, iterations=near_sky)
    cs, _ = cv2.findContours(foliage.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    best = []; axial = []; npts = 0
    Y = luma(im); thick = distance_transform_edt(foliage)
    mx = im.max(axis=2); mn = im.min(axis=2); d_ = np.maximum(mx - mn, 1e-3); r_, g_, b_ = im[..., 0], im[..., 1], im[..., 2]
    hue = np.where(mx == r_, (60 * (g_ - b_) / d_) % 360, np.where(mx == g_, 60 * (b_ - r_) / d_ + 120, 60 * (r_ - g_) / d_ + 240))
    def strip_class(a, b):
        """what lies on the foliage side of a boundary segment: 'crown' (leaf-coloured, lit, thicker than a twig) or why not (dark = lamp head / trunk / bare limb,
        thin = a twig or limb under 7 px, hue = brick / facade colours outside the canopy's yellow-olive-green range)"""
        n = max(2, int(np.hypot(*(b - a).astype(float)) // 2)); t = np.linspace(0.0, 1.0, n)
        P = a[None, :] + (b - a)[None, :] * t[:, None]
        nx, ny = -(b - a)[1], (b - a)[0]; nl = max(1e-6, float(np.hypot(nx, ny))); nx, ny = nx / nl, ny / nl
        best_side = None
        for sgn in (1.0, -1.0):   # pick the side of the segment that is foliage
            xs = np.clip((P[:, 0] + sgn * nx * 5).round().astype(int), 0, W - 1); ys = np.clip((P[:, 1] + sgn * ny * 5).round().astype(int), 0, H - 1)
            f = foliage[ys, xs].mean()
            if best_side is None or f > best_side[0]: best_side = (f, xs, ys)
        f, xs, ys = best_side
        if np.median(Y[ys, xs]) < 55: return 'dark'
        if np.median(thick[ys, xs]) < 3.5: return 'thin'
        hh = np.median(hue[ys, xs])
        if hh < 32 or hh > 170: return 'hue'
        return 'crown'
    for c in cs:
        c = c[:, 0, :]
        if len(c) < 20: continue
        ok = skyd[c[:, 1], c[:, 0]] & (c[:, 0] > 2) & (c[:, 0] < W - 3) & (c[:, 1] > 2) & (c[:, 1] < H - 3)
        npts += int(ok.sum())
        # runs of consecutive sky-facing contour points (the contour is closed: rotate so a run does not wrap)
        if ok.all(): runs = [c]
        else:
            k = int(np.argmin(ok)); c2 = np.roll(c, -k, axis=0); o2 = np.roll(ok, -k)
            runs, cur = [], []
            for pnt, f in zip(c2, o2):
                if f: cur.append(pnt)
                elif cur: runs.append(np.array(cur)); cur = []
            if cur: runs.append(np.array(cur))
        for run in runs:
            if len(run) < 10: continue
            ap = cv2.approxPolyDP(run.reshape(-1, 1, 2).astype(np.int32), tol, False)[:, 0, :]
            for a, b in zip(ap[:-1], ap[1:]):
                dx, dy = (b - a).astype(float); L = float(np.hypot(dx, dy))
                if L <= 0: continue
                ang = abs(np.degrees(np.arctan2(dy, dx))) % 90.0
                axis = min(ang, 90.0 - ang) <= axis_tol           # building verticals / roof lines / lamp posts (the cameras have no roll): reported apart
                why = 'axis-aligned' if axis else strip_class(a, b)
                rec = (L, [int(a[0]), int(a[1])], [int(b[0]), int(b[1])], why)
                (best if why == 'crown' else axial).append(rec)
    best.sort(key=lambda t: -t[0]); axial.sort(key=lambda t: -t[0])
    return {'image': os.path.basename(path), 'sky_pct': round(100 * float(sky.mean()), 1), 'foliage_pct': round(100 * float(foliage.mean()), 1), 'sky_boundary_points': npts,
            'longest_straight_px': round(best[0][0], 1) if best else 0.0, 'segments_longer_than_%d_px' % min_report: sum(1 for t in best if t[0] > min_report),
            'longest': [{'len_px': round(t[0], 1), 'from': t[1], 'to': t[2]} for t in best[:8]],
            'set_aside': [{'len_px': round(t[0], 1), 'from': t[1], 'to': t[2], 'why': t[3]} for t in axial[:8]]}

def main():
    args = sys.argv[1:]
    d, cj, out = args[:3]; rest = args[3:]
    flat_imgs, sil_imgs, preview, mode = [], [], None, None
    for a in rest:
        if a == '--flat': mode = 'flat'
        elif a == '--silhouette': mode = 'sil'
        elif a == '--preview': mode = 'preview'
        elif mode == 'preview': preview = a
        elif mode == 'sil': sil_imgs.append(a)
        else: flat_imgs.append(a)
    C = json.load(open(cj)); res = {'crowns': [], 'reference': [], 'flat': []}
    for f, boxes in C.get('crowns', {}).items():
        p = os.path.join(d, f)
        if not os.path.exists(p): continue
        for c in crop_stats(p, boxes): c['image'] = f; res['crowns'].append(c)
    for p, boxes in C.get('reference', {}).items():
        if not os.path.exists(p): continue
        for c in crop_stats(p, boxes): c['image'] = os.path.basename(p); res['reference'].append(c)
    for p in flat_imgs:
        pp = p if os.path.exists(p) else os.path.join(d, p)
        if os.path.exists(pp): res['flat'].append(flat_faces(pp))
    res['silhouette'] = []
    for p in sil_imgs:
        pp = p if os.path.exists(p) else os.path.join(d, p)
        if os.path.exists(pp): res['silhouette'].append(silhouette(pp))
    sds = [c['hp_sd'] for c in res['crowns']]
    p1 = [f for f in res['flat'] if f['image'] in ('p1_south.jpg', 'p10_lawn_eye.jpg')]
    res['summary'] = {'crown_crops': len(sds), 'min_hp_sd': min(sds) if sds else None, 'median_hp_sd': round(float(np.median(sds)), 2) if sds else None, 'max_hp_sd': max(sds) if sds else None,
                      'pass_crown_sd_ge_9': bool(sds) and min(sds) >= 9.0,
                      'median_hsv_sat': round(float(np.median([c['mean_hsv_sat'] for c in res['crowns']])), 3) if sds else None,   # r05 targets: all >= 9, median sd >= 12, median sat >= 0.65
                      'pass_r05_crowns': bool(sds) and min(sds) >= 9.0 and float(np.median(sds)) >= 12.0 and float(np.median([c['mean_hsv_sat'] for c in res['crowns']])) >= 0.65,
                      'reference_hp_sd': [c['hp_sd'] for c in res['reference']],
                      'max_flat_width_px': {f['image']: f['max_flat_width_px'] for f in res['flat']},
                      'pass_no_flat_hull_face_gt_40px': bool(p1) and all(f['max_flat_width_px'] <= 40 for f in p1),
                      'crops_ge_9': sum(1 for v in sds if v >= 9.0),
                      'longest_straight_silhouette_px': {f['image']: f['longest_straight_px'] for f in res['silhouette']},
                      'pass_no_straight_silhouette_gt_40px_p10': (lambda L: bool(L) and all(f['longest_straight_px'] <= 40 for f in L))([f for f in res['silhouette'] if f['image'] == 'p10_lawn_eye.jpg'])}   # p1 looks down 30 deg: converging building verticals are not axis-aligned there, so p1 is information only
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res['summary']))
    for c in res['crowns']: print('%-24s %-14s hp_sd %6.2f  luma %5.1f  sat %.3f' % (c['image'], c['box_xywh'][:2], c['hp_sd'], c['mean_luma'], c['mean_hsv_sat']))
    for f in res['flat']: print('flat', f['image'], 'max_flat_width', f['max_flat_width_px'], 'patches>40:', f['patches_wider_than_40_px'], 'flat%% of foliage %.2f' % f['flat_pct_of_foliage'], 'dark pockets %.2f%%' % f['dark_pocket_pct'])
    for f in res['silhouette']: print('silhouette', f['image'], 'longest straight', f['longest_straight_px'], 'px; segments > 40 px:', f['segments_longer_than_40_px'], 'sky %.1f%% foliage %.1f%%' % (f['sky_pct'], f['foliage_pct']), f['longest'][:3])
    if preview and res['crowns']:
        by = {}
        for c in res['crowns']: by.setdefault(c['image'], []).append(c['box_xywh'])
        tiles = []
        for f, boxes in by.items():
            im = Image.open(os.path.join(d, f)).convert('RGB')
            for (x, y, w, h) in boxes: tiles.append(im.crop((x, y, x + w, y + h)).resize((300, 300), Image.LANCZOS))
        cols = 6; rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 300, rows * 300))
        for k, t in enumerate(tiles): sheet.paste(t, ((k % cols) * 300, (k // cols) * 300))
        sheet.save(preview)
if __name__ == '__main__': main()
