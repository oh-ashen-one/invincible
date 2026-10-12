#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14: de-facet the hero's shoulders / upper arms in the UE-only hero GLB.

Critic r13 (image quality): "Cinder's shoulders are faceted".  The browser mesh has 7 - 17 mm edges on the deltoid / upper arm (57 px per edge in the 4K chest still): the
silhouette is a polygon and the near-black DEEP panel shows its flat shading planes.  This script refines the shoulder / upper-arm region TWICE (conforming red-green
refinement of hero_head_r14.refine: 4x faces per level, every attribute, the UVs and the four skin joints / weights interpolated, so no crack and no T-junction) and puts every
new vertex on the PHONG-TESSELLATION surface: p' = p* + 0.75 (1/2 (pi_a(p*) + pi_b(p*)) - p*), pi_a = projection onto the tangent plane at the edge's end a (welded normals, so the
duplicates of a UV seam land on the same point: no crack).  Original vertices do not move (the surface still interpolates the browser mesh, the suit paint of design.py -
evaluated on the original mesh - lands where it did).  Normals follow: n_new = normalize(n_old + (n_welded(displaced) - n_welded(flat refined))).

  python3 tools/ue_char/suit8/hero_shoulder_r14.py <SK_Hero.glb>        (in place; run after hero_head_r14.py / hero_lens_r14.py, before hero_weights_r12.py)
  python3 tools/ue_char/suit8/hero_shoulder_r14.py --report <SK_Hero.glb>   (edge length / silhouette polygon measures before / after, CPU)
"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import glbedit  # noqa: E402
import skinfit  # noqa: E402
import hero_head_r14 as HH  # noqa: E402

# the shoulder cap + upper arm of the T-pose rest mesh: |x| 0.10 .. 0.46 m, y 1.26 .. 1.56 m (centroid test); a smooth ramp keeps the Phong strength at 0 at the zone edge
ZONE = dict(x0=0.10, x1=0.46, y0=1.26, y1=1.56)
LEVELS = 1
ALPHA = 0.75


def zone_sel(P, F, sh=0.0):
    c = P[F].mean(1)
    ax = np.abs(c[:, 0])
    return (ax > ZONE['x0'] + sh) & (ax < ZONE['x1'] - sh) & (c[:, 1] > ZONE['y0'] + sh) & (c[:, 1] < ZONE['y1'] - sh)


def phong_place(P, nw, a_idx, b_idx, new_idx):
    """Move the new (midpoint) vertices new_idx (edge a_idx - b_idx) onto the Phong surface (strength ALPHA); returns the new positions."""
    pa, pb = P[a_idx], P[b_idx]
    na, nb = nw[a_idx], nw[b_idx]
    ps = 0.5 * (pa + pb)
    pia = ps - ((ps - pa) * na).sum(1, keepdims=True) * na
    pib = ps - ((ps - pb) * nb).sum(1, keepdims=True) * nb
    return ps + ALPHA * (0.5 * (pia + pib) - ps)


def smooth(P, N, UV, J, W, F, levels=LEVELS):
    n_start = len(P)
    for lev in range(levels):
        sh = 0.0 if lev == 0 else 0.012
        sel = zone_sel(P, F, sh)
        nv0 = len(P)
        nw = HH.welded_normals(P, F)                                   # normals at the CURRENT vertices (welded: seam duplicates agree)
        Pn, Nn, UVn, Jn, Wn, Fn = HH.refine(P, N, UV, J, W, F, sel)
        # the new vertices are the midpoints of the marked edges: recover each one's end points from its position
        newv = np.arange(nv0, len(Pn))
        mid = Pn[newv].astype(np.float64)
        # candidate edges: the edges of the selected triangles
        tri = F[sel]
        E = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
        E = np.unique(np.sort(E, axis=1), axis=0)
        mids = 0.5 * (P[E[:, 0]].astype(np.float64) + P[E[:, 1]].astype(np.float64))
        # match new vertices to edges (refine appended them in the order of its own `marked` dict = insertion order of the selected triangles' edges, not sorted): match by position
        from scipy.spatial import cKDTree
        tree = cKDTree(mids)
        dist, ei = tree.query(mid, k=1)
        assert dist.max() < 1e-7, 'refine midpoint match failed (%g)' % dist.max()
        a_idx, b_idx = E[ei, 0], E[ei, 1]
        # the displacement strength ramps to 0 toward the zone boundary
        pos = phong_place(P.astype(np.float64), nw.astype(np.float64), a_idx, b_idx, newv)
        w = ramp(mid)
        Pn = Pn.astype(np.float64)
        Pn[newv] = mid + (pos - mid) * w[:, None]
        P, N, UV, J, W, F = Pn.astype(np.float32), Nn, UVn, Jn, Wn, Fn
        # welded normals after each level so the next level's tangent planes see the displaced surface
        N = N.copy()
        n1 = HH.welded_normals(P, F)
        # keep the original (DCC) normals at the old vertices, the welded normal of the displaced surface at the new ones
        N[newv] = n1[newv]
    return P, N, UV, J, W, F


