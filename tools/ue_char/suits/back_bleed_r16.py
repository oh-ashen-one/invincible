# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 16 instrument (critic r15: "the front emblem and sash repeat on the Tessera and Plum backs, as if projected through the torso").

On each 4K back still: the hero silhouette (distance from the background, which is a smooth sky / floor gradient: a per-row median of the frame's outer columns), the BACK TORSO MASK
(rows from 0.170 to 0.340 of the silhouette height below the head top: the collar down to just above the belt piping; columns
+-0.13 m of the silhouette's centre column at that row - the sash ended at |x| 0.118 m, the shoulder caps' ring cords lie outside - and 6 px inside the silhouette), and every pixel whose colour DIRECTION (linear RGB, illumination-invariant up to a white light) is closer to the suit's accent
(the front emblem / sash fill colour; accent_d, its darker shade, counts with it) than to any other palette colour, by >= 1.5 deg, within 20 deg of it and not near-black (luma >= 18).  Connected clusters of such pixels with
>= 20 px area are failures (gate: 0 clusters on every suit).  Overlay crops go to --png.
usage: python3 back_bleed_r16.py <stills dir> <out.json> [--png DIR]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
DEF = dict(body='#0f4452', crown='#0b3441', deep='#071a21', ink='#050d11', accent='#e0780c', accent_d='#ad5c08', stitch='#9cc0c6', sole='#0d1012')


def lin(h):
    c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def palette(suit):
    d = json.load(open(os.path.join(HERE, 'suits.json')))
    for s in d['suits']:
        if s['id'] == suit:
            p = dict(DEF); p.update(s['style'].get('palette', {})); return p
    raise KeyError(suit)


def check(path, suit, png=None):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255.0
    H, W, _ = a.shape
    al = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    # per-row background: linear interpolation between two side strips (the hero stands at the centre, ~1680 - 2160 px wide at 4K; the sky / floor gradient varies along x)
    bl = np.median(a[:, 1250:1450], axis=1); br = np.median(a[:, 2390:2590], axis=1)
    t = (np.arange(W) - 1350.0) / (2490.0 - 1350.0)
    bg = bl[:, None, :] * (1 - t)[None, :, None] + br[:, None, :] * t[None, :, None]
    dist = np.linalg.norm(a - bg, axis=-1)
    sil = ndi.binary_opening(dist > 0.10, iterations=2)
    sil[:, :1450] = False; sil[:, 2390:] = False
    lab, n = ndi.label(sil)
    if n == 0: return dict(ok=False, why='no silhouette')
    sizes = ndi.sum(sil, lab, range(1, n + 1)); k = int(np.argmax(sizes)) + 1
    hero = lab == k
    hero_in = ndi.binary_erosion(hero, iterations=6)      # 6 px inside the silhouette: the anti-aliased edge (body colour blended with the sky) is no colour of the suit
    ys, xs = np.where(hero)
    top, bot = ys.min(), ys.max()
    # the feet's shadow joins the silhouette at the bottom: use the head top and the known stage framing (hero height ~ the rows down to the lowest pixel of the legs' columns)
    Hh = bot - top
    pxm = Hh / 1.80
    r0, r1 = int(top + 0.170 * Hh), int(top + 0.340 * Hh)
    tor = np.zeros_like(hero)
    for r in range(r0, r1):
        cols = np.where(hero[r])[0]
        if len(cols) == 0: continue
        c = 0.5 * (cols.min() + cols.max())
        lo, hi = int(c - 0.13 * pxm), int(c + 0.13 * pxm)
        tor[r, lo:hi + 1] = hero_in[r, lo:hi + 1]
    pal = palette(suit)
    names = [k_ for k_ in ('body', 'crown', 'deep', 'ink', 'accent', 'accent_d', 'stitch')]
    P = np.stack([lin(pal[k_]) for k_ in names]); P = P / np.linalg.norm(P, axis=1, keepdims=True)
    v = al / np.maximum(np.linalg.norm(al, axis=-1, keepdims=True), 1e-9)
    ang = np.degrees(np.arccos(np.clip(v @ P.T, -1, 1)))                     # (H, W, 7)
    ia = names.index('accent')
    others = np.delete(ang, [ia, names.index('accent_d')], axis=-1).min(-1)          # accent_d is the same hue, darker: the accent FAMILY counts
    Y = 255 * (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])
    acc = (ang[..., ia] <= 20.0) & (ang[..., ia] + 1.5 <= others) & (Y >= 18) & tor
    lab2, n2 = ndi.label(acc, structure=np.ones((3, 3)))
    cl = []
    if n2:
        ar = ndi.sum(acc, lab2, range(1, n2 + 1))
        com = ndi.center_of_mass(acc, lab2, range(1, n2 + 1))
        cl = [dict(area=int(s_), y=int(c_[0]), x=int(c_[1])) for s_, c_ in zip(ar, com) if s_ >= 20]
    out = dict(ok=True, torso_px=int(tor.sum()), accent_px=int(acc.sum()), clusters_ge20=len(cl), largest=max([c['area'] for c in cl], default=0), clusters=sorted(cl, key=lambda c: -c['area'])[:12],
               torso_rows=[r0, r1], hero_px=int(Hh))
    if png:
        im = Image.open(path).convert('RGB'); ov = np.asarray(im).copy()
        edge = tor ^ ndi.binary_erosion(tor, iterations=3)
        ov[edge] = (255, 255, 0); ov[acc] = (255, 0, 255)
        cx = int(xs.mean())
        Image.fromarray(ov).crop((cx - 420, max(0, r0 - 260), cx + 420, min(H, r1 + 160))).save(os.path.join(png, 'back_%s.jpg' % suit), quality=88)
    return out


def main():
    d, outp = sys.argv[1], sys.argv[2]
    png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    if png: os.makedirs(png, exist_ok=True)
    res = {}
    for s in SUITS:
        p = os.path.join(d, 'skin_%s_back_4k.png' % s)
        res[s] = check(p, s, png)
        r = res[s]; print(s, {k: r[k] for k in ('torso_px', 'accent_px', 'clusters_ge20', 'largest')} if r['ok'] else r)
    res['gate_no_cluster_ge20'] = all(res[s].get('clusters_ge20', 1) == 0 for s in SUITS)
    print('GATE no accent cluster >= 20 px in the back torso:', res['gate_no_cluster_ge20'])
    json.dump(res, open(outp, 'w'), indent=1)


if __name__ == '__main__':
    main()
