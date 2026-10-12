# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08 suit tooling: the hero body mesh, its rest-pose joints and a texel rasteriser (triangle id + barycentrics per texel).

Everything is derived from public/assets/spiderman.glb (the browser game's own hero mesh and UV atlas); the ORIGINAL suit design of round 08
(tools/ue_char/suit8/design.py) is painted on top of those UVs procedurally, in rest-pose object space, so it needs no hand-drawn art.
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
from p2paths import WT  # noqa: E402
import skinfit  # noqa: E402

GLB = WT + '/public/assets/spiderman.glb'

# joint-name prefix -> part group used by the design (weights are summed per group)
GROUPS = ['head', 'torso', 'shoulder', 'armU', 'armF', 'hand', 'thigh', 'shin', 'foot']


def group_of(name):
    b = name.split('.')[0]
    if b in ('head', 'neck'): return 'head'
    if b in ('hips', 'glute', 'spine', 'spine1', 'spine2'): return 'torso'
    if b in ('shoulder', 'deltoid'): return 'shoulder'
    if b == 'upperArm': return 'armU'
    if b in ('forearm', 'forearmTwist'): return 'armF'
    if b.startswith(('hand', 'index', 'middle', 'pinky', 'ring', 'thumb')): return 'hand'
    if b == 'thigh': return 'thigh'
    if b == 'shin': return 'shin'
    if b in ('foot', 'toe'): return 'foot'
    raise KeyError(name)


def load_body():
    j, b = skinfit.read_glb(GLB)
    nd = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan')
    p = j['meshes'][nd['mesh']]['primitives'][0]
    A = p['attributes']
    P = skinfit.accessor(j, b, A['POSITION']); N = skinfit.accessor(j, b, A['NORMAL']); UV = skinfit.accessor(j, b, A['TEXCOORD_0'])
    F = skinfit.accessor(j, b, p['indices']).reshape(-1, 3).astype(int)
    J = skinfit.accessor(j, b, A['JOINTS_0']).astype(int); W = skinfit.accessor(j, b, A['WEIGHTS_0'])
    sk = j['skins'][0]
    names = [j['nodes'][i].get('name') for i in sk['joints']]
    ibm = skinfit.accessor(j, b, sk['inverseBindMatrices']).reshape(-1, 4, 4)
    jpos = {n: np.linalg.inv(m.T)[:3, 3] for n, m in zip(names, ibm)}
    # per-vertex group weights (n_vert, n_groups)
    gi = {g: i for i, g in enumerate(GROUPS)}
    jg = np.array([gi[group_of(n)] for n in names])
    GW = np.zeros((len(P), len(GROUPS)), np.float32)
    for k in range(4):
        np.add.at(GW, (np.arange(len(P)), jg[J[:, k]]), W[:, k].astype(np.float32))
    return dict(P=P.astype(np.float32), N=N.astype(np.float32), UV=UV, F=F, GW=GW, jpos=jpos, names=names, J=J, W=W)


def raster_tri(UV, F, n, tol=0.06):
    """Per texel: triangle id (-1 outside) and barycentrics (w0, w1).  Texel centre = (x + .5, y + .5) in pixels; image row = v * n (glTF v is down).
    Texels within `tol` (barycentric) outside a triangle are accepted as a gutter unless a triangle contains them properly."""
    tri = np.full((n, n), -1, np.int32)
    inside = np.zeros((n, n), bool)
    w0m = np.zeros((n, n), np.float32); w1m = np.zeros((n, n), np.float32)
    U = UV * n
    for fi in range(len(F)):
        u = U[F[fi]]
        x0 = max(int(np.floor(u[:, 0].min() - 1)), 0); x1 = min(int(np.ceil(u[:, 0].max() + 1)), n - 1)
        y0 = max(int(np.floor(u[:, 1].min() - 1)), 0); y1 = min(int(np.ceil(u[:, 1].max() + 1)), n - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = u
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12: continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        mn = np.minimum(np.minimum(w0, w1), w2)
        ins = mn >= 0
        acc = mn >= -tol
        sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        take = (ins & ~inside[sl]) | (acc & (tri[sl] < 0))
        if not take.any(): continue
        t = tri[sl]; t[take] = fi
        w0m[sl][take] = w0[take]; w1m[sl][take] = w1[take]
        inside[sl] |= ins & take
    return tri, w0m, w1m, inside


def gather(tri, w0, w1, F, V, rows=None):
    """Interpolate a per-vertex attribute V (n_vert, k) at the texels of `rows` (slice of rows) -> (rows, n, k) float32; uncovered = 0."""
    sl = rows if rows is not None else slice(None)
    t = tri[sl]; cov = t >= 0
    tt = np.where(cov, t, 0)
    f = F[tt]
    a = w0[sl][..., None]; b = w1[sl][..., None]; c = 1 - a - b
    out = a * V[f[..., 0]] + b * V[f[..., 1]] + c * V[f[..., 2]]
    out[~cov] = 0
    return out.astype(np.float32)