def ramp(p):
    """1 inside the zone, falling to 0 over 25 mm toward its boundary (positions only)."""
    ax = np.abs(p[:, 0]); y = p[:, 1]
    def s(v):
        t = np.clip(v / 0.025, 0, 1); return t * t * (3 - 2 * t)
    return s(ax - ZONE['x0']) * s(ZONE['x1'] - ax) * s(y - ZONE['y0']) * s(ZONE['y1'] - y)


def body_prim(j):
    nd = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan')
    return j['meshes'][nd['mesh']]['primitives'][0]


def read_body(g):
    j = g.j; p = body_prim(j); A = p['attributes']; raw = bytes(g.bin)
    P = skinfit.accessor(j, raw, A['POSITION']).astype(np.float32); N = skinfit.accessor(j, raw, A['NORMAL']).astype(np.float32)
    UV = skinfit.accessor(j, raw, A['TEXCOORD_0']).astype(np.float32)
    J = skinfit.accessor(j, raw, A['JOINTS_0']).astype(np.int64); W = skinfit.accessor(j, raw, A['WEIGHTS_0']).astype(np.float32)
    F = skinfit.accessor(j, raw, p['indices']).reshape(-1, 3).astype(int)
    return p, P, N, UV, J, W, F


def edge_stats(P, F, sel):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); m = np.repeat(sel, 3)
    L = np.linalg.norm(P[E[m, 0]] - P[E[m, 1]], axis=1)
    return dict(edges=int(len(L)), mean_mm=round(float(L.mean() * 1e3), 2), p90_mm=round(float(np.percentile(L, 90) * 1e3), 2))


def main(path, report=False):
    g = glbedit.Glb(path)
    p, P, N, UV, J, W, F = read_body(g)
    nv0, nt0 = len(P), len(F)
    st0 = edge_stats(P, F, zone_sel(P, F))
    P2, N2, UV2, J2, W2, F2 = smooth(P, N, UV, J, W, F)
    st1 = edge_stats(P2, F2, zone_sel(P2, F2))
    jt = np.uint8 if J.max() < 256 else np.uint16
    Fi = F2.reshape(-1).astype(np.uint32 if len(P2) > 65535 else np.uint16)
    p['attributes'] = {'POSITION': g.add(P2.astype(np.float32), 34962, True), 'NORMAL': g.add(N2.astype(np.float32), 34962), 'TEXCOORD_0': g.add(UV2.astype(np.float32), 34962),
                       'JOINTS_0': g.add(J2.astype(jt), 34962), 'WEIGHTS_0': g.add(W2.astype(np.float32), 34962)}
    p['indices'] = g.add(Fi, 34963)
    g.save(path)
    rep = dict(vertices=[nv0, len(P2)], triangles=[nt0, len(F2)], zone_edges_before=st0, zone_edges_after=st1)
    print('hero_shoulder_r14: ' + json.dumps(rep))
    return rep


if __name__ == '__main__':
    main([a for a in sys.argv[1:] if not a.startswith('--')][0], '--report' in sys.argv)
