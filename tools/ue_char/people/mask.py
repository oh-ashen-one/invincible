"""Round-04 enemy face masks and texture fixes for the people pipeline (numpy/scipy). Fan homage; no affiliation.

The round-03 bandana was a separate ray-cast shell: at 72 x 14 samples it read as a flat card with polygon edges, clipped the ears and
let the nose through between rays. Here the mask IS the head surface:
  subdivide_region()  one midpoint subdivision of the triangles around the lower face / neck (red-green refinement, no T-junctions,
                      UV seams split on both sides by welded position);
  drape()             pushes the lower-face vertices radially out onto the convex hull of the front of the head (the cloth spans
                      nose -> cheeks and chin -> collar instead of following lips and the neck hollow), plus a few mm of cloth
                      thickness and small folds; ears are excluded, so nothing can poke through or clip;
  paint_mask()        paints the cloth into the body atlas by 3D position (feathered edge + stitched hem, weave, soft fold shading,
                      no tiled print), and a tie band round the back of the head, leaving the ears bare;
  seam_blend()        averages texels along UV-island borders with the texels at the same 3D position on the other island (hides the
                      hard colour seams of the Tripo atlas, e.g. the scalp/forehead line);
  auto_landmarks()    nose tip / eye / ear-lobe / chin heights from the mesh (for people without hand-measured CFG numbers)."""
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull, cKDTree


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------------ landmarks and mask region
def auto_landmarks(P, axis_z=-0.02):
    top = P[:, 1].max()
    head = (P[:, 1] > top - 0.30) & (P[:, 1] < top - 0.08) & (np.abs(P[:, 0]) < 0.025)
    i = np.argmax(np.where(head, P[:, 2], -9))
    nose = float(P[i, 1]); nz = float(P[i, 2])
    # chin: lowest centre-line point still within 4.5 cm behind the nose tip before the neck recedes
    col = (np.abs(P[:, 0]) < 0.02) & (P[:, 1] < nose) & (P[:, 1] > nose - 0.16) & (P[:, 2] > nz - 0.045)
    chin = float(P[col, 1].min()) if col.any() else nose - 0.09
    return dict(eye=nose + 0.031, nose=nose, ear_lobe=nose - 0.027, chin=chin, axis_z=axis_z, nose_z=nz)


def mask_bounds(phi, cfg):
    """top/bottom heights of the mask as a function of azimuth phi (0 = front)."""
    eye, ear, chin = cfg['eye'], cfg['ear_lobe'], cfg['chin']
    a = np.abs(phi)
    ang = np.radians([0, 35, 70, 90, 105, 125, 150, 180])
    top = np.interp(a, ang, [eye - .016, eye - .026, ear + .012, ear + .020, ear + .030, ear + .038, ear + .040, ear + .040])
    bd = cfg.get('bot_drop', 0.040)     # how far below the chin the front hem hangs (round 05b: brute 0.004 - its vest collar reaches the chin)
    bot = np.interp(a, ang, [chin - bd, chin - bd + .004, chin - bd * 0.4, ear - .012, ear + .004, ear + .010, ear + .010, ear + .010])
    if not cfg.get('tie_band', True):          # long / voluminous hair at the back: the mask ends behind the ears (no painted tie)
        cut = smoothstep(np.radians(108), np.radians(116), a)
        top = top * (1 - cut) + (bot - 0.01) * cut
    return top, bot


def cyl(P, cfg):
    x, z = P[..., 0], P[..., 2] - cfg['axis_z']
    return np.arctan2(x, z), np.hypot(x, z)


def ear_flag(P, cfg, Pall):
    """True where a point belongs to an ear: beyond the cheek width of the front half of the head at that height, not in front."""
    y = P[..., 1]
    phi, r = cyl(P, cfg)
    ear = cfg['ear_lobe']
    band = (y > ear - 0.012) & (y < ear + 0.075) & (np.abs(phi) > np.radians(55)) & (np.abs(phi) < np.radians(135))
    # cheek half-width per 5 mm slice from the front half
    front = (Pall[:, 2] > cfg['axis_z'] + 0.035) & (Pall[:, 1] > ear - 0.03) & (Pall[:, 1] < ear + 0.09) & (np.hypot(Pall[:, 0], Pall[:, 2] - cfg['axis_z']) < 0.13)
    ys = np.arange(ear - 0.03, ear + 0.09, 0.005)
    w = np.array([np.percentile(np.abs(Pall[front & (np.abs(Pall[:, 1] - yy) < 0.004), 0]), 97) if (front & (np.abs(Pall[:, 1] - yy) < 0.004)).sum() > 5 else 0.07 for yy in ys])
    wy = np.interp(y, ys, w)
    return band & (np.abs(P[..., 0]) > wy + 0.004)


def region_weight(P, cfg, feather=0.006):
    """0..1 inside the mask (1 = fully cloth), by height against the azimuth-dependent top/bottom curves."""
    phi, r = cyl(P, cfg)
    top, bot = mask_bounds(phi, cfg)
    y = P[..., 1]
    w = smoothstep(bot - feather * 0.5, bot + feather * 0.5, y) * (1 - smoothstep(top - feather * 0.5, top + feather * 0.5, y))
    # radial limit: the face (nose tip radius + 4.5 cm) in front, generous at the back so voluminous hair gets the whole tie band
    rmax = np.where(np.abs(phi) > np.radians(100), 0.26, cfg.get('nose_r', 0.13) + 0.045)
    return w * (r < rmax)


# ------------------------------------------------------------------------------------------------ geometry
def weld_ids(P, tol=1e-6):
    k = np.round(P / tol).astype(np.int64)
    _, inv = np.unique(k, axis=0, return_inverse=True)
    return inv.reshape(-1)


