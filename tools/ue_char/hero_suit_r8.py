#!/usr/bin/env python3
"""Round-08 ORIGINAL hero suit (Tessera): procedural base colour / normal / ORM on the hero UV atlas.  Fan homage project, not official
Marvel/Sony/Insomniac; no affiliation.  The design lives in tools/ue_char/suit8/design.py (palette, panels, net, badge; nothing is copied from
an existing suit and nothing is taken from the old browser texture); this script evaluates it per texel in rest-pose object space and writes

  art/night1/characters/hero/tex/suit_basecolor_r8.png  suit_normal_r8.png (OpenGL, from the design height map)  suit_orm_r8.png  suit_r8.json
  art/night1/characters/shared/suit_twill_n.png         (the 2/2 twill detail normal of round 05, regenerated; tiled by the material)

  python3 tools/ue_char/hero_suit_r8.py [--n 4096] [--out DIR] [--no-normal]
"""
import sys, os, json, time
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'suit8'))
from p2paths import WT  # noqa: E402
import meshio, design  # noqa: E402
Image.MAX_IMAGE_PIXELS = None


def arg(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def build(n, log=print, style=None, pre=None):
    """style = design.DEFAULT_STYLE override (round 11: tools/ue_char/suits); pre = (mesh, raster) reused across suits of one size."""
    m = pre[0] if pre else meshio.load_body()
    P, N, UV, F, GW = m['P'], m['N'], m['UV'], m['F'], m['GW']
    t0 = time.time()
    tri, w0, w1, inside = pre[1] if pre else meshio.raster_tri(UV, F, n)
    cov = tri >= 0
    log('raster %.1fs coverage %.3f' % (time.time() - t0, cov.mean()))
    # metres per texel of each triangle (anti-alias footprint)
    a3 = np.linalg.norm(np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]), axis=1) / 2
    a2 = np.abs((UV[F[:, 1], 0] - UV[F[:, 0], 0]) * (UV[F[:, 2], 1] - UV[F[:, 0], 1]) - (UV[F[:, 2], 0] - UV[F[:, 0], 0]) * (UV[F[:, 1], 1] - UV[F[:, 0], 1])) / 2 * n * n
    mpt_tri = np.sqrt(a3 / np.maximum(a2, 1e-9)).astype(np.float32)
    mpt_tri = np.clip(mpt_tri, 2e-5, 2e-3)
    gi = {g: i for i, g in enumerate(meshio.GROUPS)}
    jp = {k: tuple(float(x) for x in v) for k, v in m['jpos'].items()}
    cavity = 0.0
    col = np.zeros((n, n, 3), np.float32); hgt = np.zeros((n, n), np.float32)
    rough = np.full((n, n), 0.8, np.float32); ao = np.ones((n, n), np.float32); mptm = np.full((n, n), 2e-4, np.float32)
    step = 256
    for r0 in range(0, n, step):
        sl = slice(r0, min(r0 + step, n))
        c = cov[sl]
        if not c.any(): continue
        Pp = meshio.gather(tri, w0, w1, F, P, sl); Nn = meshio.gather(tri, w0, w1, F, N, sl)
        Nn /= np.linalg.norm(Nn, axis=-1, keepdims=True) + 1e-9
        G = meshio.gather(tri, w0, w1, F, GW, sl)
        mp = mpt_tri[np.where(tri[sl] >= 0, tri[sl], 0)]
        o = design.paint(Pp, Nn, G, mp, gi, jp, style)
        col[sl] = o['col']; hgt[sl] = o['h']; rough[sl] = o['rough']; ao[sl] = o['ao']; mptm[sl] = mp
        cavity = o.get('cavity', cavity)
    log('paint %.1fs' % (time.time() - t0))
    if cavity > 0:
        ao = cavity_ao(hgt, ao, mptm, cov, cavity)
    return dict(col=col, h=hgt, rough=rough, ao=ao, mpt=mptm, cov=cov, tri=tri, relief=cavity > 0)


def cavity_ao(h, ao, mpt, cov, k):
    """Round 12: occlusion at the foot of the raised cords: where the local height is below its 2.5 mm neighbourhood average the AO darkens (k per mm)."""
    sig = float(np.clip(0.0025 / np.median(mpt[cov]), 1.0, 8.0))
    hb = ndi.gaussian_filter(h, sig)
    return np.clip(ao - k * np.clip(hb - h, 0, 1) * cov, 0.55, 1.0).astype(np.float32)


