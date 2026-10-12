#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14 (numbers of round 15 in PARAMS: a deeper eye socket, a stronger brow so the lens RIM sits >= 1 % of the head height behind the brow in the 4K headside stills of the posed head): FINISH the shared mask sculpt of the hero head (brow ridge that overhangs the lens, a nose-bridge recess, cheek-bone planes, mouth bulge, chin plane)
in the UE-only hero GLB.  Run by build_characters.py 'prep' (after prep_glbs.py, before hero_lens_r14.py, which seats the lenses in the eye sockets this script cuts).

Critic r13 (hero 6): "no brow ridge, no nose-bridge recess (the profile edge rises from y=860 to 1140) and no cheekbones or mouth".  The r13 sculpt had the
features but their amplitudes were smaller than the egg's own curvature (the browser mesh is a vertical face plane at z ~ 100 mm from the chin to the brow, falling away
above 1.71 m), so the profile was a straight slope brow -> nose tip.  Round 14 targets the three critic tests on the SILHOUETTE and the FRONT relief:
  T1  headside profile: the silhouette between the brow and the nose tip dips >= 1.5 % of the head height behind the brow -> nose-tip chord (a nasion notch)
  T2  the brow's front-most point is >= 1 % of the head height in front of the top of the lens + rim (the rim and lens sit in a socket UNDER the brow ridge)
  T3  a horizontal luma line through the cheek bones has >= 3 extrema (swing >= 20): cheek-bone planes, hollows, nose flanks, alae
(measured on the mesh by tools/ue_char/suits/head_profile_r14.py before the engine hold, on the 4K stills by head_check_r14.py).

What it does (numpy, no Blender; every vertex attribute is carried through, the UVs stay the browser atlas so the suit paint of design.py still lands on it):
  1. conforming red-green refinement of the front face zone (|x| < 0.095, 1.545 < y < 1.745, z > 0.02): two levels, ~2 mm triangles in the middle of the face
     (edge split templates, attributes interpolated: position, normal, UV, the four skin joints / weights, so no crack and no T-junction);
  2. a z-displacement field (mm) built from Gaussian features in the face frame, windowed by the surface's n_z so it fades before the silhouette (z only: the
     front-projected paint of design.py keeps its x, y);
  3. normals: n_new = normalize(n_old + (n_welded(displaced) - n_welded(undisplaced))), welded by position, so the shading is smooth and there is no seam where the field ends.

  python3 tools/ue_char/suit8/hero_head_r14.py <SK_Hero.glb> [--dump DIR]      (in place; run after prep_glbs.py, before hero_lens_r14.py)
"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import glbedit  # noqa: E402
import skinfit  # noqa: E402

ZONE = dict(xmax=0.095, y0=1.545, y1=1.745, zmin=0.02)       # refinement zone (centroid test) of level 1
LEVELS = 2
WIDEN = 0.0075                                                  # m of temple / cheek-bone widening each side at the eye level (r13: 6 mm)


# ------------------------------------------------------------------------------------------------ the sculpt field
def G(d, s):
    return np.exp(-0.5 * (d / s) ** 2)


def G2(x, y, cx, cy, sx, sy):
    return G(x - cx, sx) * G(y - cy, sy)


def ss(x, a, b):
    t = np.clip((x - a) / (b - a + 1e-12), 0, 1)
    return t * t * (3 - 2 * t)


# midline nose height (mm above the base surface) and its lateral sigma, by y.  Round 14: the bridge starts BELOW the brow (nasion notch at y 1.690) and climbs to a
# longer, higher tip, so the silhouette dips behind the brow -> tip chord (the r13 ramp ran straight from the brow to the tip)
NOSE_Y = np.array([1.598, 1.616, 1.628, 1.637, 1.644, 1.652, 1.662, 1.672, 1.682, 1.690, 1.698])
NOSE_H = np.array([0.0,   4.0,   11.0,  17.0,  20.5,  17.0,  11.0,  6.0,   2.6,   0.2,   -1.0])
NOSE_S = np.array([0.012, 0.0115, 0.0105, 0.0092, 0.0080, 0.0070, 0.0062, 0.0056, 0.0052, 0.0050, 0.0055])    # lateral sigma (m)

