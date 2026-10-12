#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14: smooth the hero's skin weights on the TRAPEZIUS / neck-shoulder junction (on top of round 12's torso-side / armpit smoothing, which this script applies first).

Critic r13 (image quality): "the Sage trapezius groove is torn (head34)"; the Ash / Cinder chest stills show the same dark creases at the clavicle - the neck, spine2, shoulder and
deltoid bones all weigh in on the trapezius with DIFFERENT mixtures on neighbouring vertices (1 390 vertices, 450 of them with 3 - 4 influences >= 0.1), so in the idle / run poses
the surface folds along the rows where the dominant bone changes.  Same cure as round 12 (hero_weights_r12.py): inside the region (rest pose y 1.38 .. 1.57, |x| 0.025 .. 0.26 with a mix
of neck / spine2 / shoulder / deltoid weights) every vertex's per-joint weight vector is replaced by a Gaussian average over its same-facing 3D neighbours (radius 2.4 cm), blended in
with a ramp so the region has no edge; the four largest influences are kept and renormalised.  Positions, normals, UVs and the suit paint are untouched.

  python3 tools/ue_char/suit8/hero_weights_r14.py <SK_Hero.glb>          (in place; run after hero_shoulder_r14.py: it reads whatever body primitive the GLB has)
  python3 tools/ue_char/suit8/hero_weights_r14.py --check [out.json]     (CPU: folded-face counts in the trapezius region, r12 weights vs r14 weights, idle + run + sprint + fight idle)
