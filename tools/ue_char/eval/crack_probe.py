"""Offline see-through test for the crowd citizens (round 05): counts thin uncovered slivers inside the silhouette of the
posed garment mesh with and without the under-layer hull (orthographic side / front / back / 3/4 views, 2 mm pixels).
Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.
  python3 tools/ue_char/eval/crack_probe.py NAME [NAME ...] [--clip walk --frame 5]
"""
import json, os, sys
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import underlayer as U
from p2paths import scr

PX = 0.002


def raster(P, T, W, Hh, org, mask, cull=True):
    """Coverage of the triangles; cull=True keeps only the ones facing the camera (camera at +z looking down -z): the game draws single-sided,
    so the inside of the far wall of a hollow garment does not hide a crack in the near wall."""
    if cull:
        n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        T = T[n[:, 2] > 0]
    A = (P[T[:, 0]] - org) / PX; B = (P[T[:, 1]] - org) / PX; C = (P[T[:, 2]] - org) / PX
    for a, b, c in zip(A, B, C):
        x0 = int(max(0, np.floor(min(a[0], b[0], c[0])))); x1 = int(min(W - 1, np.ceil(max(a[0], b[0], c[0]))))
        y0 = int(max(0, np.floor(min(a[1], b[1], c[1])))); y1 = int(min(Hh - 1, np.ceil(max(a[1], b[1], c[1]))))
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12: continue
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        m = (l1 >= -0.02) & (l2 >= -0.02) & (l1 + l2 <= 1.02)
        mask[y0:y1 + 1, x0:x1 + 1] |= m


def holes(mask):
    filled = ndimage.binary_fill_holes(mask)
    h = filled & ~mask
    # thin = not removed by a 5 px (10 mm) opening
    thick = ndimage.binary_opening(h, structure=np.ones((5, 5), bool))
    thin = h & ~thick
    lab, n = ndimage.label(thin)
    return int(thin.sum()), int(n)