def subdivide_region(P, N, UV, F, sel_tri):
    """one red-green midpoint subdivision of the selected triangles (and the needed splits of their neighbours)."""
    wid = weld_ids(P)
    def gk(a, b):
        a, b = wid[a], wid[b]
        return (a, b) if a < b else (b, a)
    split = set()
    for t in np.where(sel_tri)[0]:
        a, b, c = F[t]
        split.add(gk(a, b)); split.add(gk(b, c)); split.add(gk(c, a))
    P, N, UV = list(P), list(N), list(UV)
    mids = {}
    def mid(a, b):
        k = (a, b) if a < b else (b, a)
        if k not in mids:
            P.append((P[a] + P[b]) / 2); n = N[a] + N[b]; N.append(n / (np.linalg.norm(n) + 1e-12)); UV.append((UV[a] + UV[b]) / 2)
            mids[k] = len(P) - 1
        return mids[k]
    out = []
    for f in F:
        a, b, c = int(f[0]), int(f[1]), int(f[2])
        s = [gk(a, b) in split, gk(b, c) in split, gk(c, a) in split]
        n = sum(s)
        if n == 0: out.append((a, b, c)); continue
        if n == 3:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            out += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]; continue
        # rotate so that the pattern is canonical
        v = [a, b, c]
        if n == 1:
            k = s.index(True); a, b, c = v[k], v[(k + 1) % 3], v[(k + 2) % 3]
            m = mid(a, b); out += [(a, m, c), (m, b, c)]
        else:
            k = s.index(False); c, a, b = v[k], v[(k + 1) % 3], v[(k + 2) % 3]   # unsplit edge is c->a
            m1, m2 = mid(a, b), mid(b, c)
            out += [(a, m1, m2), (m1, b, m2), (a, m2, c)]
    return np.array(P), np.array(N), np.array(UV), np.array(out, np.int64)


def vertex_normals(P, F):
    wid = weld_ids(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    acc = np.zeros((wid.max() + 1, 3))
    for k in range(3): np.add.at(acc, wid[F[:, k]], fn)
    n = acc[wid]
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


def drape(P, F, cfg, seed=0, thick=0.0035):
    """push lower-face / neck vertices radially onto the convex hull of the front head (cloth spans the hollows). Returns P, weight."""
    P = P.copy()
    w = region_weight(P, cfg, feather=0.012)
    ear = ear_flag(P, cfg, P)
    phi, r = cyl(P, cfg)
    near = (r < 0.13) & (P[:, 1] > cfg['chin'] - 0.07) & (P[:, 1] < cfg['eye'] + 0.01)
    hull_pts = P[near & ~ear & (np.abs(phi) < np.radians(115))]
    hull = ConvexHull(hull_pts)
    Nn, C = hull.equations[:, :3], hull.equations[:, 3]
    o = np.stack([np.zeros(len(P)), P[:, 1], np.full(len(P), cfg['axis_z'])], 1)
    d = np.stack([np.sin(phi), np.zeros(len(P)), np.cos(phi)], 1)
    sel = (w > 0) & ~ear & near
    rng = np.random.RandomState(seed)
    moved = np.zeros(len(P))
    for i in np.where(sel)[0]:
        nd = Nn @ d[i]
        ok = nd > 1e-6
        t = (-(C[ok] + Nn[ok] @ o[i])) / nd[ok]
        rh = float(t.min()) if ok.any() else r[i]
        # draping strength: full in front of the face / under the chin, fading toward the sides (cloth hugs the cheeks at the sides)
        side = 1 - smoothstep(np.radians(55), np.radians(100), abs(phi[i]))
        fold = 0.0012 * np.sin(phi[i] * 9 + P[i, 1] * 60) + 0.0008 * np.sin(-phi[i] * 5 + P[i, 1] * 110 + 1.1)
        rn = r[i] + (max(rh, r[i]) - r[i]) * side * w[i] + (thick + fold) * w[i]
        moved[i] = rn - r[i]
        P[i, 0] = np.sin(phi[i]) * rn; P[i, 2] = cfg['axis_z'] + np.cos(phi[i]) * rn
    # relax: a few Laplacian passes over the lower face (welded neighbours) close the last hairline of the lip crease
    wid = weld_ids(P)
    nbr = [set() for _ in range(wid.max() + 1)]
    for a_, b_, c_ in F:
        A, B, C = wid[a_], wid[b_], wid[c_]
        nbr[A].update((B, C)); nbr[B].update((A, C)); nbr[C].update((A, B))
    rep = np.zeros(wid.max() + 1, int); rep[wid] = np.arange(len(P))
    lower = (w > 0.3) & sel & (y < cfg['nose'] - 0.012) & (y > cfg['chin'] - 0.05) & (np.abs(phi) < np.radians(80))
    lw = np.zeros(wid.max() + 1, bool); lw[wid[lower]] = True
    Pw = np.zeros((wid.max() + 1, 3)); Pw[wid] = P
    for it in range(relax):
        Q = Pw.copy()
        for v in np.where(lw)[0]:
            n = list(nbr[v])
            if n: Q[v] = Pw[v] * 0.4 + Pw[n].mean(0) * 0.6
        Pw = Q
    chg = lw[wid]
    P[chg] = Pw[wid[chg]]
    moved = np.where(chg, np.hypot(P[:, 0], P[:, 2] - cfg['axis_z']) - r, moved)
    return P, moved


def _ray_hits_any(O, D, P, F, tmax, skip_verts=None):
    """True per ray if some triangle (not touching vertex skip_verts[i]) is hit within (2 mm, tmax] (Moller-Trumbore, chunked)."""
    P0 = P[F[:, 0]]; E1 = P[F[:, 1]] - P0; E2 = P[F[:, 2]] - P0
    hit_any = np.zeros(len(O), bool)
    wid = weld_ids(P)
    Fw = wid[F]
    for s0 in range(0, len(O), 128):
        o = O[s0:s0 + 128, None, :]; d = D[s0:s0 + 128, None, :]
        h = np.cross(d, E2[None]); a = (E1[None] * h).sum(-1)
        ok = np.abs(a) > 1e-12
        f = 1.0 / np.where(ok, a, 1); sv = o - P0[None]; u = f * (sv * h).sum(-1)
        q = np.cross(sv, E1[None]); v = f * (d * q).sum(-1); t = f * (E2[None] * q).sum(-1)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.002) & (t < tmax)
        if skip_verts is not None:
            sv_ids = wid[skip_verts[s0:s0 + 128]]
            touch = (Fw[None, :, :] == sv_ids[:, None, None]).any(-1)
            hit &= ~touch
        hit_any[s0:s0 + 128] = hit.any(1)
    return hit_any