PARAMS = dict(
    brow_amp=13.5, brow_y=1.7075, brow_sy=0.0056, brow_arch=0.0125, brow_x0=0.060, brow_x1=0.092,        # round 15: brow 11 -> 13.5 mm
    glabella=2.5,
    socket_amp=-8.8, socket_x=0.041, socket_y=1.6715, socket_sx=0.033, socket_sy=0.0165,                    # round 15: socket -5.2 -> -8.8 mm (the lens + rim sit 3.6 mm deeper under the brow)
    canthus_amp=-7.5, canthus_x=0.0125, canthus_y=1.6665, canthus_sx=0.0085, canthus_sy=0.0125,           # round 15: -5.0 -> -7.5; the inner corner of each eye: between the lens end and the nose bridge
    cheek_amp=9.0, cheek_x=0.050, cheek_y=1.6405, cheek_sx=0.0155, cheek_sy=0.0105,
    hollow_amp=-5.0, hollow_x=0.042, hollow_y=1.6195,
    temple_amp=-3.0,
    mouth_amp=6.0, groove_amp=-3.2, chin_amp=9.0,
)


def field_mm(x, y, p=None):
    """Height (mm, +z) of the sculpt at (x, y) metres in the hero rest frame (x symmetric)."""
    p = {**PARAMS, **(p or {})}
    ax = np.abs(x)
    h = np.zeros_like(x)
    # brow ridge: a shelf over each eye, arching down toward the temple, + glabella between the brows
    yb = p['brow_y'] - p['brow_arch'] * (ax / 0.07) ** 2
    h += p['brow_amp'] * G(y - yb, p['brow_sy']) * (1 - ss(ax, p['brow_x0'], p['brow_x1']))
    h += p['glabella'] * G2(ax, y, 0.0, p['brow_y'] - 0.003, 0.012, 0.007)
    # forehead above the brow: a gentle rise then back (the brow reads as a shelf), temple hollow
    h += -1.6 * G(y - 1.730, 0.010) * (1 - ss(ax, 0.05, 0.085))
    h += p['temple_amp'] * G2(ax, y, 0.078, 1.700, 0.012, 0.016)
    # eye sockets: a broad hollow under the ridge; the lens + rim sit in it (so the rim stays BEHIND the brow); the inner corner is cut deeper next to the bridge
    h += p['socket_amp'] * G2(ax, y, p['socket_x'], p['socket_y'], p['socket_sx'], p['socket_sy'])
    h += p['canthus_amp'] * G2(ax, y, p['canthus_x'], p['canthus_y'], p['canthus_sx'], p['canthus_sy'])
    # nose: bridge ridge (height / width by y) + rounded tip + alae + undercut
    hy = np.interp(y, NOSE_Y, NOSE_H, left=0.0, right=0.0)
    sy = np.interp(y, NOSE_Y, NOSE_S)
    h += hy * G(ax, sy)
    h += 2.8 * G2(ax, y, 0.0, 1.646, 0.0085, 0.0070)
    h += 4.0 * G2(ax, y, 0.0138, 1.636, 0.0058, 0.0058)                 # alae
    h += -3.6 * G2(ax, y, 0.0, 1.6255, 0.0150, 0.0042)                  # nostril undercut / columella shadow
    h += -2.0 * G2(ax, y, 0.0, 1.616, 0.020, 0.0045)                    # philtrum hollow
    # cheek bones (the zygomatic arch, a plane under the outer corner of the eye) and the hollows below them, nasolabial folds
    h += p['cheek_amp'] * G2(ax, y, p['cheek_x'], p['cheek_y'], p['cheek_sx'], p['cheek_sy'])
    h += p['hollow_amp'] * G2(ax, y, p['hollow_x'], p['hollow_y'], 0.015, 0.0115)
    h += -2.2 * G2(ax, y, 0.027, 1.627, 0.0045, 0.012)                   # nasolabial fold
    # mouth bulge + groove below it + chin plane
    h += p['mouth_amp'] * G(y - 1.611, 0.0072) * G(ax, 0.031)
    h += p['groove_amp'] * G(y - 1.5975, 0.0042) * G(ax, 0.029)
    h += p['chin_amp'] * G2(ax, y, 0.0, 1.5775, 0.021, 0.0115)
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


