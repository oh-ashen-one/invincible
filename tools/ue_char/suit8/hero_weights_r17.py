#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17: two skin-weight discontinuities behind the r16 critic's remaining 4K defects (found on the CPU, posed render of the prepped GLB in the idle clip).

(1) TORSO FRONT / BACK: the browser mesh's raw spine weights jump across a vertical strip at |x| 0.03 - 0.05 (y 1.19 - 1.26): the sternum column carries spine1 0.37 - 0.53, the
    pec panels next to it spine2 0.76 - 0.89 and no spine1 (hero_weights_r17.py --report prints the rows).  spine1 and spine2 move apart a little in the idle clip, so every sash edge
    / groove cord that crosses the strip steps sideways there: the Ash sash edge shelf (~34 px, x 2340 - 2420 of the chest still), the Verdant rib cord step where it crosses the
    chest stripe (x ~2380, 9 px).  Cure (like rounds 12 / 14): inside |x| < 0.20, 0.97 < y < 1.46 every vertex's weight vector becomes a Gaussian average over its same-facing 3D
    neighbours (island gaps are bridged: the neighbours are found in 3D, not on the mesh), blended in by a ramp that is 0 at the armpit smoothing's edge and at the trapezius band.
(2) HEAD / NECK: the face was weighted to the neck up to y 1.66 (neck 0.18 at the chin line, 0.10 at the mouth, 0.03 at the eyes), and the neck -> head transition happened inside 1 cm at the
    chin line (head mean 0.28 -> 0.75 between y 1.53 and 1.54).  The idle clip turns the head against the neck by a few degrees: the face seam bent along the whole face (dev100 10.9 on Cinder)
    and broke with a ~30 px step where the head-weighted cord meets the neck-weighted throat cord (Cinder chin, critic r16: "~120 px").  Now: the whole head / face above y 1.56 follows
    the head bone ONLY (neck weight -> head), and the head <-> neck blend of the head + neck mass is a smooth ramp over y 1.40 .. 1.56 (the shear is spread over 16 cm of throat, not 1 cm; CPU seam3d: max step slope 0.66 -> 0.11 mm/mm, face seam exactly straight in the head plane).

Runs AFTER hero_weights_r16.py (prep_hero_r17.sh).  Positions, normals, UVs and the suit paint are untouched.
  python3 tools/ue_char/suit8/hero_weights_r17.py <SK_Hero.glb>          (in place)
  python3 tools/ue_char/suit8/hero_weights_r17.py --report <SK_Hero.glb>  (weight rows across the sternum strip and the head / neck blend, no write)
"""
import sys, os, json, struct
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit  # noqa: E402
import hero_weights_r12 as hw  # noqa: E402
import hero_weights_r16 as h16  # noqa: E402

RADIUS = 0.030
ITERS = 10
AX0, AX1 = 0.100, 0.150          # |x| ramp: fully smoothed inside AX0, none beyond AX1 (the armpit region |x| 0.15 - 0.20 keeps its round-16 weights)
Y0, Y1, Y2, Y3 = 0.97, 1.00, 1.415, 1.455      # y ramp: in from Y0 to Y1, out from Y2 to Y3 (the trapezius band y > 1.38 has its own smoothing)
HEAD_Y0, HEAD_Y1 = 1.40, 1.56   # head <-> neck blend of the head + neck mass; above HEAD_Y1 the head bone takes all of it


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def torso_ramp(P):
    ax = np.abs(P[:, 0]); y = P[:, 1]
    rx = 1.0 - smoothstep((ax - AX0) / (AX1 - AX0))
    ry = smoothstep((y - Y0) / (Y1 - Y0)) * (1.0 - smoothstep((y - Y2) / (Y3 - Y2)))
    return rx * ry


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
    return cur


def head_neck(P, dense, names):
    """Head + neck mass: above HEAD_Y1 all of it on the head bone; between HEAD_Y0 and HEAD_Y1 a smooth blend (position based, so the two copies of a seam vertex agree)."""
    ni = names.index('neck'); hi = names.index('head')
    out = dense.copy()
    m = out[:, ni] + out[:, hi]
    # only vertices that belong to the head / throat: head + neck mass >= 0.3 and above the blend start
    sel = (m >= 0.30) & (P[:, 1] > HEAD_Y0)
    t = smoothstep((P[:, 1] - HEAD_Y0) / (HEAD_Y1 - HEAD_Y0))
    th = np.where(sel, np.maximum(out[:, hi] / np.maximum(m, 1e-9), t), out[:, hi] / np.maximum(m, 1e-9))     # never LESS head than before
    out[sel, hi] = (m * th)[sel]
    out[sel, ni] = (m * (1.0 - th))[sel]
    return out


def process(P, N, dense, names):
    ramp = torso_ramp(P)
    cur = smooth_ramp(P, N, dense, ramp)
    cur = head_neck(P, cur, names)
    h16.install(names)
    return h16.top4_merge(cur), ramp


def rewrite(path):
    d = bytearray(open(path, 'rb').read())
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(bytes(d[20:20 + jl]))
    b0 = 28 + jl
    bl = struct.unpack('<I', d[20 + jl:24 + jl])[0]
    buf = d[b0:b0 + bl]
    p = hw.body_prim(j); A = p['attributes']
    b = bytes(buf)
    P = skinfit.accessor(j, b, A['POSITION']).astype(np.float64); N = skinfit.accessor(j, b, A['NORMAL']).astype(np.float64)
    J = skinfit.accessor(j, b, A['JOINTS_0']).astype(int); W = skinfit.accessor(j, b, A['WEIGHTS_0'])
    names = [j['nodes'][i].get('name') for i in j['skins'][0]['joints']]
    dense = hw.dense_of(J, W, len(names))
    new, ramp = process(P, N, dense, names)
    Jn, Wn = hw.to_jw(new)
    hw.write_acc(buf, j, A['JOINTS_0'], Jn)
    hw.write_acc(buf, j, A['WEIGHTS_0'], Wn)
    d[b0:b0 + bl] = buf
    open(path + '.tmp', 'wb').write(bytes(d)); os.replace(path + '.tmp', path)
    print('hero_weights_r17: %s: torso smoothing %d vertices (%d fully), head / neck blend y %.2f - %.2f, max weight change %.3f'
          % (path, int((ramp > 0).sum()), int((ramp > 0.99).sum()), HEAD_Y0, HEAD_Y1, float(np.abs(new - dense).max())))


def report(path):
    import glbedit, hero_shoulder_r14 as HS, meshio
    g = glbedit.Glb(path); _, P, N, UV, J, W, F = HS.read_body(g)
    names = meshio.load_body()['names']; P = P.astype(float)
    for y0 in (1.22, 1.26):
        sel = np.where((np.abs(P[:, 1] - y0) < 0.0015) & (P[:, 2] > -0.02) & (np.abs(P[:, 0]) < 0.25))[0]
        sel = sel[np.argsort(P[sel, 0])]
        print('y', y0)
        for v in sel[::2]:
            w = sorted([(names[J[v][q]], round(float(W[v][q]), 2)) for q in range(4) if W[v][q] > 0.02], key=lambda t: -t[1])
            print('  x %.3f' % P[v, 0], w)


if __name__ == '__main__':
    if sys.argv[1] == '--report':
        report(sys.argv[2])
    else:
        rewrite(sys.argv[1])
