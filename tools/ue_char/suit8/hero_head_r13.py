#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 13: SCULPT the shared hero mask head (brow ridge, eye sockets, nose bridge + tip + nostril wings, cheek bones, mouth, chin) in the UE-only hero GLB.

Critic r12: "heads are unsculpted socks with small rimless lenses" (the single biggest gap).  The browser hero mesh is an egg with ~8 mm triangles and no face
relief; the 8 suits all share this mesh, so ONE script on the hero GLB (run by build_characters.py 'prep' after hero_weights... no: BEFORE hero_lens_r13.py,
which reads the sculpted surface) gives every suit the same head.

What it does (numpy, no Blender; every vertex attribute is carried through, the UVs stay the browser atlas so the suit paint of design.py still lands on it):
  1. conforming red-green refinement of the front face zone (|x| < 0.095, 1.565 < y < 1.745, z > 0.02): two levels, ~2 mm triangles in the middle of the face
     (edge split templates, attributes interpolated: position, normal, UV, the four skin joints / weights, so no crack and no T-junction);
  2. a z-displacement field (mm) built from Gaussian features in the face frame (brow ridge + glabella, eye sockets, nose bridge / tip / alae / nostril
     undercut, cheek bones + hollows, mouth bulge + groove, chin), windowed by the surface's n_z so it fades before the silhouette (z only: the front-projected
     paint of design.py keeps its x, y);
  3. normals: n_new = normalize(n_old + (n_welded(displaced) - n_welded(undisplaced))), welded by position, so the shading is smooth and there is no seam where the
     field ends.

  python3 tools/ue_char/suit8/hero_head_r13.py <SK_Hero.glb> [--dump DIR]      (in place; run after prep_glbs.py, before hero_lens_r13.py)
  --check: prints the profile numbers (nose bump, relief) of the result.
"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import glbedit  # noqa: E402
import skinfit  # noqa: E402

ZONE = dict(xmax=0.095, y0=1.565, y1=1.745, zmin=0.02)       # refinement zone (centroid test) of level 1
LEVELS = 2


# ------------------------------------------------------------------------------------------------ the sculpt field
def G(d, s):
    return np.exp(-0.5 * (d / s) ** 2)


def G2(x, y, cx, cy, sx, sy):
    return G(x - cx, sx) * G(y - cy, sy)


def ss(x, a, b):
    t = np.clip((x - a) / (b - a + 1e-12), 0, 1)
    return t * t * (3 - 2 * t)


NOSE_Y = np.array([1.600, 1.622, 1.634, 1.645, 1.655, 1.668, 1.680, 1.692, 1.702, 1.712])
NOSE_H = np.array([0.0,   4.5,   9.5,   14.0,  11.5,  8.5,   5.5,   3.0,   1.0,   0.0])      # mm above the base surface along the midline
NOSE_S = np.array([0.012, 0.011, 0.0105, 0.0085, 0.0075, 0.0068, 0.0062, 0.0058, 0.0056, 0.0055])    # lateral sigma (m)


def field_mm(x, y):
    """Height (mm, +z) of the sculpt at (x, y) metres in the hero rest frame (x symmetric)."""
    ax = np.abs(x)
    h = np.zeros_like(x)
    # brow ridge: a bar above the eye, arching a little toward the temple, + glabella
    yb = 1.709 - 0.014 * (ax / 0.07) ** 2
    h += 5.8 * G(y - yb, 0.0062) * (1 - ss(ax, 0.060, 0.088))
    h += 2.0 * G2(ax, y, 0.0, 1.699, 0.012, 0.007)
    # forehead above the brow: a gentle rise then back
    h += -1.6 * G(y - 1.727, 0.010) * (1 - ss(ax, 0.05, 0.085))
    # eye sockets: a broad hollow under the ridge, the lens + rim sit in it
    h += -4.2 * G2(ax, y, 0.042, 1.670, 0.026, 0.0140)
    # nose: bridge ridge (height / width as a function of y) + rounded tip + alae + undercut
    hy = np.interp(y, NOSE_Y, NOSE_H, left=0.0, right=0.0)
    sy = np.interp(y, NOSE_Y, NOSE_S)
    h += hy * G(ax, sy)
    h += 2.6 * G2(ax, y, 0.0, 1.646, 0.0085, 0.0070)
    h += 3.4 * G2(ax, y, 0.0128, 1.637, 0.0056, 0.0056)                 # alae
    h += -3.4 * G2(ax, y, 0.0, 1.6275, 0.0150, 0.0042)                  # nostril undercut / columella shadow
    h += -1.8 * G2(ax, y, 0.0, 1.617, 0.020, 0.0045)                    # philtrum hollow
    # cheek bones and the hollows below them
    h += 5.2 * G2(ax, y, 0.060, 1.658, 0.0165, 0.0125)
    h += -3.0 * G2(ax, y, 0.052, 1.622, 0.015, 0.0125)
    # mouth bulge + groove below it + chin
    h += 3.2 * G(y - 1.610, 0.0075) * G(ax, 0.030)
    h += -2.8 * G(y - 1.5965, 0.0042) * G(ax, 0.027)
    h += 6.5 * G2(ax, y, 0.0, 1.581, 0.020, 0.0105)
    return h