def posed(name, clip, frame, use_hull, expand=0.0):
    """LBS in game space with the crowd pack's baked matrices (same maths as citizen_rig.lbs)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import importlib.util
    npc = U.NPC
    p = json.load(open(os.path.join(npc, 'people.json'))); pb = open(os.path.join(npc, 'people.bin'), 'rb').read()
    A = np.frombuffer(pb, np.float32, p['frames'] * p['nb'] * 12, p['anim']).reshape(p['frames'], p['nb'], 3, 4)
    m = json.load(open(os.path.join(npc, 'citizens.json'))); b = open(os.path.join(npc, 'citizens.bin'), 'rb').read()
    v = next(x for x in m['variants'] if x['name'] == name); L = v['lods'][0]; nv, nt = L['nv'], L['nt']
    pos = np.frombuffer(b, np.float32, nv * 3, L['pos']).reshape(-1, 3).astype(float)
    si = np.frombuffer(b, np.uint8, nv * 4, L['si']).reshape(-1, 4).astype(int)
    sw = np.frombuffer(b, np.uint8, nv * 4, L['sw']).reshape(-1, 4).astype(float) / 255.0
    idx = np.frombuffer(b, np.uint32 if L.get('idx32') else np.uint16, nt * 3, L['idx']).reshape(-1, 3).astype(int)
    nb = p['nb']
    w = sw / sw.sum(1, keepdims=True)
    dense = np.zeros((nv, nb))
    for k in range(4): np.add.at(dense, (np.arange(nv), si[:, k]), w[:, k])
    key = np.round(pos / 1e-5).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
    acc = np.zeros((inv.max() + 1, nb)); np.add.at(acc, inv, dense); dense = acc[inv] / np.bincount(inv)[inv][:, None]
    if os.environ.get('SMOOTHW', '1') != '0':
        nrm = np.frombuffer(b, np.float32, nv * 3, L['nrm']).reshape(-1, 3).astype(float)
        dense = U.final_weights(pos, nrm, idx, dense)   # smoothing + skirt-panel blend, the same as citizen_rig.build
    Mf = A[p['clips'][clip]['row'] + frame]
    def skin(P, D):
        out = np.zeros_like(P); Ph = np.c_[P, np.ones(len(P))]
        Mall = np.einsum('bij,nj->nbi', Mf, Ph)     # (n, nb, 3)
        return np.einsum('nb,nbi->ni', D, Mall)
    G = skin(pos, dense)
    T = idx
    if expand > 0:   # per-triangle expansion in bind space, skinned with the corner vertices' weights
        P3, _ = U.expand_triangles(pos, idx, np.zeros((len(pos), 2)), expand)
        Pe = P3.reshape(-1, 3); De = dense[idx.reshape(-1)]
        G = skin(Pe, De); T = np.arange(len(Pe)).reshape(-1, 3); nv = len(Pe)
    if use_hull:
        Hh = np.load(scr('eval', 'hull', name + '.npz'))
        dh = np.einsum('nk,nkb->nb', Hh['nw'], dense[Hh['nn']])
        HV = skin(Hh['V'], dh)
        T0 = T
        G = np.vstack([G, HV]); T = np.vstack([T0, Hh['T'] + len(G) - len(HV)])
    return G, T


def views_metrics(name, clip, frame, angles=(0, 45, 90, 135, 180, 225, 270, 315), img=None):
    """Single-sided (culled) coverage: see = pixels inside the filled silhouette (8 mm eroded, so silhouette-edge slivers are excluded, like
    cracks.py's eroded person mask) that no front-facing garment triangle covers = what a player sees through the cloth.
    covered = share of them the hull fills;  pokes = hull pixels farther than 6 mm from any garment pixel (a hull sticking out of the cloth)."""
    Gg, Tg = posed(name, clip, frame, False)
    Gh, Th = posed(name, clip, frame, True)
    nG = len(Gg)
    Hv, Ht = Gh[nG:], Th[len(Tg):] - nG
    see_t = cov_t = pk = 0
    rows = []
    for ang in angles:
        th = np.radians(ang); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])
        Qg = Gg @ R.T; Qh = Hv @ R.T
        org = Qg.min(0) - 0.02
        W = int((Qg[:, 0].max() - org[0]) / PX) + 20; Hh = int((Qg[:, 1].max() - org[1]) / PX) + 20
        mg = np.zeros((Hh, W), bool); mh = np.zeros((Hh, W), bool); ma = np.zeros((Hh, W), bool)
        raster(Qg, Tg, W, Hh, org, mg); raster(Qh, Ht, W, Hh, org, mh); raster(Qg, Tg, W, Hh, org, ma, cull=False)
        sil = ndimage.binary_erosion(ndimage.binary_fill_holes(ma), iterations=4)
        see = sil & ~mg
        see_t += int(see.sum()); cov_t += int((see & mh).sum())
        pk += int((mh & ~ndimage.binary_dilation(mg, structure=np.hypot(*np.meshgrid(np.arange(-3, 4), np.arange(-3, 4))) <= 3)).sum())
        if img is not None:
            im = np.zeros((Hh, W, 3), np.uint8); im[mg] = (110, 110, 110); im[see] = (0, 200, 255); im[see & mh] = (0, 255, 0)
            im[mh & ~ndimage.binary_dilation(mg, iterations=3)] = (0, 0, 255)
            rows.append(im[::-1])
    if img is not None:
        import cv2
        h = max(r.shape[0] for r in rows)
        cv2.imwrite(img, np.hstack([np.pad(r, ((0, h - r.shape[0]), (0, 10), (0, 0))) for r in rows]))
    return see_t, cov_t, pk


if __name__ == '__main__':
    a = sys.argv[1:]
    clip = 'walk'; frame = 5
    if '--clip' in a: k = a.index('--clip'); clip = a[k + 1]; a = a[:k] + a[k + 2:]
    if '--frame' in a: k = a.index('--frame'); frame = int(a[k + 1]); a = a[:k] + a[k + 2:]
    for name in a:
        thin, cov, pk = views_metrics(name, clip, frame)
        print('%-24s %s f%d: see-through %d px (interior, 8 views, 2 mm px); hull fills %.1f%%; hull px > 6 mm outside the garment: %d' % (name, clip, frame, thin, 100.0 * cov / max(1, thin), pk))
