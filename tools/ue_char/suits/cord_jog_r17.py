# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17 instrument (critic r16: "Ash yoke-seam shelf on the image-RIGHT side (x 2340-2420, 34 px)", "Verdant rib cord step where it crosses the chest stripe (x ~2380, 9 px)"; brief: "cord_jog tracks the
yoke seam on BOTH sides plus every cord crossing a panel border or glyph, step <= 4 px on 8 / 8 chests").

The r16 tracker followed ONE cord (the yoke bottom seam) on the image-left side.  This one follows EVERY long near-horizontal cord of the chest across the WHOLE torso width (both sides, through the
sash, the chest glyph and the stripes):
  1. ridge = luma minus a 41 px vertical median (light cords > 0, dark cords < 0); per polarity a Viterbi path over the columns (state = row, |d row| <= 3 per column, a smoothness cost, emission =
     the ridge) finds the strongest cord; its +-28 rows are masked and the next one is found (K cords per polarity, kept when the cord is visible on >= 45 % of its columns);
  2. a column is 'visible' when the ridge >= 9 luma and the path row is a local ridge peak; the invisible runs are gaps (a cord covered by a panel border / glyph / sash);
  3. JOG = the largest change of the (5-column median) row between neighbouring visible columns beyond the local slope (31 px quadratic fit): a stair-step;
     CROSSING STEP = for every gap of 8 .. 200 columns, the mean of the two extrapolation errors (the 50 visible columns before the gap, quadratic, extrapolated across it to the first visible column after
     it; and the reverse): a cord that comes out of a border / glyph shifted.
Gate: JOG <= 4 px and CROSSING STEP <= 4 px for every tracked cord on all 8 chest stills (cords of the arms are outside the torso x-range).
usage: python3 cord_jog_r17.py <stills dir> <out.json> [--png DIR] [--suits a,b]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
# the torso in the 25 deg 4K chest still: the arm edges bound it (the hero drifts ~100-150 px between rounds: the track stops where the cord's ridge ends)
X0, X1, Y0, Y1 = 1080, 2900, 600, 1900
K = 6
STEP_GATE = 4.0


def viterbi(E, lam=0.6, maxd=3):
    """best path through E[row, col] (maximise sum E - lam*|d row|) with |d row| <= maxd per column"""
    H, W = E.shape
    score = np.full((H, W), -1e9, np.float32); back = np.zeros((H, W), np.int8)
    score[:, 0] = E[:, 0]
    for c in range(1, W):
        best = np.full(H, -1e9, np.float32); arg = np.zeros(H, np.int8)
        for d in range(-maxd, maxd + 1):
            sh = np.full(H, -1e9, np.float32)
            if d >= 0: sh[d:] = score[:H - d, c - 1] if d else score[:, c - 1]
            else: sh[:d] = score[-d:, c - 1]
            sh = sh - lam * abs(d)
            m = sh > best; best = np.where(m, sh, best); arg = np.where(m, d, arg)
        score[:, c] = best + E[:, c]; back[:, c] = arg
    r = int(np.argmax(score[:, -1])); path = np.zeros(W, np.int32); path[-1] = r
    for c in range(W - 1, 0, -1):
        r = r - int(back[r, c]); path[c - 1] = r
    return path, float(score[:, -1].max())