def hang(P, F, cfg, seed=0, thick=0.0035, reach=0.05, slope=0.35, grow=0.012, sigma=0.011, relax=8, uncover_mouth=False):
    """Round 05: the mask as CLOTH, not as a skin-tight shell (critic r04: 'shrink-wrapped, lips and chin show through the cloth').
    Every vertex of the mask region takes the cloth radius
        r_cloth(s, y) = max over the head surface within `grow` sideways and from y up to y + `reach` of ( r - slope * (y' - y) )
    (cloth hangs down from the higher points: over the lips it is carried by the nose and the upper lip, under the chin it falls almost
    vertically from the jaw to the collar), Gaussian-smoothed over `sigma` (lips, chin cleft and jowl creases vanish, the nose stays a soft
    tent), then r_new = max(r + thick, r_cloth).  The displacement fades over the region weight so the lower edge merges into the neck
    without a flap.  Ears are excluded.  Returns P, moved (metres, like drape)."""
    P = P.copy()
    w = region_weight(P, cfg, feather=0.03)
    ear = ear_flag(P, cfg, P)
    phi, r = cyl(P, cfg)
    near = (r < 0.15) & (P[:, 1] > cfg['chin'] - 0.09) & (P[:, 1] < cfg['eye'] + 0.012)
    sel = (w > 0) & ~ear & near
    import os
    if os.environ.get('HANG_DEBUG'):
        box = (np.abs(P[:, 0]) < 0.035) & (P[:, 1] > cfg['nose'] - 0.05) & (P[:, 1] < cfg['nose'] - 0.005) & (P[:, 2] > 0.05)
        print('HANG box verts', int(box.sum()), 'w>0', int((w[box] > 0).sum()), 'ear', int(ear[box].sum()), 'near', int(near[box].sum()), 'sel', int(sel[box].sum()), 'cfg', {k: round(float(cfg[k]), 3) for k in ('eye', 'nose', 'chin', 'ear_lobe', 'nose_r')})
        bx = np.where(box & ~sel)[0][:12]
        for i in bx: print('  unsel', i, np.round(P[i], 4), 'w', round(float(w[i]), 3), 'r', round(float(r[i]), 3), 'near', bool(near[i]), 'ear', bool(ear[i]))
    r0 = 0.11
    s_ = phi * r0
    y = P[:, 1]
    pts = np.c_[s_, y]
    # source cloud: every region-ish vertex (the head surface under and beside the mask, ears excluded)
    src = np.where(near & ~ear & (np.abs(phi) < np.radians(125)))[0]
    tree = cKDTree(pts[src])
    env = r.copy()
    tgt = np.where(sel)[0]
    for i in tgt:
        cand = tree.query_ball_point([s_[i], y[i] + reach / 2], np.hypot(grow + 0.006, reach / 2 + 0.006))
        cand = np.asarray(src[cand], int)
        cand = cand[(np.abs(s_[cand] - s_[i]) <= grow) & (y[cand] >= y[i] - 0.004) & (y[cand] <= y[i] + reach)]
        if len(cand) == 0: continue
        env[i] = max(r[i], np.max(r[cand] - slope * np.maximum(y[cand] - y[i], 0.0)))
    # gaussian smoothing of the envelope over the selected vertices (2D, parametric space)
    t2 = cKDTree(pts[tgt])
    sm = env.copy()
    for k, i in enumerate(tgt):
        nb = np.asarray(t2.query_ball_point(pts[i], 3 * sigma), int)
        d2 = ((pts[tgt[nb]] - pts[i]) ** 2).sum(1)
        wt = np.exp(-d2 / (2 * sigma * sigma))
        sm[i] = (env[tgt[nb]] * wt).sum() / wt.sum()
    side = 1 - smoothstep(np.radians(85), np.radians(112), np.abs(phi))          # sides of the head: cloth follows the cheek / ear line
    _, botb = mask_bounds(phi, cfg)
    taper = smoothstep(botb + 0.002, botb + 0.035, y)                            # round 05b: the hem returns to the neck surface (no skirt over the collar)
    # round 05b: only the OUTERMOST shell is draped.  A vertex with another shell (hoodie collar, vest collar, hair) within 5 cm straight out is
    # under it (neck skin under a collar): moving it would push it through / tear it away from the outer shell (the tears at the mask hem).
    Dv = np.stack([np.sin(phi[tgt]), np.zeros(len(tgt)), np.cos(phi[tgt])], 1)
    covered = np.zeros(len(P), bool)
    covered[tgt] = _ray_hits_any(P[tgt] + Dv * 0.0005, Dv, P, F, 0.05, skip_verts=tgt)
    if uncover_mouth:   # round 08: the lips of a parted mouth are 'covered' by the other lip (the slit then stays as a ledge under the cloth): let them hang too
        mb = (np.abs(phi[tgt]) < np.radians(62)) & (y[tgt] > cfg['chin'] + 0.006) & (y[tgt] < cfg['nose'] - 0.004)
        covered[tgt[mb]] = False
    moved = np.zeros(len(P))
    for i in tgt:
        if covered[i]: continue
        fold = (0.0011 * np.sin(phi[i] * 8 + y[i] * 55) + 0.0007 * np.sin(-phi[i] * 5 + y[i] * 95 + 1.1)) * smoothstep(cfg['nose'] - 0.01, cfg['chin'], y[i])
        target = max(r[i] + thick, sm[i] + thick * 0.6 + fold)
        rn = r[i] + (target - r[i]) * w[i] * (0.25 + 0.75 * side[i]) * taper[i]
        moved[i] = rn - r[i]
        P[i, 0] = np.sin(phi[i]) * rn; P[i, 2] = cfg['axis_z'] + np.cos(phi[i]) * rn
    # relax: a few Laplacian passes over the lower face (welded neighbours) close the last hairline of the lip crease
    wid = weld_ids(P)
    nbr = [set() for _ in range(wid.max() + 1)]
    for a_, b_, c_ in F:
        A, B, C = wid[a_], wid[b_], wid[c_]
        nbr[A].update((B, C)); nbr[B].update((A, C)); nbr[C].update((A, B))
    rep = np.zeros(wid.max() + 1, int); rep[wid] = np.arange(len(P))
    lower = (w > 0.3) & sel & (y < cfg['nose'] - 0.012) & (y > cfg['chin'] - 0.05) & (np.abs(phi) < np.radians(80))
    lw = np.zeros(wid.max() + 1, bool); lw[wid[lower]] = True
    Pw = np.zeros((wid.max() + 1, 3)); Pw[wid] = P
    for it in range(relax):
        Q = Pw.copy()
        for v in np.where(lw)[0]:
            n = list(nbr[v])
            if n: Q[v] = Pw[v] * 0.4 + Pw[n].mean(0) * 0.6
        Pw = Q
    chg = lw[wid]
    P[chg] = Pw[wid[chg]]
    moved = np.where(chg, np.hypot(P[:, 0], P[:, 2] - cfg['axis_z']) - r, moved)
    return P, moved


