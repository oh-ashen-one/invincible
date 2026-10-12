#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 12: smooth the hero's skin weights on the side of the torso / armpit so the idle and run poses no longer FOLD there.

Diagnosis (round 12, docs/night1/characters/round-12/FOLD.md): the browser mesh gives neighbouring torso-side vertices small weights on DIFFERENT
arm bones (e.g. rest (-0.136, 1.240, 0.027) torso 0.88 + shoulder 0.12 next to (-0.151, 1.229, -0.019) torso 0.89 + upperArm 0.11).  With the arms down
(idle, run) the upperArm-weighted row moves ~12 mm inward while its shoulder-weighted neighbours stay: the surface folds into a step along that row.
That fold is the 24 px Verdant chevron jog, the Tessera / Cinder sash-border stair-step at the armpit, the "weave flip" line and the faceted
polygon shade patches (folded triangles) the critic saw on Ash / Tessera.  The suit TEXTURES are continuous across that UV seam (seam probe).

Fix: inside the torso-side region (rest pose, torso weight >= 0.45 with some shoulder / upperArm weight, 0.98 < y < 1.46) every vertex's per-joint weight
vector is replaced by a Gaussian average over its 3D neighbours (same-facing only), blended in with a smooth ramp so the region has no edge; then the
four largest influences are kept and renormalised.  Positions, normals, UVs and the suit paint (which reads public/assets/spiderman.glb) are untouched.

  python3 tools/ue_char/suit8/hero_weights_r12.py <SK_Hero.glb>          (in place; run after prep_glbs.py + hero_lens_r8.py)
  python3 tools/ue_char/suit8/hero_weights_r12.py --check                 (fold count, original vs smoothed, idle + run frames; CPU only)
"""
import sys, os, json, struct
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit  # noqa: E402

RADIUS = 0.030      # metres: Gaussian neighbourhood of the smoothing
ITERS = 8


def region_ramp(P, dense, names):
    """0..1 weight of the smoothing per vertex (1 = fully smoothed)."""
    def grp(prefixes):
        idx = [k for k, n in enumerate(names) if n.split('.')[0] in prefixes]
        return dense[:, idx].sum(1)
    torso = grp(('hips', 'glute', 'spine', 'spine1', 'spine2'))
    armish = grp(('shoulder', 'deltoid', 'upperArm'))
    y = P[:, 1]; ax = np.abs(P[:, 0])
    core = (torso >= 0.45) & (armish >= 0.004) & (y > 0.98) & (y < 1.46) & (ax > 0.06)
    tree = cKDTree(P)
    d, _ = tree.query(P, k=1, distance_upper_bound=np.inf) if False else (None, None)
    # distance from every vertex to the core set -> ramp 1 inside, 0 beyond 3 cm
    ct = cKDTree(P[core]) if core.any() else None
    if ct is None: return np.zeros(len(P))
    dist, _ = ct.query(P, k=1)
    ramp = np.clip(1.0 - dist / 0.030, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)
    return ramp


def strip_arm(P, dense, names):
    """Below the armpit the side of the chest follows the SPINE only: the shoulder / deltoid / upperArm weights of torso-side vertices fade out from
    y = 1.36 (armpit, kept) to y = 1.25 (removed), the removed weight goes to the vertex's torso bones (round 12: smoothing alone moved the fold inward)."""
    arm = np.array([n.split('.')[0] in ('shoulder', 'deltoid', 'upperArm') for n in names])
    tor = np.array([n.split('.')[0] in ('hips', 'glute', 'spine', 'spine1', 'spine2') for n in names])
    ts = dense[:, tor].sum(1); y = P[:, 1]; ax = np.abs(P[:, 0])
    t = np.clip((y - 1.25) / (1.36 - 1.25), 0, 1); keep = t * t * (3 - 2 * t)
    sel = (ts >= 0.45) & (y > 0.98) & (y < 1.36) & (ax > 0.05) & (ax < 0.26)
    out = dense.copy()
    rem = out[sel][:, arm].sum(1) * (1 - keep[sel])
    out_sel = out[sel]
    out_sel[:, arm] *= keep[sel][:, None]
    tw = out_sel[:, tor]; tw = tw / np.maximum(tw.sum(1, keepdims=True), 1e-9)
    out_sel[:, tor] += tw * rem[:, None]
    out[sel] = out_sel
    return out


def smooth_weights(P, N, dense, names, radius=RADIUS, iters=ITERS):
    ramp = region_ramp(P, dense, names)          # the region is found on the ORIGINAL weights
    dense = strip_arm(P, dense, names)
    act = ramp > 0
    tree = cKDTree(P)
    pr = tree.query_pairs(radius, output_type='ndarray')
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
        sm = acc / ws
        cur = cur + (sm - cur) * ramp[:, None]          # only the region moves; outside it the weights stay exactly as they were
    return top4(cur), ramp


def top4(dense):
    out = np.zeros_like(dense)
    idx = np.argsort(-dense, axis=1)[:, :4]
    rows = np.arange(len(dense))[:, None]
    out[rows, idx] = dense[rows, idx]
    out /= out.sum(1, keepdims=True) + 1e-12
    return out


