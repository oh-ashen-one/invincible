# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 16 instrument (critic r15: "a 20 px stair-step groove jog at the Verdant armpit (~1300, 1310)", "stair-step jogs where groove cords meet panel borders: Ash and Cinder left chest").

The round-12 chest jog instrument (relief_check_r12.py jog) follows the ACCENT panel edge; the jogs of round 15 are in the light YOKE SEAM CORD and the net lines crossing the
torso side under the armpit.  This tracker follows one near-horizontal light cord across the chest's image-left armpit side (the side the 25 deg chest camera sees; the hero's
right): per column the row of the strongest ridge (luma minus a 41 px vertical median) inside +-6 px of the previous column's row (+-26 after a lost column: a stair-step), seeded at `seed_x` on the strongest ridge
in rows [y0, y1]; tracked left and right while the ridge is clear (>= 10 luma).  After a 5-column median, `max_jump` = the largest row change between neighbouring columns
beyond the local slope (a 31 px quadratic fit): a stair-step shows as one large jump.  Gate (round 16): max_jump <= 4 px over the tracked run.
usage: python3 cord_jog_r16.py <stills dir> <out.json> [--png DIR]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
# (x0, x1) the image-left torso side from the arm edge to the sash / centre, (y0, y1) the band where the yoke's bottom seam lies in the 4K chest still
ROI = dict(x0=1130, x1=1700, y0=1180, y1=1460)
X1 = dict(cinder=1530)      # Cinder's yoke sash starts at x ~1550: the track must not run onto its border


def track(path, png=None, tag=''):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    x0, x1, y0, y1 = ROI['x0'], X1.get(tag, ROI['x1']), ROI['y0'], ROI['y1']
    sub = L[y0 - 40:y1 + 40, x0:x1]
    R = sub - ndi.median_filter(sub, size=(41, 1))
    R = ndi.uniform_filter1d(R, 3, axis=1)[40:-40]
    H, W = R.shape
    # seed: the column band 40 % - 60 % of the ROI, the strongest horizontal ridge = the row with the largest mean ridge over 30 columns
    best = None
    for sx in range(int(W * 0.35), int(W * 0.65), 10):
        prof = R[:, sx - 15:sx + 15].mean(1)
        r = int(np.argmax(prof))
        if best is None or prof[r] > best[0]: best = (prof[r], sx, r)
    if best is None or best[0] < 8: return dict(ok=False, why='no cord')
    _, sx, sr = best
    # the cord's own colour (chromaticity at the seed, 30 columns): the track stops where the ridge has another colour (an arm's accent net line beyond the torso edge, a sash border)
    sub_rgb = a[y0:y1, x0:x1]
    ref = np.median(np.stack([sub_rgb[sr, c] / max(sub_rgb[sr, c].sum(), 1e-6) for c in range(max(0, sx - 15), min(W, sx + 15))]), axis=0)
    rows = {}
    for direction in (1, -1):
        r = float(sr); miss = 0
        rng = range(sx, W) if direction == 1 else range(sx - 1, -1, -1)
        for c in rng:
            wdw = 6 if miss == 0 else 26          # after a lost column the search widens to +-26 rows: a stair-step continues the cord 5 - 25 px higher / lower
            lo, hi = max(0, int(r) - wdw), min(H, int(r) + wdw + 1)
            seg = R[lo:hi, c]
            k = int(np.argmax(seg))
            px = sub_rgb[min(H - 1, lo + k), c]; okc = float(np.abs(px / max(px.sum(), 1e-6) - ref).sum()) < 0.16
            if seg[k] >= (10 if miss == 0 else 14) and okc:
                # the cord's CENTRE: the middle of the run of rows around the peak whose ridge is >= half the peak (the lit flank and the shadow flank swap with the light)
                a_, b_ = k, k
                while a_ > 0 and seg[a_ - 1] >= 0.5 * seg[k]: a_ -= 1
                while b_ < len(seg) - 1 and seg[b_ + 1] >= 0.5 * seg[k]: b_ += 1
                rows[c] = lo + 0.5 * (a_ + b_); r = rows[c]; miss = 0
            else:
                miss += 1
                if miss > 12: break
    cs = np.array(sorted(rows)); rs = np.array([rows[c] for c in cs], np.float64)
    if len(cs) < 60: return dict(ok=False, why='short track %d' % len(cs))
    rs = ndi.median_filter(rs, size=5, mode='nearest')
    fit = np.zeros_like(rs)
    for i in range(len(cs)):
        sel = np.abs(cs - cs[i]) <= 15
        fit[i] = np.polyval(np.polyfit(cs[sel], rs[sel], 2), cs[i]) if sel.sum() >= 5 else rs[i]
    slope = np.gradient(fit, cs)
    adj = np.diff(cs) == 1
    jump = np.where(adj, np.abs(np.diff(rs) - slope[:-1]), 0.0)
    # a jump over a gap of up to 12 columns (the tracker bridged a crossing line): the row change minus slope x gap
    gap = np.diff(cs)
    jump_gap = np.where(~adj, np.abs(np.diff(rs) - slope[:-1] * gap), 0.0)
    jj = np.maximum(jump, jump_gap)
    jj[:25] = 0; jj[-25:] = 0             # the first / last 25 columns: where the cord runs into the arm edge or a sash border (the tracker may step onto that border)
    k = int(np.argmax(jj))
    # round 17: the same maximum over the UNDER-ARM run only (x < 1600): where the r15 stair-steps were; the run's far end meets a sash border / net line (the cord's thicker end cap), where the tracker may step
    ua = (cs[:-1] + x0) < 1600
    out = dict(ok=True, columns=int(len(cs)), x_range=[int(cs[0] + x0), int(cs[-1] + x0)], max_jump_px=round(float(jj.max()), 1), max_jump_under_arm_px=round(float(jj[ua].max()), 1) if ua.any() else None, jump_at=[int(cs[k] + x0), int(rs[k] + y0)],
               jumps_over_4=[[int(cs[i] + x0), int(rs[i] + y0), round(float(jj[i]), 1)] for i in np.nonzero(jj > 4)[0][:10]])
    if png:
        im = Image.open(path).convert('RGB'); dr = ImageDraw.Draw(im)
        for c, r in zip(cs, rs): dr.point((int(c + x0), int(r + y0) - 6), fill=(255, 0, 255))
        dr.rectangle((cs[k] + x0 - 12, rs[k] + y0 - 12, cs[k] + x0 + 12, rs[k] + y0 + 12), outline=(255, 255, 0))
        im.crop((x0 - 40, y0 - 60, x1 + 40, y1 + 60)).save(os.path.join(png, 'cordjog_%s.jpg' % tag), quality=90)
    return out


def main():
    d, outp = sys.argv[1], sys.argv[2]
    png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    if png: os.makedirs(png, exist_ok=True)
    res = {}
    for s in SUITS:
        p = os.path.join(d, 'skin_%s_chest_4k.png' % s)
        if not os.path.exists(p): p = p.replace('.png', '.jpg')
        res[s] = track(p, png, s)
        r = res[s]; print(s, {k: r[k] for k in ('columns', 'x_range', 'max_jump_px', 'jump_at')} if r['ok'] else r)
    res['gate_max_jump_le_4'] = all(res[s].get('ok') and res[s]['max_jump_px'] <= 4 for s in SUITS)
    print('GATE yoke-seam cord jog <= 4 px on all 8 chest stills:', res['gate_max_jump_le_4'])
    json.dump(res, open(outp, 'w'), indent=1)


if __name__ == '__main__':
    main()