def flatten_mouth(P, cfg, reach=0.011, sigma=0.007, margin=0.0008):
    """Round 08 (critic r07: 'lips show through the tee mask'): the mouth slit of a Tripo face survives the drape as a ledge because the vertices
    inside it have another shell in front of them (the lips), so hang() leaves them where they are.  Every vertex of the mouth band is raised to the
    cloth envelope: the maximum radius of any band vertex within `reach` (closing of the dents), Gaussian-smoothed over `sigma`, minus `margin`.
    Only ever moves vertices OUTWARD along their own radial direction; the lips / nose tip keep their place.  Returns P."""
    from scipy.spatial import cKDTree
    P = P.copy()
    phi, r = cyl(P, cfg)
    y = P[:, 1]
    band = (np.abs(phi) < np.radians(62)) & (y > cfg['chin'] + 0.006) & (y < cfg['nose'] - 0.004) & (r < 0.17)
    idx = np.where(band)[0]
    if len(idx) == 0: return P
    s_ = phi * 0.11
    pts = np.c_[s_[idx], y[idx]]
    tree = cKDTree(pts)
    env = r[idx].copy()
    for k, nb in enumerate(tree.query_ball_point(pts, reach)):
        env[k] = r[idx][nb].max()
    sm = env.copy()
    for k, nb in enumerate(tree.query_ball_point(pts, 3 * sigma)):
        nb = np.asarray(nb, int)
        w = np.exp(-((pts[nb] - pts[k]) ** 2).sum(1) / (2 * sigma * sigma))
        sm[k] = (env[nb] * w).sum() / w.sum()
    fade = smoothstep(np.radians(62), np.radians(48), np.abs(phi[idx])) * smoothstep(cfg['chin'] + 0.006, cfg['chin'] + 0.016, y[idx]) * smoothstep(cfg['nose'] - 0.004, cfg['nose'] - 0.012, y[idx])
    rn = np.maximum(r[idx], r[idx] + (sm - margin - r[idx]) * fade)
    P[idx, 0] = np.sin(phi[idx]) * rn
    P[idx, 2] = cfg['axis_z'] + np.cos(phi[idx]) * rn
    return P


def sink_neck(P, F, cfg, depth=0.012, top=0.475, bottom=0.44):
    """Round 08 (critic r07: 'thug collar shards'): in the running game the neck skin under a hood / jacket collar pokes through the collar as jagged
    skin-coloured wedges when the head turns (the collar and the neck are skinned to different bone mixes).  Every vertex that has another shell
    within 5 cm straight out (= the neck skin UNDER the collar) is pulled toward the head axis by up to `depth` metres, growing from 0 at y = top to
    `depth` at y = bottom, so there is slack under the cloth.  The visible neck (above the collar) is untouched.  Returns P."""
    P = P.copy()
    phi, r = cyl(P, cfg)
    y = P[:, 1]
    sel = np.where((r < 0.075) & (r > 0.02) & (y > 1.30) & (y < top + 0.02))[0]
    if len(sel) == 0: return P
    Dv = np.stack([np.sin(phi[sel]), np.zeros(len(sel)), np.cos(phi[sel])], 1)
    cov = _ray_hits_any(P[sel] + Dv * 0.0005, Dv, P, F, 0.05, skip_verts=sel)
    f = smoothstep(top, bottom, y[sel]) * cov
    rn = r[sel] - depth * f
    P[sel, 0] = np.sin(phi[sel]) * rn
    P[sel, 2] = cfg['axis_z'] + np.cos(phi[sel]) * rn
    return P