def sculpt(P, N, UV, J, W, F, params=None, widen=None):
    for lev in range(LEVELS):
        sh = 0.0 if lev == 0 else 0.004
        c = P[F].mean(1)
        sel = (np.abs(c[:, 0]) < ZONE['xmax'] - sh) & (c[:, 1] > ZONE['y0'] + sh) & (c[:, 1] < ZONE['y1'] - sh) & (c[:, 2] > ZONE['zmin'] + sh * 0.5)
        P, N, UV, J, W, F = refine(P, N, UV, J, W, F, sel)
    n0 = welded_normals(P, F)
    h = field_mm(P[:, 0].astype(np.float64), P[:, 1].astype(np.float64), params) * 1e-3
    nz = np.clip(n0[:, 2], 0, 1)
    wz = ss(nz, 0.32, 0.68)
    P2 = P.copy(); P2[:, 2] += (h * wz).astype(np.float32)
    # temple / cheek-bone width: the egg is 168 mm wide at the eyes and the lenses wrap around its sides, so the head gets 6 mm wider each side at the eye level
    # (x only: tapering to 0 toward the centre line, the jaw, the crown and the back of the head).  Without it the 63 mm lenses reach the silhouette at a 12 deg view.
    ax_ = np.abs(P[:, 0].astype(np.float64))
    wx = (WIDEN if widen is None else widen) * ss(ax_, 0.035, 0.080) * G(P[:, 1].astype(np.float64) - 1.672, 0.030) * ss(P[:, 2].astype(np.float64), -0.06, 0.01)
    P2[:, 0] += (np.sign(P[:, 0]) * wx).astype(np.float32)
    n1 = welded_normals(P2, F)
    Nn = N + (n1 - n0)
    Nn = (Nn / (np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-12)).astype(np.float32)
    return P2, Nn, UV, J, W, F, h * wz


def body_prim(j):
    nd = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan')
    return j['meshes'][nd['mesh']]['primitives'][0]


def main(path, dump=None, params=None, widen=None):
    g = glbedit.Glb(path); j = g.j
    p = body_prim(j); A = p['attributes']
    raw = bytes(g.bin)
    P = skinfit.accessor(j, raw, A['POSITION']).astype(np.float32); N = skinfit.accessor(j, raw, A['NORMAL']).astype(np.float32)
    UV = skinfit.accessor(j, raw, A['TEXCOORD_0']).astype(np.float32)
    J = skinfit.accessor(j, raw, A['JOINTS_0']).astype(np.int64)
    W = skinfit.accessor(j, raw, A['WEIGHTS_0']).astype(np.float32)
    F = skinfit.accessor(j, raw, p['indices']).reshape(-1, 3).astype(int)
    nv0, nt0 = len(P), len(F)
    P2, N2, UV2, J2, W2, F2, hd = sculpt(P, N, UV, J, W, F, params, widen)
    jt = np.uint8 if J.max() < 256 else np.uint16
    Fi = F2.reshape(-1).astype(np.uint32 if len(P2) > 65535 else np.uint16)
    p['attributes'] = {'POSITION': g.add(P2.astype(np.float32), 34962, True), 'NORMAL': g.add(N2.astype(np.float32), 34962), 'TEXCOORD_0': g.add(UV2.astype(np.float32), 34962),
                       'JOINTS_0': g.add(J2.astype(jt), 34962), 'WEIGHTS_0': g.add(W2.astype(np.float32), 34962)}
    p['indices'] = g.add(Fi, 34963)
    g.save(path)
    rep = dict(vertices=[nv0, len(P2)], triangles=[nt0, len(F2)], max_displacement_mm=round(float(np.abs(hd).max() * 1e3), 2),
               nose_tip_mm=round(float(hd[(np.abs(P2[:, 0]) < 0.003) & (np.abs(P2[:, 1] - 1.645) < 0.003)].max() * 1e3), 2))
    print('hero_head_r14: ' + json.dumps(rep))
    if dump:
        os.makedirs(dump, exist_ok=True); np.savez(dump + '/head.npz', P=P2, F=F2, h=hd)
    return rep


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[sys.argv.index('--dump') + 1] if '--dump' in sys.argv else None)