# ------------------------------------------------------------------------------------------------ refinement
def _mid_attrs(P, N, UV, J, W, a, b):
    p = 0.5 * (P[a] + P[b]); n = N[a] + N[b]; n = n / (np.linalg.norm(n) + 1e-12); uv = 0.5 * (UV[a] + UV[b])
    d = {}
    for jj, ww in zip(J[a], W[a]): d[int(jj)] = d.get(int(jj), 0.0) + 0.5 * float(ww)
    for jj, ww in zip(J[b], W[b]): d[int(jj)] = d.get(int(jj), 0.0) + 0.5 * float(ww)
    top = sorted(d.items(), key=lambda kv: -kv[1])[:4]
    jj = [t[0] for t in top] + [0] * (4 - len(top)); ww = [t[1] for t in top] + [0.0] * (4 - len(top))
    s = sum(ww) + 1e-12
    return p, n, uv, jj, [w / s for w in ww]


def refine(P, N, UV, J, W, F, sel):
    """Split every edge of the triangles in `sel` (bool per triangle) at its midpoint; conforming templates for 1 / 2 / 3 split edges per triangle."""
    marked = {}
    for t in np.nonzero(sel)[0]:
        for k in range(3):
            a, b = int(F[t, k]), int(F[t, (k + 1) % 3])
            marked[(min(a, b), max(a, b))] = -1
    keys = list(marked)
    newP, newN, newUV, newJ, newW = [], [], [], [], []
    base = len(P)
    for i, (a, b) in enumerate(keys):
        p, n, uv, jj, ww = _mid_attrs(P, N, UV, J, W, a, b)
        marked[(a, b)] = base + i
        newP.append(p); newN.append(n); newUV.append(uv); newJ.append(jj); newW.append(ww)
    mid = lambda a, b: marked.get((min(a, b), max(a, b)), -1)
    out = []
    for t in range(len(F)):
        v = [int(F[t, 0]), int(F[t, 1]), int(F[t, 2])]
        m = [mid(v[0], v[1]), mid(v[1], v[2]), mid(v[2], v[0])]
        nm = sum(1 for q in m if q >= 0)
        if nm == 0: out.append(v); continue
        if nm == 3:
            out += [[v[0], m[0], m[2]], [m[0], v[1], m[1]], [m[2], m[1], v[2]], [m[0], m[1], m[2]]]; continue
        # rotate so the marked edges come first
        if nm == 1:
            r = [k for k in range(3) if m[k] >= 0][0]
            a, b, c = v[r], v[(r + 1) % 3], v[(r + 2) % 3]; mm = m[r]
            out += [[a, mm, c], [mm, b, c]]; continue
        r = [k for k in range(3) if m[k] < 0][0]          # the unmarked edge is e_r: rotate so it becomes e2
        s = (r + 1) % 3
        a, b, c = v[s], v[(s + 1) % 3], v[(s + 2) % 3]; m0, m1 = m[s], m[(s + 1) % 3]
        out += [[m0, b, m1], [a, m0, m1], [a, m1, c]]
    P2 = np.vstack([P, np.array(newP, np.float32)]); N2 = np.vstack([N, np.array(newN, np.float32)]); UV2 = np.vstack([UV, np.array(newUV, np.float32)])
    J2 = np.vstack([J, np.array(newJ, J.dtype)]); W2 = np.vstack([W, np.array(newW, np.float32)])
    return P2, N2, UV2, J2, W2, np.array(out, int)