"""
import sys, os, json, struct
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit  # noqa: E402
import hero_weights_r12 as hw  # noqa: E402

RADIUS = 0.024
ITERS = 10
Y0, Y1, AX0, AX1 = 1.38, 1.57, 0.025, 0.26


def grp(names, dense, prefixes):
    idx = [k for k, n in enumerate(names) if n.split('.')[0] in prefixes]
    return dense[:, idx].sum(1)


def trap_ramp(P, dense, names):
    """0..1 weight of the smoothing per vertex.  The core = the vertices of the trapezius band whose weights are MIXED (>= 2 of neck / spine2 / shoulder-deltoid >= 0.08)."""
    neck = grp(names, dense, ('neck',)); sp = grp(names, dense, ('spine2', 'spine1')); sh = grp(names, dense, ('shoulder', 'deltoid', 'upperArm'))
    y = P[:, 1]; ax = np.abs(P[:, 0])
    n_mix = (neck >= 0.08).astype(int) + (sp >= 0.08).astype(int) + (sh >= 0.08).astype(int)
    core = (n_mix >= 2) & (y > Y0) & (y < Y1) & (ax > AX0) & (ax < AX1)
    if not core.any(): return np.zeros(len(P))
    dist, _ = cKDTree(P[core]).query(P, k=1)
    ramp = np.clip(1.0 - dist / 0.026, 0, 1)
    return ramp * ramp * (3 - 2 * ramp)


def smooth_ramp(P, N, dense, ramp, radius=RADIUS, iters=ITERS):
    act = ramp > 0
    pr = cKDTree(P).query_pairs(radius, output_type='ndarray')
    i, j = pr[:, 0], pr[:, 1]
    keep = (np.einsum('ij,ij->i', N[i], N[j]) > 0.2) & (act[i] | act[j])
    i, j = i[keep], j[keep]
    d = np.linalg.norm(P[i] - P[j], axis=1)
    w = np.exp(-(d / (radius * 0.6)) ** 2)[:, None]
    cur = dense.copy()
    for _ in range(iters):
        acc = cur.copy(); ws = np.ones((len(P), 1))
        np.add.at(acc, i, w * cur[j]); np.add.at(acc, j, w * cur[i])
        np.add.at(ws, i, w); np.add.at(ws, j, w)
        cur = cur + (acc / ws - cur) * ramp[:, None]
    return hw.top4(cur)


def smooth_all(P, N, dense, names):
    """round 12 armpit smoothing, then the round 14 trapezius smoothing (its region is found on the weights the first pass returns)."""
    d12, ramp12 = hw.smooth_weights(P, N, dense, names)
    r14 = trap_ramp(P, d12, names)
    d14 = smooth_ramp(P, N, d12, r14)
    return d14, ramp12, r14


def rewrite(path):
    d = bytearray(open(path, 'rb').read())
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(bytes(d[20:20 + jl]))
    b0 = 28 + jl
    bl = struct.unpack('<I', d[20 + jl:24 + jl])[0]
    buf = d[b0:b0 + bl]
    p = hw.body_prim(j); A = p['attributes']
    b = bytes(buf)
    P = skinfit.accessor(j, b, A['POSITION']); N = skinfit.accessor(j, b, A['NORMAL'])
    J = skinfit.accessor(j, b, A['JOINTS_0']).astype(int); W = skinfit.accessor(j, b, A['WEIGHTS_0'])
    names = [j['nodes'][i].get('name') for i in j['skins'][0]['joints']]
    dense = hw.dense_of(J, W, len(names))
    new, r12, r14 = smooth_all(P, N, dense, names)
    Jn, Wn = hw.to_jw(new)
    hw.write_acc(buf, j, A['JOINTS_0'], Jn)
    hw.write_acc(buf, j, A['WEIGHTS_0'], Wn)
    d[b0:b0 + bl] = buf
    open(path + '.tmp', 'wb').write(bytes(d)); os.replace(path + '.tmp', path)
    print('hero_weights_r14: %s: armpit region %d vertices (r12), trapezius region %d vertices (%d fully smoothed), max weight change %.3f'
          % (path, int((r12 > 0).sum()), int((r14 > 0).sum()), int((r14 > 0.99).sum()), float(np.abs(new - dense).max())))


def check(glb=None):
    """CPU: folded faces (posed face normal vs posed vertex normals, dot < 0.3) in the trapezius region, per weight set, for idle / run / sprint / fight idle."""
    sys.path.insert(0, os.path.join(HERE, '..', 'heroanim'))
    import meshio, ganim
    if glb:
        import glbedit, hero_shoulder_r14 as HS
        g = glbedit.Glb(glb); _, P, N, UV, J, W, F = HS.read_body(g)
        P = P.astype(np.float64); N = N.astype(np.float64)
        names = meshio.load_body()['names']
        dense = hw.dense_of(J, W, len(names))
    else:
        m = meshio.load_body()
        P, N, F = m['P'].astype(np.float64), m['N'].astype(np.float64), m['F']
        names = m['names']; dense = hw.dense_of(m['J'], m['W'], len(names))
    d12, _ = hw.smooth_weights(P, N, dense, names)
    d14, _, r14 = smooth_all(P, N, dense, names)
    doc = ganim.Doc(meshio.GLB)
    j, b = skinfit.read_glb(meshio.GLB)
    sk = j['skins'][0]; ibm = skinfit.accessor(j, b, sk['inverseBindMatrices']).reshape(-1, 4, 4)
    Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
    zone = (r14[F].max(1) > 0)
    res = {}
    for clip, ts in (('idle', (0.0, 1.0, 2.2)), ('run', (0.0, 0.1, 0.2, 0.3)), ('sprint', (0.0, 0.15)), ('fightIdle', (0.0,))):
        tr = doc.tracks(clip)
        for t in ts:
            Wd = doc.world(doc.sample(tr, t))
            M = np.stack([Wd[n] @ ibm[k].T for k, n in enumerate(sk['joints'])])
            row = []
            for wts in (dense, d12, d14):
                X = np.einsum('vj,jab,vb->va', wts, M, Ph)[:, :3]
                Nn = np.einsum('vj,jab,vb->va', wts, M[:, :3, :3], N); Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
                fn = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
                vn = Nn[F].mean(1); vn /= np.linalg.norm(vn, axis=1, keepdims=True)
                dots = (fn * vn).sum(1)
                row.append(dict(folded=int(((dots < 0.3) & zone).sum()), bent=int(((dots < 0.8) & zone).sum()), min_dot=round(float(dots[zone].min()), 3)))
            res['%s@%.2f' % (clip, t)] = dict(original=row[0], r12=row[1], r14=row[2])
    out = dict(region_vertices=int((r14 > 0).sum()), region_faces=int(zone.sum()), poses=res)
    print(json.dumps(out, indent=1))
    return out


if __name__ == '__main__':
    if '--check' in sys.argv:
        args = [a for a in sys.argv[2:] if not a.endswith('.json')]
        o = check(args[0] if args else None)
        if sys.argv[-1].endswith('.json'): json.dump(o, open(sys.argv[-1], 'w'), indent=1)
    else:
        rewrite(sys.argv[1])
