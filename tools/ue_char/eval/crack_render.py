"""Offline stand-in for the UE see-through test (round 05): renders posed citizens single-sided (back faces culled, like the game) with their
atlas tile, in a row against a bright wall, with and without the under-layer hull, and runs the critic's cracks.py measure on it.
No GPU.  Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.
  python3 tools/ue_char/eval/crack_render.py OUT_DIR NAME[:clip:frame] ... [--px-per-m 234]
"""
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import crack_probe as C
import underlayer as U
from p2paths import scr


def posed_full(name, clip, frame, use_hull, expand=0.0):
    """Like crack_probe.posed but also returns per-corner tile-local uv (nt, 3, 2)."""
    G, T = C.posed(name, clip, frame, use_hull, expand)
    pos, tuv, idx, nrm, _ = U.load(name)
    uv = tuv[idx] if expand <= 0 else U.expand_triangles(pos, idx, tuv, expand)[1]
    if use_hull:
        H = np.load(scr('eval', 'hull', name + '.npz'))
        uv = np.concatenate([uv, np.repeat(H['tri_uv'][:, None, :], 3, axis=1)], 0)
    return G, T, uv


def raster(scene_items, W, H, px_per_m, wall=(196, 132, 100), floor_y=0.0, ground=(214, 210, 198), light=(0.35, 0.55, 0.75), hull_from=None, hull_col=(60, 255, 60)):
    img = np.zeros((H, W, 3), np.float32); img[:] = wall
    gy = int(H - 0.06 * H)
    img[gy:] = ground
    zb = np.full((H, W), -1e9, np.float32)
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    for (P, T, uv, tex, ox, nG) in scene_items:
        A = P[T[:, 0]]; B = P[T[:, 1]]; Cc = P[T[:, 2]]
        fn = np.cross(B - A, Cc - A)
        ln = np.linalg.norm(fn, axis=1) + 1e-15
        fn = fn / ln[:, None]
        front = fn[:, 2] > 0                                         # camera at +z, single-sided
        tw, th = tex.shape[1], tex.shape[0]
        for ti in np.where(front)[0]:
            pts = P[T[ti]]
            xs = pts[:, 0] * px_per_m + ox; ys = gy - pts[:, 1] * px_per_m
            x0, x1 = int(max(0, np.floor(xs.min()))), int(min(W - 1, np.ceil(xs.max())))
            y0, y1 = int(max(0, np.floor(ys.min()))), int(min(H - 1, np.ceil(ys.max())))
            if x1 < x0 or y1 < y0: continue
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9: continue
            gx_, gy_ = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((ys[1] - ys[2]) * (gx_ - xs[2]) + (xs[2] - xs[1]) * (gy_ - ys[2])) / den
            w1 = ((ys[2] - ys[0]) * (gx_ - xs[2]) + (xs[0] - xs[2]) * (gy_ - ys[2])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -0.01) & (w1 >= -0.01) & (w2 >= -0.01)
            if not m.any(): continue
            z = w0 * pts[0, 2] + w1 * pts[1, 2] + w2 * pts[2, 2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            vis = m & (z > sub)
            if not vis.any(): continue
            u = w0 * uv[ti, 0, 0] + w1 * uv[ti, 1, 0] + w2 * uv[ti, 2, 0]; v = w0 * uv[ti, 0, 1] + w1 * uv[ti, 1, 1] + w2 * uv[ti, 2, 1]
            col = tex[np.clip(((1 - v) * th).astype(int), 0, th - 1), np.clip((u * tw).astype(int), 0, tw - 1)].astype(np.float32)
            if hull_from is not None and ti >= nG: col = np.broadcast_to(np.asarray(hull_col, np.float32), col.shape)
            lam = 0.55 + 0.45 * float(np.clip(fn[ti] @ L, 0, 1))
            sub[vis] = z[vis]
            img[y0:y1 + 1, x0:x1 + 1][vis] = (col * lam)[vis]
    return np.clip(img, 0, 255).astype(np.uint8)


def main():
    av = sys.argv[1:]
    ppm = 234.0
    if '--px-per-m' in av:
        k = av.index('--px-per-m'); ppm = float(av[k + 1]); av = av[:k] + av[k + 2:]
    out = av[0]; specs = [a for a in av[1:] if not a.startswith('--')]
    EXP = float(os.environ.get('EXPAND', '0'))
    os.makedirs(out, exist_ok=True)
    res = {}
    for use_hull in (False, True):
        items = []
        W = int(len(specs) * 1.15 * ppm) + 200; H = int(2.0 * ppm)
        for k, sp in enumerate(specs):
            nm, clip, fr = (sp.split(':') + ['walk', '5'])[:3]
            G, T, uv = posed_full(nm, clip, int(fr), use_hull, EXP)
            tex = np.asarray(Image.open(os.path.join(scr('eval', 'tiles'), nm + '.png')).convert('RGB'))
            # view from the side: rotate by 90 deg about y (walking +x in the pack's frame faces +z)
            th = np.radians(90); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])
            nG = len(U.load(nm)[2])
            items.append((G @ R.T, T, uv, tex, 100 + k * 1.15 * ppm, nG))
        img = raster(items, W, H, ppm)
        p = os.path.join(out, 'citizens_%s.png' % ('hull' if use_hull else 'garment'))
        Image.fromarray(img).save(p)
        if use_hull:
            Image.fromarray(raster(items, W, H, ppm, hull_from=True)).save(os.path.join(out, 'citizens_hullmap.png'))
        res['hull' if use_hull else 'garment'] = p
    print(json.dumps(res))


if __name__ == '__main__':
    main()
