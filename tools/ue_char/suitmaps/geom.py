"""Geometry fixes for a fitted AI-suit skin (numpy, no Blender). Vertex count, order, UVs and triangles are unchanged.

    python3 tools/ue_char/suitmaps/geom.py <suit> [--flatten-back]

1. Weld skin weights across UV-seam duplicates. Tripo splits vertices along UV seams; skinfit.py transferred weights
   to each copy separately, so coincident copies carry different weights (L1 difference up to 0.8) and the seams tear
   open into dark slits as soon as the suit animates. Every copy now gets the mean of its group (top 4, renormalised).
2. --flatten-back (Gemini, Qwen): Tripo sculpted the chest emblem onto the upper back. The back band is fitted with
   a smooth cubic height field z(x, y) (robust, relief excluded); vertices standing proud of it are pulled back onto it
   with a feathered falloff, and normals are recomputed there.
Writes _scratch/characters/suits/<suit>/geom.npz (P, N, J, W, flat = per-vertex flatten weight).

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import mesh_arrays, orig_skin, accessor, SCRATCH  # noqa: E402

FLAT = {'qwen': ('disc', 0.105), 'gemini': ('grow', 4)}
BAND = {'gemini': (-0.2, 0.2, 1.05, 1.55), 'qwen': (-0.2, 0.2, 1.1, 1.58)}


def seam_groups(suit):
    """Group seam duplicates by their position in the untouched Tripo source (exactly coincident there; the fitted
    skin's copies drifted apart by up to ~8 mm because each copy was un-posed with its own weights)."""
    from common import SUITS, mesh_arrays as ma
    _, _, Ps, _, _, _ = ma(SUITS[suit])
    key = np.round(Ps * 1e6).astype(np.int64)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    return inv.ravel(), cnt


def weld(P, N, J, W, inv, cnt, nb=58):
    """Same weights, bind position and normal for every copy of a seam vertex."""
    D = np.zeros((len(P), nb))
    for k in range(4): np.add.at(D, (np.arange(len(P)), J[:, k]), W[:, k])
    G = np.zeros((cnt.size, nb)); np.add.at(G, inv, D); G /= cnt[:, None]
    Dn = G[inv]
    wdiff = np.abs(D - Dn).sum(1)
    Jn = np.argsort(-Dn, 1)[:, :4]
    Wn = np.take_along_axis(Dn, Jn, 1); Wn /= Wn.sum(1, keepdims=True)
    Gp = np.zeros((cnt.size, 3)); np.add.at(Gp, inv, P); Gp /= cnt[:, None]
    pdiff = np.linalg.norm(P - Gp[inv], axis=1)
    Gn = np.zeros((cnt.size, 3)); np.add.at(Gn, inv, N); Gn /= np.maximum(np.linalg.norm(Gn, axis=1, keepdims=True), 1e-12)
    return Gp[inv], Gn[inv], Jn.astype(np.uint8), Wn.astype(np.float32), wdiff, pdiff


def vertex_normals(P, F):
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])  # area weighted
    N = np.zeros_like(P)
    for k in range(3): np.add.at(N, F[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def quad_basis(x, y):
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], 1)


def emblem_vertices(suit, UV):
    """Back-emblem vertices, by the source texture colour at their UV (the relief is painted as well as sculpted)."""
    import cv2
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = np.array(Image.open(os.path.join(SCRATCH, f'{suit}_src8k.png'))).astype(np.float32) / 255
    H = im.shape[0]
    px = np.clip((UV * H).astype(int), 0, H - 1)
    c = im[px[:, 1], px[:, 0]]
    lab = cv2.cvtColor(c[None], cv2.COLOR_RGB2LAB)[0]
    L, A, Bb = lab[:, 0], lab[:, 1], lab[:, 2]
    if suit == 'qwen':    # violet emblem on red: blue-ish (b < -25) and magenta-ish (a > 15)
        return (Bb < -25) & (A > 15)
    if suit == 'gemini':  # pale lavender four-point star
        return (L > 32) & (Bb < -20) & (A > 12)
    raise SystemExit('no emblem rule for ' + suit)


