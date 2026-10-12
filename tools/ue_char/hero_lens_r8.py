#!/usr/bin/env python3
"""Round-08 hero eyes: each eye = ONE closed bezel ring sealed to a lens that is sunk into the bezel, both conformed to the mask surface.
Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.  Replaces the 'LensFrame' / 'Lens' primitives of the UE-only derived
SK_Hero.glb ($P2_SCRATCH/ueimport, the browser GLB is untouched).

Critic r07: 'the right lens sits outside the head, a background gap at (3250-3300, 900-1250)'.  Causes: the old lens was a flat disc (plane fit + dome) that
did not follow the curved head, and the frame was a separate loose tube.  Here:
  * the outline is an ORIGINAL blade-shaped eye (rounded inner end, pointed outer tip lifted 12 deg), built as a closed periodic spline;
  * the mask height field z(x, y) is rasterised from the actual SpiderSuit head triangles, upper-enveloped and smoothed; the lens, the bezel loops and the
    buried foot of the bezel are all z(x, y) + a profile height, so the eye follows the head instead of floating off it;
  * the lens boundary loop and the bezel's inner loop are the SAME positions (no gap between rim and lens at any angle), the bezel's outer foot is buried
    0.7 mm under the mask (no gap between rim and head);
  * the lens stays inside |x| <= 0.056 (surface normal <= ~45 deg from straight ahead), so it never reaches the head silhouette in the 3/4 views.

  python3 tools/ue_char/hero_lens_r8.py SK_Hero.glb [--dump DIR]
"""
import sys, os, json
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'suit8')); sys.path.insert(0, os.path.join(HERE, '..', 'skinfit'))
import glbedit  # noqa: E402

# ---- eye design (metres, local frame of one eye: +u toward the OUTER end, +v up)
KEY = np.array([(21.0, 3.2), (11.5, 9.6), (-2.0, 11.0), (-14.0, 8.4), (-19.5, 0.8), (-14.0, -6.2), (-2.0, -7.6), (11.0, -3.6)]) * 0.95e-3
TILT = np.radians(12.0)                      # outer tip lifted
CENTER_X, CENTER_Y = 0.0272, 1.6775          # left eye centre on the mask (mirrored for the right eye)
N_OUT = 72                                   # outline samples
RINGS = 9
BEZEL = [(0.0, 0.6), (0.0, 1.9), (0.9, 2.3), (1.9, 2.3), (3.3, 0.5), (4.3, -0.7)]     # (outward offset mm, height above the mask mm); first = lens edge
LENS_EDGE_H, LENS_DOME_H = 0.6, 1.7          # lens edge height (= BEZEL[0]) and the extra dome at the centre (mm)


