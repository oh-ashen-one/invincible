# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 16 instrument (critic r15: "the Cinder centre seam zig-zags ~60 px"): track the face centre seam cord on a 4K headfront still and measure its lateral deviation.

The seam is a light raised cord on the hood midline.  Per row (top of the hood -> chin) the tracker takes the brightest ridge (luma minus a 25 px median background) inside +-W px of
the previous row's column (seeded at the top of the head by the strongest ridge near the head's centre column), skipping the lens / brow-pipe rows where no ridge is found.
Robust step: a 15-row running median, rows > 6 px off it dropped.  Outputs per still: the column per row, `dev100` = max |x(y + 100) - x(y)| over the tracked rows (gate <= 10 px), `resid` = max |x - straight line fit|, an overlay crop.
usage: python3 seam_track_r16.py <stills dir> <out.json> [--png DIR] [--suits a,b]"""
import json, sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import median_filter, uniform_filter1d
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def head_box(L, rgb):
    """the hood: the darkest big blob in the upper middle of the frame (rows where the background is sky / floor): use the column profile of 'not background'"""
    H, W = L.shape
    bg_top = np.median(rgb[5:40, :, :].reshape(-1, 3), axis=0)
    d = np.linalg.norm(rgb - bg_top[None, None], axis=-1)
    return d


def track(path, png=None, tag='', suit=None, y_start=60):
    rgb = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    L = luma(rgb)
    H, W = L.shape
    # the cord is ~30 px wide and light (luma ~200 on a 50 - 130 hood): a 25 px box filter across, then per row the brightest column near the previous one
    B = uniform_filter1d(L, 15, axis=1)
    cx = W // 2
    xs = {}
    x = None; miss = 0; ref = None; chs = []
    for y in range(y_start, H - 40):
        if x is None:
            seg = B[y, cx - 160:cx + 160]; j = int(np.argmax(seg)) + cx - 160      # the portrait is centred on the face: the seam is within +-160 px of the centre column
            rid = B[y, j] - 0.5 * (B[y, j - 32] + B[y, j + 32])
            if rid > 25 and np.std(L[y, j - 200:j - 40]) < 25 and np.std(L[y, j + 40:j + 200]) < 25: x = float(j); xs[y] = x
            continue
        lo, hi = int(x) - 24, int(x) + 25
        seg = B[y, lo:hi]; j = int(np.argmax(seg)) + lo
        wide = B[y, lo - 90:hi + 90]
        bg = np.percentile(wide, 30)
        # a ridge: the peak beats the 30th percentile of +-115 px by 45 luma and both sides 40 px away by 30 (a horizontal pipe / lens rim lifts the whole row)
        ok = B[y, j] - B[y, j - 34] > 12 and B[y, j] - B[y, j + 34] > 12
        if ok and ref is not None:      # the seam cord's own colour (chromaticity of the first 150 tracked rows): a vent slot / honeycomb cell edge or a lens rim is another colour
            px = rgb[y, j]; ch = px / max(px.sum(), 1e-6)
            ok = float(np.abs(ch - ref).sum()) < 0.06
        if ok and abs(j - x) <= min(24, 6 + miss // 4):
            # sub-pixel: centroid of L above the half-max inside +-16 px
            seg2 = L[y, j - 16:j + 17]; t = seg2 - (seg2.max() + bg) / 2; t = np.clip(t, 0, None)
            xc = j - 16 + float((t * np.arange(33)).sum() / max(t.sum(), 1e-6))
            xs[y] = xc; x = xc; miss = 0
            if ref is None:
                px = rgb[y, int(round(xc))]; chs.append(px / max(px.sum(), 1e-6))
                if len(chs) >= 150: ref = np.median(np.array(chs), axis=0)
        else:
            miss += 1
            if miss > 250: break
    ys = np.array(sorted(xs)); xv = np.array([xs[k] for k in ys])
    if len(ys) < 300:
        if y_start < 500: return track(path, png, tag, suit, y_start=y_start + 220)      # the crown's stripes can hide the seed: start lower (below the crown piping)
        return dict(ok=False, why='short track %d' % len(ys))
    # rows where the seam runs UNDER an accent piece (the jaw vent's honeycomb / slots, the crown stripes' ends): >= 8 % of the +-80 px band around the track's median column is
    # accent-family colour (colour direction within 20 deg of the suit's accent / accent_d, as in back_bleed_r16.py) - the seam is covered there, those rows are dropped
    if suit is not None:
        import back_bleed_r16 as BB
        pal = BB.palette(suit)
        A_ = np.stack([BB.lin(pal['accent']), BB.lin(pal['accent_d'])]); A_ /= np.linalg.norm(A_, axis=1, keepdims=True)
        O_ = np.stack([BB.lin(pal[k]) for k in ('body', 'crown', 'deep', 'ink', 'stitch')]); O_ /= np.linalg.norm(O_, axis=1, keepdims=True)
        cx_ = int(np.median(xv)); band_ = rgb[:, max(0, cx_ - 80):cx_ + 81] / 255.0
        bl_ = np.where(band_ <= 0.04045, band_ / 12.92, ((band_ + 0.055) / 1.055) ** 2.4)
        v_ = bl_ / np.maximum(np.linalg.norm(bl_, axis=-1, keepdims=True), 1e-9)
        aa_ = np.degrees(np.arccos(np.clip(v_ @ A_.T, -1, 1))).min(-1); oo_ = np.degrees(np.arccos(np.clip(v_ @ O_.T, -1, 1))).min(-1)
        accm_ = (aa_ <= 20) & (aa_ + 1.5 <= oo_); accm_[:, 60:101] = False          # not the seam cord itself (+-20 px around the median column): a light cord can share the accent's colour direction (Saffron's cream)
        accrow = accm_.mean(1) >= 0.08
        accrow = ndi.binary_dilation(accrow, iterations=12)
        keep0 = ~accrow[ys]
        ys, xv = ys[keep0], xv[keep0]
    # robust: a 15-row running median, rows more than 6 px off it are dropped (a vent slot / honeycomb edge, a lens-rim glint), then 9 rows of smoothing (stitch noise)
    from scipy.ndimage import median_filter as _mf
    med = _mf(xv, size=15, mode='nearest')
    keep = np.abs(xv - med) <= 6
    ys, xv = ys[keep], xv[keep]
    xsm = uniform_filter1d(xv, 9)
    dev = []
    lookup = dict(zip(ys.tolist(), xsm.tolist()))
    for yy, xx in zip(ys, xsm):
        if (yy + 100) in lookup: dev.append((abs(lookup[yy + 100] - xx), int(yy)))
    d100 = max(dev) if dev else (None, None)
    # round 17: the local jog (critic r16: the Cinder seam 'breaks and jogs ~120 px' at the chin): the largest lateral change over 20 rows (= a step), and the same over the last 350 tracked rows (chin / throat)
    # round 17 (supplementary, NOT the gate): dev100 of a 31-row MEDIAN trace - a low-contrast cord (Glacier: pale cord on a pale hood) makes single rows jump by +-6 px, which the 9-row mean keeps
    xm31 = _mf(xsm, size=31, mode='nearest'); lk31 = dict(zip(ys.tolist(), xm31.tolist()))
    dev31 = [(abs(lk31[yy + 100] - xx), int(yy)) for yy, xx in zip(ys, xm31) if (yy + 100) in lk31]
    d100_31 = max(dev31) if dev31 else (None, None)
    st20 = [(abs(lookup[yy + 20] - xx), int(yy)) for yy, xx in zip(ys, xsm) if (yy + 20) in lookup]
    step20 = max(st20) if st20 else (None, None)
    st20_chin = max([t for t in st20 if t[1] >= ys[-1] - 350] or [(None, None)])
    A = np.vstack([ys, np.ones_like(ys)]).T
    co, *_ = np.linalg.lstsq(A, xsm, rcond=None)
    res = xsm - A @ co
    out = dict(ok=True, y_top=int(ys[0]), y_bot=int(ys[-1]), n_rows=int(len(ys)), dev100=round(float(d100[0]), 1), dev100_at_y=d100[1],
               dev100_med31=round(float(d100_31[0]), 1) if d100_31[0] is not None else None, dev100_med31_at_y=d100_31[1],
               step20=round(float(step20[0]), 1) if step20[0] is not None else None, step20_at_y=step20[1], step20_chin=round(float(st20_chin[0]), 1) if st20_chin[0] is not None else None, step20_chin_at_y=st20_chin[1],
               resid_max=round(float(np.abs(res).max()), 1), slope=round(float(co[0]), 4), range_x=round(float(xsm.max() - xsm.min()), 1),
               cols=[[int(a), round(float(b), 1)] for a, b in zip(ys[::20], xsm[::20])])
    if png:
        im = Image.open(path).convert('RGB')
        dr = ImageDraw.Draw(im)
        for a, b in zip(ys, xsm): dr.point((b + 25, a), fill=(255, 0, 255))
        x0c = int(xsm.mean())
        im.crop((max(0, x0c - 700), max(0, ys[0] - 60), min(W, x0c + 700), min(H, ys[-1] + 60))).resize((700, int(700 * (ys[-1] - ys[0] + 120) / 1400))).save(os.path.join(png, 'seam_%s.jpg' % tag), quality=88)
    return out


def main():
    d, outp = sys.argv[1], sys.argv[2]
    png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    suits = sys.argv[sys.argv.index('--suits') + 1].split(',') if '--suits' in sys.argv else SUITS
    if png: os.makedirs(png, exist_ok=True)
    res = {}
    for s in suits:
        p = os.path.join(d, 'skin_%s_headfront_4k.png' % s)
        if not os.path.exists(p): p = p.replace('.png', '.jpg')
        res[s] = track(p, png, s, suit=s)
        r = res[s]
        print(s, 'dev100 %s at y %s  resid %s  range %s rows %s' % (r.get('dev100'), r.get('dev100_at_y'), r.get('resid_max'), r.get('range_x'), r.get('n_rows')) if r['ok'] else r)
    res['gate_dev100_le_10'] = all(res[s].get('ok') and res[s]['dev100'] <= 10 for s in suits)
    json.dump(res, open(outp, 'w'), indent=1)
    print('GATE dev100 <= 10 on all:', res['gate_dev100_le_10'])


if __name__ == '__main__':
    main()