def to_jw(dense):
    idx = np.argsort(-dense, axis=1)[:, :4]
    rows = np.arange(len(dense))[:, None]
    return idx, dense[rows, idx]


def body_prim(j):
    nd = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan')
    return j['meshes'][nd['mesh']]['primitives'][0]


def dense_of(J, W, nj):
    dense = np.zeros((len(J), nj))
    for k in range(J.shape[1]):
        np.add.at(dense, (np.arange(len(J)), J[:, k].astype(int)), W[:, k])
    return dense


def write_acc(buf, j, ai, arr):
    a = j['accessors'][ai]; bv = j['bufferViews'][a['bufferView']]
    dt = skinfit.CT[a['componentType']]; n = skinfit.NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    item = n * np.dtype(dt).itemsize; stride = bv.get('byteStride', item)
    if a.get('normalized') and dt != np.float32:
        mx = np.iinfo(dt).max
        q = np.floor(arr * mx + 0.5).astype(np.int64)
        # fix rounding so every row sums to exactly mx (the largest weight takes the remainder)
        q[np.arange(len(q)), np.argmax(q, 1)] += mx - q.sum(1)
        v = q.astype(dt)
    else:
        v = arr.astype(dt)
    raw = v.tobytes()
    for r in range(a['count']):
        buf[off + r * stride: off + r * stride + item] = raw[r * item:(r + 1) * item]


def rewrite(path):
    d = bytearray(open(path, 'rb').read())
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(bytes(d[20:20 + jl]))
    b0 = 28 + jl
    bl = struct.unpack('<I', d[20 + jl:24 + jl])[0]
    buf = d[b0:b0 + bl]
    p = body_prim(j); A = p['attributes']
    b = bytes(buf)
    P = skinfit.accessor(j, b, A['POSITION']); N = skinfit.accessor(j, b, A['NORMAL'])
    J = skinfit.accessor(j, b, A['JOINTS_0']).astype(int); W = skinfit.accessor(j, b, A['WEIGHTS_0'])
    names = [j['nodes'][i].get('name') for i in j['skins'][0]['joints']]
    dense = dense_of(J, W, len(names))
    new, ramp = smooth_weights(P, N, dense, names)
    Jn, Wn = to_jw(new)
    write_acc(buf, j, A['JOINTS_0'], Jn)
    write_acc(buf, j, A['WEIGHTS_0'], Wn)
    d[b0:b0 + bl] = buf
    open(path + '.tmp', 'wb').write(bytes(d)); os.replace(path + '.tmp', path)
    print('hero_weights_r12: %s: %d vertices in the smoothing region (ramp > 0), %d fully smoothed, max weight change %.3f'
          % (path, int((ramp > 0).sum()), int((ramp > 0.99).sum()), float(np.abs(new - dense).max())))


def check():
    """CPU: count folded faces (posed face normal vs posed vertex normals) in the torso-side region, original vs smoothed weights."""
    sys.path.insert(0, os.path.join(HERE, '..', 'heroanim'))
    import meshio, ganim
    m = meshio.load_body()
    P, N, F = m['P'].astype(np.float64), m['N'].astype(np.float64), m['F']
    names = m['names']
    dense = dense_of(m['J'], m['W'], len(names))
    new, ramp = smooth_weights(P, N, dense, names)
    doc = ganim.Doc(meshio.GLB)
    j, b = skinfit.read_glb(meshio.GLB)
    sk = j['skins'][0]; ibm = skinfit.accessor(j, b, sk['inverseBindMatrices']).reshape(-1, 4, 4)
    Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
    zone = (ramp[F].max(1) > 0)
    res = {}
    for clip, ts in (('idle', (0.0, 1.0)), ('run', (0.0, 0.1, 0.2, 0.3)), ('sprint', (0.0, 0.15)), ('fightIdle', (0.0,))):
        tr = doc.tracks(clip)
        for t in ts:
            Wd = doc.world(doc.sample(tr, t))
            M = np.stack([Wd[n] @ ibm[k].T for k, n in enumerate(sk['joints'])])
            row = []
            for wts in (dense, new):
                X = np.einsum('vj,jab,vb->va', wts, M, Ph)[:, :3]
                Nn = np.einsum('vj,jab,vb->va', wts, M[:, :3, :3], N); Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
                fn = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
                vn = Nn[F].mean(1); vn /= np.linalg.norm(vn, axis=1, keepdims=True)
                dots = (fn * vn).sum(1)
                row.append(dict(folded=int(((dots < 0.3) & zone).sum()), bent=int(((dots < 0.8) & zone).sum()), min_dot=round(float(dots[zone].min()), 3)))
            res['%s@%.2f' % (clip, t)] = dict(original=row[0], smoothed=row[1])
    out = dict(region_vertices=int((ramp > 0).sum()), region_faces=int(zone.sum()), max_weight_change=round(float(np.abs(new - dense).max()), 3), poses=res)
    print(json.dumps(out, indent=1))
    return out


if __name__ == '__main__':
    if '--check' in sys.argv:
        o = check()
        if len(sys.argv) > 2 and sys.argv[-1].endswith('.json'): json.dump(o, open(sys.argv[-1], 'w'), indent=1)
    else:
        rewrite(sys.argv[1])