def drop_cavity(P, F, cfg, max_area=6e-5, dot=-0.3):
    """Round 05: delete the mouth / nostril cavity triangles: small back-facing triangles (normal against the radial outward direction) in the
    lower face.  They lie under the cloth and only show as a dark slit; the loops they leave are closed by fill_face_holes().
    Returns F, number dropped."""
    cen = P[F].mean(1)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    ar = np.linalg.norm(fn, axis=1) / 2
    fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-15
    phi, r = cyl(cen, cfg)
    rad = np.stack([np.sin(phi), np.zeros(len(phi)), np.cos(phi)], 1)
    inreg = (np.abs(phi) < np.radians(70)) & (r < 0.16) & (cen[:, 1] > cfg['chin'] - 0.03) & (cen[:, 1] < cfg['nose'] + 0.012)
    bad = inreg & ((fn * rad).sum(1) < dot) & (ar < max_area)
    return F[~bad], int(bad.sum())


def fill_face_holes(P, N, UV, F, cfg, max_extent=0.075):
    """Round 05: close the small open boundary loops of the lower face / neck (the Tripo mouth slit, chin and jaw tears that showed dark
    through the cloth).  Each loop that lies entirely in the mask region and is smaller than `max_extent` gets a centroid fan whose
    triangles use the boundary edges in reverse (same winding as the surface around the hole).  Returns P, N, UV, F, number filled."""
    from collections import defaultdict
    wid = weld_ids(P)
    dirn = {}
    cnt = defaultdict(int)
    for ti, (a, b, c) in enumerate(F):
        for u, v in ((a, b), (b, c), (c, a)):
            wu, wv = wid[u], wid[v]
            if wu == wv: continue
            k = (min(wu, wv), max(wu, wv)); cnt[k] += 1; dirn[k] = (u, v)
    bnd = [k for k, v in cnt.items() if v == 1]
    pos = np.zeros((wid.max() + 1, 3)); pos[wid] = P
    adj = defaultdict(list)
    for a, b in bnd:
        adj[a].append(b); adj[b].append(a)
    seen = set(); loops = []
    for s0 in adj:
        if s0 in seen: continue
        st = [s0]; comp = []
        while st:
            v = st.pop()
            if v in seen: continue
            seen.add(v); comp.append(v); st += adj[v]
        loops.append(set(comp))
    w = region_weight(P, cfg, feather=0.02)
    P, N, UV, Fl = list(P), list(N), list(UV), [tuple(f) for f in F]
    filled = 0
    for comp in loops:
        pp = pos[list(comp)]
        if (pp.max(0) - pp.min(0)).max() > max_extent or len(comp) < 3: continue
        phi, r = cyl(pp, cfg)
        inreg = (np.abs(phi) < np.radians(100)) & (r < 0.15) & (pp[:, 1] > cfg['chin'] - 0.07) & (pp[:, 1] < cfg['eye'] + 0.01)
        if not inreg.all(): continue
        edges = [k for k in bnd if k[0] in comp and k[1] in comp]
        c = pp.mean(0)
        nn = np.mean([N[np.where(wid == v)[0][0]] for v in comp], axis=0); nn /= np.linalg.norm(nn) + 1e-12
        c = pp.mean(0)
        nn = np.mean([N[np.where(wid == v)[0][0]] for v in comp], axis=0); nn /= np.linalg.norm(nn) + 1e-12
        # round 05b: one centroid vertex PER boundary edge, its uv = the mean of that edge's own two uvs, so a loop that spans several UV islands
        # (the hood's neck hole) is closed edge by edge without any triangle stretching across the atlas; edges whose endpoints sit in different
        # islands (uv distance > 0.04) are left open
        nfan = 0
        for k in edges:
            u, v = dirn[k]
            if np.abs(UV[u] - UV[v]).max() > 0.04: continue
            ci = len(P); P.append(c); N.append(nn); UV.append((UV[u] + UV[v]) / 2)
            Fl.append((v, u, ci)); nfan += 1
        if nfan == 0: continue
        filled += 1
    return np.array(P), np.array(N), np.array(UV), np.array(Fl, np.int64), filled