def catmull_closed(pts, n):
    m = len(pts)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for t in np.linspace(0, 1, 40, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out = np.array(out)
    seg = np.linalg.norm(np.diff(np.vstack([out, out[:1]]), axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    tt = np.linspace(0, s[-1], n, endpoint=False)
    full = np.vstack([out, out[:1]])
    return np.stack([np.interp(tt, s, full[:, 0]), np.interp(tt, s, full[:, 1])], 1)


def outline(mirror):
    c, s = np.cos(TILT), np.sin(TILT)
    R = np.array([[c, -s], [s, c]])
    pts = catmull_closed(KEY, N_OUT) @ R.T
    if mirror: pts[:, 0] = -pts[:, 0]
    pts[:, 0] += (-CENTER_X if mirror else CENTER_X); pts[:, 1] += CENTER_Y
    return pts


def head_height_field(P, F, step=2.5e-4, x0=-0.11, x1=0.11, y0=1.58, y1=1.78):
    """Front-most z of the SpiderSuit head triangles on a regular (x, y) grid."""
    nx = int(round((x1 - x0) / step)); ny = int(round((y1 - y0) / step))
    Z = np.full((ny, nx), -1.0, np.float32)
    tri = P[F]
    keep = (tri[:, :, 1].max(1) > y0) & (tri[:, :, 1].min(1) < y1) & (np.abs(tri[:, :, 0]).min(1) < x1)
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    keep &= fn[:, 2] > 0                                   # faces looking toward +z
    for t in tri[keep]:
        px = (t[:, 0] - x0) / step; py = (t[:, 1] - y0) / step
        xa, xb = max(int(np.floor(px.min())), 0), min(int(np.ceil(px.max())), nx - 1)
        ya, yb = max(int(np.floor(py.min())), 0), min(int(np.ceil(py.max())), ny - 1)
        if xb < xa or yb < ya: continue
        gx, gy = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
        a, b, c = np.stack([px, py], 1)
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12: continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        z = w0 * t[0, 2] + w1 * t[1, 2] + w2 * t[2, 2]
        sl = (slice(ya, yb + 1), slice(xa, xb + 1))
        Z[sl] = np.where(m & (z > Z[sl]), z, Z[sl])
    # fill holes from the nearest filled cell, upper envelope over 2.5 mm, then smooth (sigma 2 mm)
    hole = Z < 0
    if hole.any():
        _, (iy, ix) = ndi.distance_transform_edt(hole, return_indices=True); Z = Z[iy, ix]
    env = ndi.maximum_filter(Z, size=int(round(0.005 / step)))
    Zs = ndi.gaussian_filter(env, 0.002 / step)
    Zs = np.maximum(Zs, ndi.gaussian_filter(Z, 0.001 / step))
    return Zs, Z, (x0, y0, step)


def zlookup(Zs, grid, x, y):
    x0, y0, step = grid
    fx = (x - x0) / step - 0.5; fy = (y - y0) / step - 0.5
    return ndi.map_coordinates(Zs, [fy, fx], order=1, mode='nearest')


def offset_outline(pts, d):
    """Outward offset of a closed CCW-or-CW convex outline by d (metres) via vertex normals."""
    c = pts.mean(0)
    t = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    n = np.stack([t[:, 1], -t[:, 0]], 1); n /= np.linalg.norm(n, axis=1, keepdims=True)
    flip = ((pts - c) * n).sum(1) < 0
    n[flip] *= -1
    return pts + n * d


def build_eye(Zs, grid, mirror):
    out = outline(mirror)
    c = out.mean(0)
    M = len(out)
    # ---- lens: centre + RINGS concentric rings scaled about the centre; height = mask + edge + dome
    verts = [np.array([c[0], c[1]])]
    hs = [LENS_EDGE_H + LENS_DOME_H]
    rho = [0.0]
    for r in range(1, RINGS + 1):
        k = r / RINGS
        ring = c + (out - c) * k
        verts += list(ring); hs += [LENS_EDGE_H + LENS_DOME_H * (1 - k * k)] * M; rho += [k] * M
    V2 = np.array(verts)
    lz = zlookup(Zs, grid, V2[:, 0], V2[:, 1]) + np.array(hs) * 1e-3
    LV = np.column_stack([V2, lz])
    tris = [(0, 1 + i, 1 + (i + 1) % M) for i in range(M)]
    for r in range(1, RINGS):
        a = 1 + (r - 1) * M; b = 1 + r * M
        for i in range(M):
            j = (i + 1) % M
            tris += [(a + i, b + i, b + j), (a + i, b + j, a + j)]
    LF = np.array(tris)
    # ---- bezel: profile loops from the lens edge outward
    loops = []
    for off_mm, h_mm in BEZEL:
        p2 = offset_outline(out, off_mm * 1e-3) if off_mm else out.copy()
        z = zlookup(Zs, grid, p2[:, 0], p2[:, 1]) + h_mm * 1e-3
        loops.append(np.column_stack([p2, z]))
    BV = np.vstack(loops)
    bt = []
    for k in range(len(loops) - 1):
        for i in range(M):
            j = (i + 1) % M
            a, b = k * M, (k + 1) * M
            bt += [(a + i, b + i, b + j), (a + i, b + j, a + j)]
    BF = np.array(bt)
    return LV, LF, BV, BF, out


def orient(V, F, want_z=1.0, ref=None):
    """Flip triangle winding so the majority faces +z (front)."""
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    if (fn[:, 2] * fn[:, 2].clip(0)).sum() < 0 or (fn[:, 2].sum() < 0): F = F[:, ::-1]
    return F


def vnormals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    n = np.zeros_like(V)
    for k in range(3): np.add.at(n, F[:, k], fn)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    return n


def main(path, dump=None):
    g = glbedit.Glb(path)
    j = g.j
    body = next(nd for nd in j['nodes'] if nd.get('name') == 'SpiderMan')
    prims = j['meshes'][body['mesh']]['primitives']
    mat = {j['materials'][p['material']]['name']: p for p in prims}
    suit, frame, lens = mat['SpiderSuit'], mat['LensFrame'], mat['Lens']
    import skinfit  # noqa: E402
    raw = bytes(g.bin)
    P = skinfit.accessor(j, raw, suit['attributes']['POSITION']).astype(np.float32)
    F = skinfit.accessor(j, raw, suit['indices']).reshape(-1, 3).astype(int)
    Zs, Zraw, grid = head_height_field(P, F)
    LVs, LFs, BVs, BFs = [], [], [], []
    lo = bo = 0
    report = {}
    for mirror in (False, True):
        LV, LF, BV, BF, out = build_eye(Zs, grid, mirror)
        if mirror:     # mirrored geometry flips the winding
            LF = LF[:, ::-1]; BF = BF[:, ::-1]
        LF = orient(LV, LF); BF = orient(BV, BF)
        LVs.append(LV); LFs.append(LF + lo); lo += len(LV)
        BVs.append(BV); BFs.append(BF + bo); bo += len(BV)
        # clearance check: lens / bezel vs the raw mask height under them
        zr = zlookup(Zraw, grid, LV[:, 0], LV[:, 1])
        report['L' if not mirror else 'R'] = dict(x_min=round(float(out[:, 0].min()), 4), x_max=round(float(out[:, 0].max()), 4), y_min=round(float(out[:, 1].min()), 4),
                                                 y_max=round(float(out[:, 1].max()), 4), lens_min_clearance_mm=round(float((LV[:, 2] - zr).min() * 1e3), 2),
                                                 width_mm=round(float((out[:, 0].max() - out[:, 0].min()) * 1e3), 1), height_mm=round(float((out[:, 1].max() - out[:, 1].min()) * 1e3), 1))
    LV = np.vstack(LVs).astype(np.float32); LF = np.vstack(LFs).astype(np.uint16)
    BV = np.vstack(BVs).astype(np.float32); BF = np.vstack(BFs).astype(np.uint16)
    LN = vnormals(LV, LF.astype(int)).astype(np.float32); BN = vnormals(BV, BF.astype(int)).astype(np.float32)
    HEAD = 7

    def setprim(p, V, N, Fi):
        n = len(V)
        uv = np.zeros((n, 2), np.float32)
        ji = np.zeros((n, 4), np.uint8); ji[:, 0] = HEAD
        wt = np.zeros((n, 4), np.float32); wt[:, 0] = 1.0
        p['attributes'] = {'POSITION': g.add(V, 34962, True), 'NORMAL': g.add(N, 34962), 'TEXCOORD_0': g.add(uv, 34962),
                           'JOINTS_0': g.add(ji, 34962), 'WEIGHTS_0': g.add(wt, 34962)}
        p['indices'] = g.add(Fi.reshape(-1), 34963)
    setprim(lens, LV, LN, LF); setprim(frame, BV, BN, BF)
    g.save(path)
    report.update(lens_verts=len(LV), lens_tris=len(LF), bezel_verts=len(BV), bezel_tris=len(BF))
    print(json.dumps(report))
    if dump:
        os.makedirs(dump, exist_ok=True)
        np.savez(dump + '/eyes.npz', LV=LV, LF=LF, BV=BV, BF=BF, LN=LN, BN=BN, Zs=Zs, Zraw=Zraw, grid=np.array(grid))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[sys.argv.index('--dump') + 1] if '--dump' in sys.argv else None)