def analyse(path_img, png=None, tag=''):
    a = np.asarray(Image.open(path_img).convert('RGB')).astype(np.float32)
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    sub = L[Y0:Y1, X0:X1]
    R = sub - ndi.median_filter(sub, size=(41, 1))
    R = ndi.uniform_filter1d(R, 3, axis=1)
    H, W = R.shape
    cords = []
    for pol, name in ((1.0, 'light'), (-1.0, 'dark')):
        E = np.clip(pol * R, 0, 40).astype(np.float32)
        # a cord is a THIN ridge: also require that the rows 12 px above / below are lower (rejects the broad shading bands)
        for k in range(K):
            p, sc = viterbi(E)
            vis = np.array([E[p[c], c] >= 9 for c in range(W)])
            # local peak: ridge at the path row beats +-10 rows by >= 4
            for c in range(W):
                if vis[c]:
                    r0 = p[c]; lo = E[max(0, r0 - 10), c]; hi = E[min(H - 1, r0 + 10), c]
                    if not (E[r0, c] - max(lo, hi) >= 4): vis[c] = False
            frac = vis.mean()
            # mask +-28 rows around the path whatever it was
            for c in range(W): E[max(0, p[c] - 28):p[c] + 29, c] = 0
            if frac < 0.45: continue
            cords.append(dict(pol=name, path=p, vis=vis, frac=float(frac)))
    results = []
    for ci, cd in enumerate(cords):
        p = cd['path'].astype(np.float64); vis = cd['vis']
        cs = np.nonzero(vis)[0]
        if len(cs) < 120: continue
        rs = ndi.median_filter(p[cs], size=5, mode='nearest')
        fit = np.zeros_like(rs)
        for i in range(len(cs)):
            sel = np.abs(cs - cs[i]) <= 15
            fit[i] = np.polyval(np.polyfit(cs[sel], rs[sel], 2), cs[i]) if sel.sum() >= 5 else rs[i]
        slope = np.gradient(fit, cs)
        adj = np.diff(cs) == 1
        jump = np.where(adj, np.abs(np.diff(rs) - slope[:-1]), 0.0); jump[:20] = 0; jump[-20:] = 0
        jk = int(np.argmax(jump))
        # crossing steps over gaps
        gaps = []
        for i in range(len(cs) - 1):
            g = int(cs[i + 1] - cs[i] - 1)
            if 8 <= g <= 200:
                lo_ = [j for j in range(max(0, i - 50), i + 1)]; hi_ = [j for j in range(i + 1, min(len(cs), i + 52))]
                if len(lo_) < 30 or len(hi_) < 30: continue
                cl, rl = cs[lo_], rs[lo_]; ch, rh = cs[hi_], rs[hi_]
                pl = np.polyfit(cl, rl, 2 if len(lo_) >= 45 else 1); ph = np.polyfit(ch, rh, 2 if len(hi_) >= 45 else 1)
                e1 = rs[i + 1] - np.polyval(pl, cs[i + 1]); e2 = rs[i] - np.polyval(ph, cs[i])
                gaps.append((abs(0.5 * (e1 - e2)) if np.sign(e1) != np.sign(e2) or True else 0.0, int(cs[i] + X0), int(cs[i + 1] + X0), int(np.mean([rs[i], rs[i + 1]]) + Y0), g))
        gaps.sort(reverse=True)
        results.append(dict(pol=cd['pol'], y_mid=int(np.median(p) + Y0), x_range=[int(cs[0] + X0), int(cs[-1] + X0)], frac=round(cd['frac'], 2),
                            jog_px=round(float(jump[jk]), 1), jog_at=[int(cs[jk] + X0), int(rs[jk] + Y0)],
                            cross_px=round(float(gaps[0][0]), 1) if gaps else 0.0, cross_at=[gaps[0][1], gaps[0][3]] if gaps else None, cross_gap=gaps[0][4] if gaps else None,
                            n_gaps=len(gaps), _cs=cs, _rs=rs))
    mj = max([r['jog_px'] for r in results] or [0.0]); mc = max([r['cross_px'] for r in results] or [0.0])
    out = dict(ok=len(results) > 0, cords=[{k: v for k, v in r.items() if not k.startswith('_')} for r in results], n_cords=len(results), max_jog_px=mj, max_cross_px=mc)
    if png:
        im = Image.open(path_img).convert('RGB'); dr = ImageDraw.Draw(im)
        for r in results:
            col = (255, 0, 255) if r['pol'] == 'light' else (0, 255, 255)
            for c, rr in zip(r['_cs'][::2], r['_rs'][::2]): dr.point((int(c + X0), int(rr + Y0) - 8), fill=col)
            if r['jog_px'] > STEP_GATE: dr.ellipse((r['jog_at'][0] - 25, r['jog_at'][1] - 25, r['jog_at'][0] + 25, r['jog_at'][1] + 25), outline=(255, 0, 0), width=4)
            if r['cross_px'] > STEP_GATE and r['cross_at']: dr.ellipse((r['cross_at'][0] - 25, r['cross_at'][1] - 25, r['cross_at'][0] + 25, r['cross_at'][1] + 25), outline=(255, 160, 0), width=4)
        im.crop((X0 - 60, Y0 - 40, X1 + 60, Y1 + 40)).resize(((X1 - X0 + 120) // 2, (Y1 - Y0 + 80) // 2)).save(os.path.join(png, 'cordjog17_%s.jpg' % tag), quality=88)
    return out


def main():
    d, outp = sys.argv[1], sys.argv[2]
    png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    suits = sys.argv[sys.argv.index('--suits') + 1].split(',') if '--suits' in sys.argv else SUITS
    if png: os.makedirs(png, exist_ok=True)
    res = {}
    for s in suits:
        p = os.path.join(d, 'skin_%s_chest_4k.png' % s)
        if not os.path.exists(p): p = p.replace('.png', '.jpg')
        res[s] = analyse(p, png, s)
        r = res[s]
        print(s, 'cords %d  max jog %.1f px  max crossing step %.1f px' % (r['n_cords'], r['max_jog_px'], r['max_cross_px']), [(c['y_mid'], c['jog_px'], c['cross_px']) for c in r['cords']])
    res['gate'] = all(res[s]['ok'] and res[s]['max_jog_px'] <= STEP_GATE and res[s]['max_cross_px'] <= STEP_GATE for s in suits)
    json.dump(res, open(outp, 'w'), indent=1)
    print('GATE every tracked cord: jog <= 4 px and crossing step <= 4 px on all chests:', res['gate'])


if __name__ == '__main__':
    main()