def fix_flips(P, F, cfg, min_area=5e-6):
    """Round 05: sub-millimetre triangles at the lips / nostrils come out of the drape with reversed winding (back-faced = a dark hole through
    the cloth).  Inside the lower face every triangle whose normal opposes the area-weighted normal of the larger triangles around it
    is flipped.  Returns F, number flipped."""
    from collections import defaultdict
    wid = weld_ids(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    ar = np.linalg.norm(fn, axis=1) / 2
    big = ar > min_area
    nrm = fn / (np.linalg.norm(fn, axis=1, keepdims=True) + 1e-15)
    acc = np.zeros((wid.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, wid[F[:, k]], nrm * (ar * big)[:, None])
    vn = acc[wid[F]].sum(1)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    cen = P[F].mean(1)
    phi, r = cyl(cen, cfg)
    inreg = (np.abs(phi) < np.radians(100)) & (r < 0.16) & (cen[:, 1] > cfg['chin'] - 0.07) & (cen[:, 1] < cfg['eye'] + 0.01)
    bad = inreg & ((nrm * vn).sum(1) < 0.0) & (ar < 12 * min_area)
    F = F.copy()
    F[bad] = F[bad][:, [0, 2, 1]]
    return F, int(bad.sum())


def _raster_cov(Q, T, W, H, org, px):
    """Coverage mask of the triangles T (vertex positions Q projected on x / y, orthographic, `px` metres per pixel)."""
    m = np.zeros((H, W), bool)
    if len(T) == 0: return m
    A = (Q[T[:, 0], :2] - org) / px; B = (Q[T[:, 1], :2] - org) / px; C = (Q[T[:, 2], :2] - org) / px
    for a_, b_, c_ in zip(A, B, C):
        x0 = int(max(0, np.floor(min(a_[0], b_[0], c_[0])))); x1 = int(min(W - 1, np.ceil(max(a_[0], b_[0], c_[0]))))
        y0 = int(max(0, np.floor(min(a_[1], b_[1], c_[1])))); y1 = int(min(H - 1, np.ceil(max(a_[1], b_[1], c_[1]))))
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
        if abs(d) < 1e-14: continue
        l1 = ((b_[1] - c_[1]) * (xs - c_[0]) + (c_[0] - b_[0]) * (ys - c_[1])) / d
        l2 = ((c_[1] - a_[1]) * (xs - c_[0]) + (a_[0] - c_[0]) * (ys - c_[1])) / d
        m[y0:y1 + 1, x0:x1 + 1] |= (l1 >= -0.02) & (l2 >= -0.02) & (l1 + l2 <= 1.02)
    return m


def flip_seethrough(P, F, cfg, azimuths=(0.0, 28.0, -28.0), px=0.0005, max_area=1.5e-5, passes=3):
    """Round 09 (critic r08: 'tee_face_4k has 3 see-through holes in the mask: 198 px, 91 px, 24 px'): the game draws single-sided, so a tiny triangle of the lip
    crease whose winding ended up reversed is a hole through which the background shows.  The lower face is rasterised orthographically from the front and from
    +-28 deg (0.5 mm pixels); every pixel inside the silhouette that only back-facing triangles cover is a see-through pixel, and the back-facing triangles (area
    < 15 mm2) that cover it are flipped.  Larger back-facing walls (a real opening) are left alone.  Returns F, number flipped."""
    from scipy import ndimage as ndi
    F = F.copy(); nflip = 0
    cen = P[F].mean(1)
    phi, r = cyl(cen, cfg)
    reg = (np.abs(phi) < np.radians(100)) & (r < 0.16) & (cen[:, 1] > cfg['chin'] - 0.07) & (cen[:, 1] < cfg['eye'] + 0.03)
    for _ in range(passes):
        ids = np.where(reg)[0]
        flipped_now = 0
        for az in azimuths:
            a = np.radians(az)
            R = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]])
            Q = P @ R.T
            T = F[ids]
            xy = Q[T.reshape(-1), :2]
            org = xy.min(0) - 0.005
            W = int((xy[:, 0].max() - org[0] + 0.01) / px) + 1; H = int((xy[:, 1].max() - org[1] + 0.01) / px) + 1
            fn = np.cross(Q[T[:, 1]] - Q[T[:, 0]], Q[T[:, 2]] - Q[T[:, 0]])
            front = fn[:, 2] > 0
            cov_front = _raster_cov(Q, T[front], W, H, org, px)
            holes = ndi.binary_fill_holes(cov_front) & ~cov_front
            holes = ndi.binary_opening(holes, structure=np.ones((2, 2), bool))                 # sub-pixel sliver noise is not a hole
            if not holes.any(): continue
            hd = ndi.binary_dilation(holes, iterations=1)
            area = np.linalg.norm(fn, axis=1) / 2
            for k in np.where(~front & (area < max_area))[0]:
                c = _raster_cov(Q, T[k:k + 1], W, H, org, px)
                if (c & hd).any():
                    F[ids[k]] = F[ids[k]][[0, 2, 1]]; flipped_now += 1
        nflip += flipped_now
        if flipped_now == 0: break
    return F, nflip


