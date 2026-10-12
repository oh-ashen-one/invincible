#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 12: verify a suit's derived normal map against the hero mesh's tangent basis, per UV island.

For texels on relief (|grad h| large) the tangent-space normal of <id>_normal.png is decoded with the MikkTSpace-style frame Unreal builds
(T = d P / d u orthogonalised to N, B = sign * N x T with the sign from the UV winding, OpenGL map -> green flipped on import) and compared with the
normal expected from the 3D gradient of the height field itself (finite differences of the painted height between neighbouring texels mapped to
their rest-pose 3D positions, so this check does NOT reuse normal_from_height's own UV-space maths).  Per island: median cosine between the two
perturbation directions, median magnitude ratio, mirrored or not.  A wrong sign on any island (cos < 0) = the island would light upside down.

  python3 tools/ue_char/suits/tangent_check.py <maps dir> <id> <heights.npy|-> OUT.json      (heights: the painted height in mm; '-' re-paints at the map size)
"""
import sys, os, json
import numpy as np
import cv2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'suit8'))
import meshio, design  # noqa: E402
import hero_suit_r8 as hs  # noqa: E402


def main():
    mdir, sid, hpath, outp = sys.argv[1:5]
    nm = cv2.imread('%s/%s_normal.png' % (mdir, sid))[..., ::-1].astype(np.float32) / 255 * 2 - 1
    n = nm.shape[0]
    m = meshio.load_body(); P, N, UV, F = m['P'], m['N'], m['UV'], m['F']
    tri, w0, w1, inside = meshio.raster_tri(UV, F, n)
    if hpath == '-':
        suits = json.load(open(os.path.join(HERE, 'suits.json')))['suits']
        st = next((e.get('style') for e in suits if e['id'] == sid), None)
        r = hs.build(n, log=lambda *a: None, style=design.resolve(st), pre=(m, (tri, w0, w1, inside)))
        h = r['h']
    else:
        h = np.load(hpath)
    # UV islands
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    nc, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(P), len(P))), directed=False)
    face_island = lab[F[:, 0]]
    # per-face exact frame: dP/du, dP/dv_up (v_up = -row = -glTF v)
    p0, p1, p2 = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    t0, t1, t2 = UV[F[:, 0]], UV[F[:, 1]], UV[F[:, 2]]
    e1, e2 = p1 - p0, p2 - p0; d1, d2 = t1 - t0, t2 - t0
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    r_ = 1.0 / np.where(np.abs(det) < 1e-12, 1e-12, det)
    dPdu = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * r_[:, None]
    dPdv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) * r_[:, None]          # d P / d (glTF v, i.e. row direction)
    fn = np.cross(e1, e2); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    # texels with relief: interior of a triangle and both +col / +row neighbours in the same triangle
    gy, gx = np.gradient(h)
    cand = (tri >= 0) & inside & (np.hypot(gx, gy) > 0.05)
    cand[:, -1] = False; cand[-1, :] = False
    same = cand & (tri == np.roll(tri, -1, 1)) & (tri == np.roll(tri, -1, 0))
    ys, xs = np.nonzero(same)
    if len(ys) > 400000:
        k = np.random.RandomState(0).choice(len(ys), 400000, replace=False); ys, xs = ys[k], xs[k]
    f = tri[ys, xs]
    def pos(yy, xx):
        ff = tri[yy, xx]; a = w0[yy, xx][:, None]; b = w1[yy, xx][:, None]
        return a * P[F[ff, 0]] + b * P[F[ff, 1]] + (1 - a - b) * P[F[ff, 2]]
    X0 = pos(ys, xs); Xu = pos(ys, xs + 1); Xv = pos(ys + 1, xs)
    hu = (h[ys, xs + 1] - h[ys, xs]) * 1e-3; hv = (h[ys + 1, xs] - h[ys, xs]) * 1e-3
    a_ = Xu - X0; b_ = Xv - X0
    # world gradient g in span(a, b) with g.a = hu, g.b = hv
    G = np.stack([np.einsum('ij,ij->i', a_, a_), np.einsum('ij,ij->i', a_, b_), np.einsum('ij,ij->i', b_, b_)], 1)
    detG = G[:, 0] * G[:, 2] - G[:, 1] ** 2
    ok = detG > 1e-24
    ca = (hu * G[:, 2] - hv * G[:, 1]) / np.where(ok, detG, 1); cb = (hv * G[:, 0] - hu * G[:, 1]) / np.where(ok, detG, 1)
    g = ca[:, None] * a_ + cb[:, None] * b_
    # the map, decoded with a MikkTSpace-style frame
    Nn = fn[f]
    T = dPdu[f] - Nn * np.einsum('ij,ij->i', dPdu[f], Nn)[:, None]; T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    vup = -dPdv[f]
    sign = np.sign(np.einsum('ij,ij->i', np.cross(Nn, T), vup)); sign[sign == 0] = 1
    B = sign[:, None] * np.cross(Nn, T)
    ts = nm[ys, xs]
    pert_map = ts[:, 0:1] * T + ts[:, 1:2] * B                       # tangential part of the decoded normal
    pert_exp = -g                                                    # expected: n ~ N - grad h
    c = np.einsum('ij,ij->i', pert_map, pert_exp) / (np.linalg.norm(pert_map, axis=1) * np.linalg.norm(pert_exp, axis=1) + 1e-12)
    mag = np.linalg.norm(pert_map, axis=1) / (np.linalg.norm(pert_exp, axis=1) / np.sqrt(1 + np.linalg.norm(pert_exp, axis=1) ** 2) + 1e-12)
    strong = ok & (np.linalg.norm(pert_exp, axis=1) > 0.05)
    isl = face_island[f]
    rows = []
    for i in range(nc):
        s = strong & (isl == i)
        if s.sum() < 50: continue
        fi = np.unique(f[s])
        rows.append(dict(island=int(i), texels=int(s.sum()), mirrored=bool((sign[s] < 0).mean() > 0.5), cos_median=round(float(np.median(c[s])), 3),
                         cos_p10=round(float(np.percentile(c[s], 10)), 3), wrong_sign_pct=round(float((c[s] < 0).mean() * 100), 2),
                         mag_ratio_median=round(float(np.median(mag[s])), 3)))
    res = dict(suit=sid, size=n, islands=nc, checked=len(rows), texels=int(strong.sum()), cos_median_all=round(float(np.median(c[strong])), 3),
               worst_island_cos_median=min(r['cos_median'] for r in rows), max_wrong_sign_pct=max(r['wrong_sign_pct'] for r in rows),
               # PASS: no island lights the wrong way (median cosine > 0.5 everywhere) and every large island (>= 2000 relief texels: torso, limbs, head) agrees
               # to cos >= 0.9; the four finger islands (a few hundred texels on 1-2 cm cylinders) are reported, the finite differences are coarse there
               verdict='PASS' if (min(r['cos_median'] for r in rows) > 0.5 and min([r['cos_median'] for r in rows if r['texels'] >= 2000] or [1]) >= 0.9) else 'FAIL',
               large_island_min_cos=min([r['cos_median'] for r in rows if r['texels'] >= 2000] or [1]), per_island=rows)
    json.dump(res, open(outp, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'per_island'}))


if __name__ == '__main__':
    main()