def grow(mask, F, inv, rings):
    adj_src = np.concatenate([F[:, 0], F[:, 1], F[:, 2], F[:, 1], F[:, 2], F[:, 0]])
    adj_dst = np.concatenate([F[:, 1], F[:, 2], F[:, 0], F[:, 0], F[:, 1], F[:, 2]])
    level = np.where(mask, 0, -1)
    cur = mask.copy()
    for r in range(1, rings + 1):
        g = np.zeros(inv.max() + 1, bool); np.logical_or.at(g, inv, cur); cur = g[inv]
        nb = np.zeros(len(mask), bool); np.logical_or.at(nb, adj_dst, cur[adj_src])
        g = np.zeros(inv.max() + 1, bool); np.logical_or.at(g, inv, nb); nb = g[inv]
        level[nb & (level < 0)] = r
        cur = nb | cur
    return level


def flatten_back(suit, P, N, UV, F, inv, band, log):
    """Remove the sculpted back emblem: re-solve the depth (z) of the emblem vertices as a bi-harmonic fill from the
    surrounding back surface (x, y stay put, so the texture does not slide). Works on the welded (unique-position) graph."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    x0, x1, y0, y1 = band
    sel = (P[:, 0] > x0) & (P[:, 0] < x1) & (P[:, 1] > y0) & (P[:, 1] < y1) & (N[:, 2] < -0.3) & (P[:, 2] < -0.02)
    emb = emblem_vertices(suit, UV) & sel
    ctr = np.median(P[emb], 0)
    emb &= np.linalg.norm(P[:, :2] - ctr[:2], axis=1) < 0.12
    mode, val = FLAT[suit]
    if mode == 'disc':      # whole emblem disc (the rim of the hexagon is not reliably emblem-coloured per vertex)
        # back-facing verts only. Including the sideways groove walls of Qwen's deep (up to ~3 cm) carved relief was
        # tried: the uniform-Laplacian fill then tears the mesh, so the carved outline stays as a faint emboss.
        region = sel & (np.linalg.norm(P[:, :2] - ctr[:2], axis=1) < val)
    else:                   # emblem-coloured verts grown `val` rings
        region = (grow(emb, F, inv, val) >= 0) & (P[:, 2] < -0.02)
    # welded graph
    nu = inv.max() + 1
    Pu = np.zeros((nu, 3)); cnt = np.bincount(inv, minlength=nu); np.add.at(Pu, inv, P); Pu /= cnt[:, None]
    Fu = inv[F]
    e = np.concatenate([Fu[:, [0, 1]], Fu[:, [1, 2]], Fu[:, [2, 0]]]); e = e[e[:, 0] != e[:, 1]]
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nu, nu)).tocsr(); A = ((A + A.T) > 0).astype(float)
    deg = np.asarray(A.sum(1)).ravel()
    L = sp.diags(deg) - A
    Lu = L.T @ L                                  # bi-Laplacian (uniform weights)
    ru = np.zeros(nu, bool); np.logical_or.at(ru, inv, region)
    free = np.nonzero(ru)[0]; fixed = np.nonzero(~ru)[0]
    M = Lu[free][:, free]; rhs = -Lu[free][:, fixed] @ Pu[fixed, 2]
    # components of the free set that touch no fixed vertex have no boundary condition: leave them alone
    from scipy.sparse.csgraph import connected_components
    ncomp, lab = connected_components(A[free][:, free], directed=False)
    touches = np.asarray((A[free][:, fixed]).sum(1)).ravel() > 0
    ok_comp = np.zeros(ncomp, bool); np.logical_or.at(ok_comp, lab, touches)
    keep = ok_comp[lab]
    Mk = Lu[free[keep]][:, free[keep]]; fx = np.concatenate([fixed, free[~keep]])
    z = Pu[free, 2].copy()
    z[keep] = spl.spsolve(Mk.tocsc(), -Lu[free[keep]][:, fx] @ Pu[fx, 2])
    dz = z - Pu[free, 2]
    # floating relief shells (Tripo modelled some emblems as separate pieces over the back): tuck them 3 mm under the
    # back surface, interpolated (inverse distance, 8 nearest) from the surrounding back-band vertices
    if (~keep).any():
        from scipy.spatial import cKDTree
        fu = np.zeros(nu, bool); np.logical_or.at(fu, inv, sel & ~region)
        body = np.nonzero(fu & ~ru)[0]
        tree = cKDTree(Pu[body, :2]); dd, ii = tree.query(Pu[free[~keep], :2], k=8)
        wi = 1 / np.maximum(dd, 1e-4) ** 2
        zb = (Pu[body, 2][ii] * wi).sum(1) / wi.sum(1)
        z[~keep] = np.maximum(Pu[free[~keep], 2], zb + 0.003)
        log(f'  tucked {(~keep).sum()} floating-shell verts under the back surface')
    dz = z - Pu[free, 2]
    bad = np.abs(dz) > 0.03                      # a fill never needs to move a vertex 3 cm: treat as failure there
    z[bad] = Pu[free, 2][bad]; dz[bad] = 0
    log(f'  free components {ncomp} ({(~ok_comp).sum()} without boundary), rejected {bad.sum()} moves > 3 cm')
    zu = Pu[:, 2].copy()
    # grow mode: only pull proud (further back, more negative z) material in; never push the surface out
    # disc mode (Qwen: relief is carved grooves as well as a proud rim) replaces the depth both ways
    zu[free] = z if mode == 'disc' else np.where(dz > 0, z, Pu[free, 2])
    Pn = P.copy(); Pn[:, 2] = np.where(region | ru[inv], zu[inv], P[:, 2])
    moved = np.abs(Pn - P).max(1) > 1e-7
    log(f'  emblem verts {emb.sum()} centre {ctr.round(3)}, free (welded) {len(free)}, '
        f'moved {moved.sum()} verts, max {np.abs(Pn - P).max() * 1000:.1f} mm, mean {np.abs(Pn - P)[moved].max(1).mean() * 1000:.1f} mm')
    Nn_all = vertex_normals(Pn, F)
    g = np.zeros((nu, 3)); np.add.at(g, inv, Nn_all); g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)
    touch = (grow(moved | region, F, inv, 1) >= 0)   # Tripo's normals still carry the relief: recompute all of it
    Nn = N.copy(); Nn[touch] = g[inv][touch]
    flat = np.zeros(len(P)); flat[region] = 1.0
    return Pn, Nn, flat


def main():
    suit = sys.argv[1]
    out = os.path.join(SCRATCH, suit); os.makedirs(out, exist_ok=True)
    j, b, P, N, UV, F = mesh_arrays(orig_skin(suit))
    A = j['meshes'][0]['primitives'][0]['attributes']
    J = accessor(j, b, A['JOINTS_0']).astype(np.int64); W = accessor(j, b, A['WEIGHTS_0'])
    inv, cnt = seam_groups(suit)
    P, N, Jn, Wn, wdiff, pdiff = weld(P, N, J, W, inv, cnt)
    print(f'{suit}: {cnt.size} unique positions / {len(P)} verts; seam copies with weight L1 diff > 0.05: '
          f'{(wdiff > 0.05).sum()} (max {wdiff.max():.2f}), bind gap max {pdiff.max() * 1000:.1f} mm -> welded')
    flat = np.zeros(len(P))
    if '--flatten-back' in sys.argv:
        P, N, flat = flatten_back(suit, P, N, UV, F, inv, BAND[suit], print)
    np.savez(os.path.join(out, 'geom.npz'), P=P.astype(np.float32), N=N.astype(np.float32), J=Jn, W=Wn, flat=flat.astype(np.float32))
    print('wrote', os.path.join(out, 'geom.npz'))


if __name__ == '__main__':
    main()