def cloth_normals(P, F, N, cfg, iters=30):
    """Round 05: shading normals of the mask region = area-weighted face normals smoothed over the welded neighbours, so the mouth-slit
    walls / nostril pits (tiny triangles facing up, down or backwards) cannot light or darken the cloth.  Returns N."""
    wid = weld_ids(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    acc = np.zeros((wid.max() + 1, 3))
    for k in range(3): np.add.at(acc, wid[F[:, k]], fn)
    nbr = [set() for _ in range(wid.max() + 1)]
    for a, b, c in F:
        A, B, C = wid[a], wid[b], wid[c]
        nbr[A].update((B, C)); nbr[B].update((A, C)); nbr[C].update((A, B))
    Pw = np.zeros((wid.max() + 1, 3)); Pw[wid] = P
    phi, r = cyl(Pw, cfg)
    w = region_weight(Pw, cfg, feather=0.012)
    act = np.where((w > 0.2) & (np.abs(phi) < np.radians(100)) & (Pw[:, 1] > cfg['chin'] - 0.07))[0]
    nw = acc / (np.linalg.norm(acc, axis=1, keepdims=True) + 1e-12)
    for _ in range(iters):
        Q = nw.copy()
        for v in act:
            n = list(nbr[v])
            if n: Q[v] = nw[v] * 0.5 + nw[n].mean(0) * 0.5
        nw = Q / (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-12)
    out = N.copy()
    chg = np.zeros(wid.max() + 1, bool); chg[act] = True
    m = chg[wid]
    out[m] = nw[wid[m]]
    return out


# ------------------------------------------------------------------------------------------------ texture
def seam_blend(img, cov, pos, band=3, radius=0.004, k=12, step=2):
    """average texels near island borders with every texel within `radius` (3D) - hides colour jumps across UV seams."""
    border = cov & ~ndi.binary_erosion(cov, iterations=band)
    src = np.zeros_like(cov); src[::step, ::step] = True; src &= cov
    sp = pos[src]; sc = img[src].astype(np.float32)
    tree = cKDTree(sp)
    bp = pos[border]
    dist, idx = tree.query(bp, k=k, distance_upper_bound=radius)
    valid = np.isfinite(dist)
    idx = np.where(valid, idx, 0)
    wgt = np.where(valid, 1.0 - dist / radius, 0.0)
    col = (sc[idx] * wgt[..., None]).sum(1) / np.maximum(wgt.sum(1, keepdims=True), 1e-6)
    out = img.astype(np.float32)
    has = wgt.sum(1) > 0.5
    cur = out[border]
    cur[has] = col[has]
    out[border] = cur
    return np.clip(out, 0, 255).astype(np.uint8), int(border.sum())


def cloth(shape, seed, base, hi):
    """plain cotton: fine weave + grain noise + low-frequency tone variation (no print)."""
    r = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(xx * 2 * np.pi / 3.2) * np.sin(yy * 2 * np.pi / 3.2)
    g = ndi.gaussian_filter(r.randn(*shape).astype(np.float32), 0.8); g /= g.std() + 1e-6
    lf = ndi.gaussian_filter(r.randn(*shape).astype(np.float32), 40); lf /= lf.std() + 1e-6
    base = np.asarray(base, np.float32); hi = np.asarray(hi, np.float32)
    return base, hi, weave, g, lf


def paint_mask(img, cov, pos, cfg, seed):
    """paint the cloth mask by 3D position; returns img, mask weight map."""
    Pm = pos.reshape(-1, 3)
    w = region_weight(pos, cfg, feather=0.003)
    w = np.where(cov, w, 0)
    ear = ear_flag(pos, cfg, Pm[cov.reshape(-1)])
    w = np.where(ear, 0, w)
    phi, r = cyl(pos, cfg)
    top, bot = mask_bounds(phi, cfg)
    y = pos[..., 1]
    base = np.asarray(cfg['mask'], np.float32); hi = np.asarray(cfg.get('mask_hi', [c * 1.35 for c in cfg['mask']]), np.float32)
    rng = np.random.RandomState(seed)
    # procedural texture evaluated in 3D (no UV-dependent tiling): weave on (arc length, height), folds as soft diagonal bands
    s = phi * np.maximum(r, 0.05)
    weave = 0.5 + 0.5 * np.sin(s * 2 * np.pi / 0.0011) * np.sin(y * 2 * np.pi / 0.0011)
    grain = ndi.gaussian_filter(rng.randn(*w.shape).astype(np.float32), 0.7); grain /= grain.std() + 1e-6
    folds = 0.5 + 0.5 * np.sin(s * 70 + (y - cfg['nose']) * 140 + 0.8 * np.sin(s * 23))
    folds2 = 0.5 + 0.5 * np.sin(-s * 45 + (y - cfg['nose']) * 95 + 2.0)
    shade = 0.80 + 0.12 * folds + 0.08 * folds2
    edge_d = np.minimum(top - y, y - bot)            # distance to the nearer edge (m)
    hem = smoothstep(0.0, 0.004, edge_d) * (1 - 0.35 * np.exp(-((edge_d - 0.0045) / 0.0012) ** 2))   # stitched rolled hem 4-5 mm in
    stitch = (np.abs(edge_d - 0.0062) < 0.0005) & (np.sin(s * 2 * np.pi / 0.004) > 0.2)
    col = base[None, None, :] * (shade * (0.88 + 0.10 * weave + 0.05 * grain) * hem)[..., None]
    col = np.where(stitch[..., None], hi[None, None, :], col)
    # lighter at the nose bridge / chin ridge (the cloth is stretched there)
    col = col * (1 + 0.10 * np.exp(-((phi / 0.35) ** 2)) * smoothstep(cfg['chin'], cfg['nose'], y))[..., None]
    out = img.astype(np.float32) * (1 - w[..., None]) + col * w[..., None]
    return np.clip(out, 0, 255).astype(np.uint8), w


def drop_loose_shells(P, F, y_min=1.655, max_tris=320, z_max=0.02):
    """Round 10 (critic r09: 'hood_face_4k has loose ribbon strands'): remove the small loose hair shells of the head -- connected components (welded at 0.1 mm) of at most max_tris triangles that lie
    entirely above y_min metres (strands above the hair line) or entirely behind z_max (strands behind the head).  The Hood's SUNGLASSES (frame 289 triangles, lenses 2 x 40, arms,
    nose pads: y 1.57 - 1.66, in front of z 0.02) are separate shells too and stay; so do the hair mass, the body and the hands.  Returns (F without those triangles, number of removed triangles)."""
    from scipy import sparse
    from scipy.sparse.csgraph import connected_components
    key = np.round(P * 1e4).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); n = inv.max() + 1
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]]])
    g = sparse.coo_matrix((np.ones(len(e)), (inv[e[:, 0]], inv[e[:, 1]])), shape=(n, n))
    nc, lab = connected_components(g, directed=False)
    fl = lab[inv[F[:, 0]]]
    sizes = np.bincount(fl, minlength=nc)
    ymin = np.full(nc, 1e9); zmax = np.full(nc, -1e9)
    np.minimum.at(ymin, fl, P[F].min(1)[:, 1]); np.maximum.at(zmax, fl, P[F].max(1)[:, 2])
    drop = (sizes <= max_tris) & ((ymin >= y_min) | (zmax <= z_max))
    keep = ~drop[fl]
    return F[keep], int((~keep).sum())