def smooth_mpt(mpt, cov):
    """Round 12: per-texel metres-per-texel without the per-triangle steps (a step in the slope scale at every triangle edge shades the normal map in facets)."""
    w = ndi.gaussian_filter(cov.astype(np.float32), 3.0)
    return (ndi.gaussian_filter(mpt * cov, 3.0) / np.maximum(w, 1e-4)).astype(np.float32)


def save_png(arr, path):
    """Atomic write (a build reading the maps while this runs never sees a half-written PNG)."""
    tmp = path + '.tmp.png'
    Image.fromarray(arr).save(tmp)
    os.replace(tmp, path)


def gutters(img, cov, px):
    """Extend the covered texels by `px` pixels (nearest covered value) so mip levels and filtering never see the empty atlas."""
    _, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True)
    d = ndi.distance_transform_edt(~cov)
    out = img[iy, ix]
    return out, (d <= px) | cov


def normal_from_height(h_mm, mpt, strength=1.0, sigma=0.9):
    """Tangent-space (OpenGL: +X = +u, +Y = -v row = image up) normal of the height map; tools/ue_char/suits/tangent_check.py verifies it against the mesh's
    per-island tangent frames."""
    hm = ndi.gaussian_filter(h_mm, sigma) * 1e-3
    gy, gx = np.gradient(hm)
    nx = -gx / mpt * strength; ny = gy / mpt * strength
    nn = np.stack([nx, ny, np.ones_like(nx)], -1)
    nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    return nn


def main():
    n = int(arg('--n', 8192))
    out = arg('--out', WT + '/art/night1/characters/hero/tex')
    os.makedirs(out, exist_ok=True)
    legacy = '--legacy-r8' in sys.argv          # round-08 flat print (test_regression.py proves it texel for texel)
    r = build(n, style={'relief': {'kind': 'r8'}} if legacy else None)
    cov = r['cov']
    col8 = (np.clip(r['col'], 0, 1) * 255 + 0.5).astype(np.uint8)
    col8, keep = gutters(col8, cov, 24)
    save_png(col8, out + '/suit_basecolor_r8.png')
    if '--no-normal' not in sys.argv:
        hh, _ = gutters(r['h'], cov, 24)
        mp, _ = gutters(smooth_mpt(r['mpt'], cov) if r['relief'] else r['mpt'], cov, 24)
        nn = normal_from_height(hh, mp, sigma=0.6) if r['relief'] else normal_from_height(hh, mp)     # round 12: sharper cord flanks (tangent_check: sigma 0.9 halved the slope)
        save_png(((nn * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), out + '/suit_normal_r8.png')
        ro, _ = gutters(r['rough'], cov, 24); ao, _ = gutters(r['ao'], cov, 24)
        orm = np.stack([ao, ro, np.zeros_like(ao)], -1)
        save_png((np.clip(orm, 0, 1) * 255 + 0.5).astype(np.uint8), out + '/suit_orm_r8.png')
    # twill detail + tiling from the mesh UV density (same as round 05)
    sys.path.insert(0, HERE)
    from hero_suit_r5 import twill_normal  # noqa: E402
    shared = WT + '/art/night1/characters/shared'; os.makedirs(shared, exist_ok=True)
    if not os.path.exists(shared + '/suit_twill_n.png') or '--twill' in sys.argv:
        tw, _ = twill_normal(); Image.fromarray(tw).save(shared + '/suit_twill_n.png')
    m = meshio.load_body(); P, F, UV = m['P'], m['F'], m['UV']
    a3 = np.linalg.norm(np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]), axis=1) / 2
    a2 = np.abs((UV[F[:, 1], 0] - UV[F[:, 0], 0]) * (UV[F[:, 2], 1] - UV[F[:, 0], 1]) - (UV[F[:, 2], 0] - UV[F[:, 0], 0]) * (UV[F[:, 1], 1] - UV[F[:, 0], 1])) / 2
    ok = (a3 > 1e-9) & (a2 > 1e-12)
    uvpm = float(np.median(np.sqrt(a2[ok] / a3[ok])))
    tile_m = 32 * 0.45e-3
    info = dict(size=n, coverage=round(float(cov.mean()), 4), uv_units_per_m=round(uvpm, 4), detail_tiling=round(1.0 / (tile_m * uvpm), 1), yarn_mm=0.45,
                design='Tessera (original), tools/ue_char/suit8/design.py')
    json.dump(info, open(out + '/suit_r8.json', 'w'), indent=1)
    print(json.dumps(info))


if __name__ == '__main__':
    main()