def welded_normals(P, F):
    """Area-weighted vertex normals welded by position (UV-seam duplicates share one normal)."""
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    key = np.round(P.astype(np.float64) / 2e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    acc = np.zeros((inv.max() + 1, 3))
    for k in range(3): np.add.at(acc, inv[F[:, k]], fn)
    n = acc[inv]
    return (n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)).astype(np.float32)


def sculpt(P, N, UV, J, W, F):
    for lev in range(LEVELS):
        sh = 0.0 if lev == 0 else 0.004
        c = P[F].mean(1)
        sel = (np.abs(c[:, 0]) < ZONE['xmax'] - sh) & (c[:, 1] > ZONE['y0'] + sh) & (c[:, 1] < ZONE['y1'] - sh) & (c[:, 2] > ZONE['zmin'] + sh * 0.5)
        P, N, UV, J, W, F = refine(P, N, UV, J, W, F, sel)
    n0 = welded_normals(P, F)
    h = field_mm(P[:, 0].astype(np.float64), P[:, 1].astype(np.float64)) * 1e-3
    nz = np.clip(n0[:, 2], 0, 1)
    wz = ss(nz, 0.32, 0.68)
    P2 = P.copy(); P2[:, 2] += (h * wz).astype(np.float32)
    # temple / cheek-bone width: the egg is 168 mm wide at the eyes and the lenses wrap around its sides, so the head gets 6 mm wider each side at the eye level
    # (x only: tapering to 0 toward the centre line, the jaw, the crown and the back of the head).  Without it the 63 mm lenses reach the silhouette at a 12 deg view.
    ax_ = np.abs(P[:, 0].astype(np.float64))
    wx = 0.006 * ss(ax_, 0.035, 0.080) * G(P[:, 1].astype(np.float64) - 1.672, 0.030) * ss(P[:, 2].astype(np.float64), -0.06, 0.01)
    P2[:, 0] += (np.sign(P[:, 0]) * wx).astype(np.float32)
    n1 = welded_normals(P2, F)
    Nn = N + (n1 - n0)
    Nn = (Nn / (np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-12)).astype(np.float32)
    return P2, Nn, UV, J, W, F, h * wz


def body_prim(j):
    nd = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan')
    return j['meshes'][nd['mesh']]['primitives'][0]


def main(path, dump=None):
    g = glbedit.Glb(path); j = g.j
    p = body_prim(j); A = p['attributes']
    raw = bytes(g.bin)
    P = skinfit.accessor(j, raw, A['POSITION']).astype(np.float32); N = skinfit.accessor(j, raw, A['NORMAL']).astype(np.float32)
    UV = skinfit.accessor(j, raw, A['TEXCOORD_0']).astype(np.float32)
    J = skinfit.accessor(j, raw, A['JOINTS_0']).astype(np.int64)
    W = skinfit.accessor(j, raw, A['WEIGHTS_0']).astype(np.float32)
    F = skinfit.accessor(j, raw, p['indices']).reshape(-1, 3).astype(int)
    nv0, nt0 = len(P), len(F)
    P2, N2, UV2, J2, W2, F2, hd = sculpt(P, N, UV, J, W, F)
    jt = np.uint8 if J.max() < 256 else np.uint16
    Fi = F2.reshape(-1).astype(np.uint32 if len(P2) > 65535 else np.uint16)
    p['attributes'] = {'POSITION': g.add(P2.astype(np.float32), 34962, True), 'NORMAL': g.add(N2.astype(np.float32), 34962), 'TEXCOORD_0': g.add(UV2.astype(np.float32), 34962),
                       'JOINTS_0': g.add(J2.astype(jt), 34962), 'WEIGHTS_0': g.add(W2.astype(np.float32), 34962)}
    p['indices'] = g.add(Fi, 34963)
    g.save(path)
    rep = dict(vertices=[nv0, len(P2)], triangles=[nt0, len(F2)], max_displacement_mm=round(float(np.abs(hd).max() * 1e3), 2),
               nose_tip_mm=round(float(hd[(np.abs(P2[:, 0]) < 0.003) & (np.abs(P2[:, 1] - 1.645) < 0.003)].max() * 1e3), 2))
    print('hero_head_r13: ' + json.dumps(rep))
    if dump:
        os.makedirs(dump, exist_ok=True); np.savez(dump + '/head.npz', P=P2, F=F2, h=hd)
    return rep


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[sys.argv.index('--dump') + 1] if '--dump' in sys.argv else None)