def bridge_hair_gap(P, N, UV, F, center, radius=0.07, max_gap=0.022, min_gap=0.0015, tex=None):
    """Round 10 (critic r09: 'beard_face_4k has a detached rear hair shell with a background gap'): the Beard's side-hair curtain hangs 3 - 15 mm off the edge of the head surface at the
    temple, and the sky shows through the wedge between them.  Both are open boundary chains of the (welded) mesh: the chain Y (the shorter) is bridged to the chain X whose vertices are
    nearest to it (gap between min_gap and max_gap) with a strip of triangles: for every edge of Y the two nearest X vertices (and the X vertices between them) form a fan.  The X-side
    vertices are DUPLICATED with the UV of the matching Y vertex, so the strip is hair-coloured instead of smearing skin into hair across the atlas; positions / normals are unchanged
    (skinfit gives the duplicates their weights).  Returns (P, N, UV, F, number of triangles added)."""
    from collections import defaultdict
    key = np.round(P * 1e4).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); nv = inv.max() + 1
    rep = np.zeros((nv, 3)); rep[inv] = P
    ridx = np.zeros(nv, int); ridx[inv] = np.arange(len(P))
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    a = inv[e[:, 0]]; b = inv[e[:, 1]]
    lo = np.minimum(a, b); hi = np.maximum(a, b); ek = lo.astype(np.int64) * nv + hi
    u, c = np.unique(ek, return_counts=True)
    be = [(int(k // nv), int(k % nv)) for k in u[c == 1]]
    center = np.asarray(center, float)
    near = [(x, y) for x, y in be if np.linalg.norm(rep[x] - center) < radius and np.linalg.norm(rep[y] - center) < radius]
    adj = defaultdict(list)
    for x, y in near: adj[x].append(y); adj[y].append(x)
    seen = set(); chains = []
    for s0 in adj:
        if s0 in seen: continue
        ends = None; comp = []; st = [s0]
        while st:
            v = st.pop()
            if v in seen: continue
            seen.add(v); comp.append(v); st += [w for w in adj[v] if w not in seen]
        # order the chain as a path: start from a degree-1 vertex when there is one
        deg1 = [v for v in comp if len(adj[v]) == 1]
        cur = deg1[0] if deg1 else comp[0]; order = [cur]; prev = None
        while True:
            nxt = [w for w in adj[cur] if w != prev and w not in order]
            if not nxt: break
            prev, cur = cur, nxt[0]; order.append(cur)
        chains.append(order)
    best = None
    for yi, Y in enumerate(chains):
        for xi, X in enumerate(chains):
            if xi == yi or len(Y) > len(X) or len(Y) < 3: continue
            d = np.linalg.norm(rep[Y][:, None, :] - rep[X][None, :, :], axis=2)
            m = d.min(1); ok = (m > min_gap) & (m < max_gap)
            score = int(ok.sum())
            if best is None or score > best[0]: best = (score, yi, xi)
    if best is None or best[0] < 3: return P, N, UV, F, 0
    _, yi, xi = best; Y, X = chains[yi], chains[xi]
    pos = {v: i for i, v in enumerate(X)}
    d = np.linalg.norm(rep[Y][:, None, :] - rep[X][None, :, :], axis=2); nn = d.argmin(1)
    newP, newN, newUV, newF = [], [], [], []
    base = len(P); dup = {}
    uv_flat = np.median(UV[[int(ridx[v]) for v in Y]], axis=0)      # one hair texel for the whole strip (no skin-to-hair smear across the atlas)
    if tex is not None:      # ... the darkest hair texel among the curtain's own vertices (the strip sits in the shadow between face and curtain)
        t_ = np.asarray(tex.convert('RGB'), np.float32); H_, W_ = t_.shape[:2]
        cand = UV[[int(ridx[v]) for v in Y]]
        lum = []
        for uvc in cand:
            x_, y_ = int(np.clip(uvc[0] * W_, 3, W_ - 4)), int(np.clip(uvc[1] * H_, 3, H_ - 4))
            lum.append(t_[y_ - 3:y_ + 4, x_ - 3:x_ + 4].mean())
        uv_flat = cand[int(np.argmin(lum))]
    def dupvertex(xv, uv):
        k = (xv, round(float(uv[0]), 5), round(float(uv[1]), 5))
        if k not in dup:
            dup[k] = base + len(newP); newP.append(P[ridx[xv]]); newN.append(N[ridx[xv]]); newUV.append(uv)
        return dup[k]
    def tri(a_, b_, c_):
        n_ = np.cross(P_[b_] - P_[a_], P_[c_] - P_[a_]); nn_ = N_[a_] + N_[b_] + N_[c_]
        newF.append([a_, b_, c_] if n_ @ nn_ >= 0 else [a_, c_, b_])
    P_ = lambda i: None
    allP = lambda i: P[i] if i < base else newP[i - base]
    allN = lambda i: N[i] if i < base else newN[i - base]
    def tri(a_, b_, c_):
        n_ = np.cross(allP(b_) - allP(a_), allP(c_) - allP(a_)); nn_ = allN(a_) + allN(b_) + allN(c_)
        newF.append([a_, b_, c_] if n_ @ nn_ >= 0 else [a_, c_, b_])
    for i in range(len(Y) - 1):
        y0, y1 = Y[i], Y[i + 1]
        if not (min_gap < d[i, nn[i]] < max_gap and min_gap < d[i + 1, nn[i + 1]] < max_gap): continue
        iy0, iy1 = int(ridx[y0]), int(ridx[y1]); uv0 = uv1 = uv_flat
        x0, x1 = X[nn[i]], X[nn[i + 1]]
        iy0 = dupvertex(y0, uv_flat); iy1 = dupvertex(y1, uv_flat)
        p0, p1 = pos[x0], pos[x1]
        step = 1 if p1 >= p0 else -1
        xs = [X[k] for k in range(p0, p1 + step, step)] if p0 != p1 else [x0]
        # fan: Y0 .. X(p0..p1) .. Y1  (the X vertices take the UV of the closer Y end)
        dv = [dupvertex(xv, uv0 if k < (len(xs) + 1) // 2 else uv1) for k, xv in enumerate(xs)]
        tri(iy0, iy1, dv[0] if len(dv) == 1 else dv[len(dv) // 2])
        for k in range(len(dv) - 1): tri(iy0 if k < len(dv) // 2 else iy1, dv[k], dv[k + 1])
    if not newF: return P, N, UV, F, 0
    P2 = np.concatenate([P, np.array(newP)]); N2 = np.concatenate([N, np.array(newN)]); UV2 = np.concatenate([UV, np.array(newUV)])
    F2 = np.concatenate([F, np.array(newF, dtype=F.dtype)])
    return P2, N2, UV2, F2, len(newF)
