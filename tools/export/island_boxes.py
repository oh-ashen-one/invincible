#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A): the traversal's building boxes (WHBox cubes), fitted to what is DRAWN.  Pure Python (numpy), no Unreal.

    python3 tools/export/island_boxes.py <export_dir>          -> <export_dir>/whboxes.json (+ drawn_raster.npz, cached)

The traversal (Source/WebHomage/Traversal/WebTravWorld.cpp) collides only with invisible axis-aligned /Engine/BasicShapes/Cube actors.
Round 1 of the island took them 1:1 from the browser's collision.json BOX solids (P4's Look_Boxes rule); the static audit
(island_coll_audit.py) showed what that misses on Midtown 7 x 9:
  * stepped crowns: roof tiers < 3 m tall were dropped (min-height rule)  -> the hero sinks into the top storeys;
  * round towers / water tanks are CYL solids, never boxed               -> the hero passes through them;
  * AABB boxes of angled (Broadway-cut, triangular) buildings and boxes of structures the export does not draw (park buildings,
    waterfront sheds)                                                    -> landing / running in mid-air (the owner's complaint).
Rules here:
  1. BOX solids of kind wall / bulkhead / watertower / spire / hero / glass, >= 1.2 m in one horizontal dimension, kept when
     >= 3 m tall OR a roof tier (bottom >= 3 m above the street, >= 0.4 m tall);
  2. CYL solids of those kinds -> 3 crossed boxes inscribed in the circle (angles 22.5 / 45 / 67.5 deg: covers ~96 % of the disk,
     nothing outside it), radius = the smaller of the two end radii (no overhang on a taper);
  3. drawn-coverage test on a 1 m raster of the drawn geometry (roof / detail up-facing triangles + facade / detail edge tops):
     a box >= 4 m in both dimensions whose footprint is < 15 % drawn near its top (drawn top >= box top - 2.5 m) is DROPPED (phantom);
     15-85 % drawn and >= 8 m in both dimensions -> SPLIT into the maximal rectangles of the drawn cells (min 2 x 2 m), same height;
  4. (round 1, resumed) BOX solids of kind EQUIPMENT (rooftop mechanical penthouses / plant rooms, drawn in the roofs mesh) >= 2 m in
     BOTH horizontal dimensions and >= 0.8 m tall.  Without them the audit found 5.81 % hollow cells whose drawn top sat a near-constant
     5.0 m (median 5.02 m) above the box: the hero stood inside the penthouse.  Simulated on Midtown 7 x 9: +3,411 boxes, hollow
     5.81 -> 0.22 %, phantom 0.21 -> 0.26 %.  Smaller units (AC boxes, vents; median 0.7 m) stay visual-only.
Output rows: [x0, y0, z0, x1, y1, z1, kind, source] in browser metres (x east, y up, z south); build_city.py spawn_boxes() reads it."""
import json, math, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glbio import read_glb

KEEP_KINDS = {0: 'wall', 7: 'bulkhead', 8: 'watertower', 13: 'spire', 14: 'hero', 17: 'glass'}
EQUIP_KIND, EQUIP_MIN_SIDE, EQUIP_MIN_H = 6, 2.0, 0.8
NEAR_TOP = 2.5


def raster_tris(H, T, X0, Z0):
    """max-rasterise triangles T (m,3,3) browser xyz into H[row=z-Z0, col=x-X0] with their own (interpolated) heights, 1 m cells, cell centres"""
    N0, N1 = H.shape
    for tri in T:
        xs, zs = tri[:, 0] - X0, tri[:, 2] - Z0
        c0, c1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), N1)
        r0, r1 = max(int(np.floor(zs.min())), 0), min(int(np.ceil(zs.max())), N0)
        if c1 <= c0 or r1 <= r0: continue
        cc, rr = np.meshgrid(np.arange(c0, c1) + 0.5, np.arange(r0, r1) + 0.5)
        (ax, az), (bx, bz), (qx, qz) = (xs[0], zs[0]), (xs[1], zs[1]), (xs[2], zs[2])
        d = (bz - qz) * (ax - qx) + (qx - bx) * (az - qz)
        if abs(d) < 1e-9: continue
        w0 = ((bz - qz) * (cc - qx) + (qx - bx) * (rr - qz)) / d
        w1 = ((qz - az) * (cc - qx) + (ax - qx) * (rr - qz)) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any(): continue
        h = w0 * tri[0, 1] + w1 * tri[1, 1] + w2 * tri[2, 1]
        sub = H[r0:r1, c0:c1]
        np.maximum(sub, np.where(inside, h, -np.inf), out=sub)


def scatter_edges(H, P, I, X0, Z0, step=0.5):
    """max-scatter points sampled along every triangle edge (xz length / step samples) into H; returns the number of samples"""
    NZ, NX = H.shape
    E = np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]])
    A, B = P[E[:, 0]], P[E[:, 1]]
    L = np.hypot(B[:, 0] - A[:, 0], B[:, 2] - A[:, 2])
    k = np.minimum(np.maximum(1, np.ceil(L / step)), 600).astype(int)
    tot = 0
    for kk in np.unique(k):
        m = k == kk
        t = np.linspace(0, 1, kk + 1)[None, :, None]
        Q = (A[m][:, None, :] * (1 - t) + B[m][:, None, :] * t).reshape(-1, 3)
        col = np.floor(Q[:, 0] - X0).astype(int); row = np.floor(Q[:, 2] - Z0).astype(int)
        ok = (col >= 0) & (col < NX) & (row >= 0) & (row < NZ) & (Q[:, 1] > 2.0)
        np.maximum.at(H, (row[ok], col[ok]), Q[ok, 1].astype(np.float32)); tot += int(ok.sum())
    return tot


def up_tris(P, I, min_area=0.0, min_y=2.0):
    T = P[I]
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nn = np.linalg.norm(nrm, axis=1)
    up = (np.abs(nrm[:, 1]) > 0.7 * np.maximum(nn, 1e-9)) & (T[:, :, 1].min(axis=1) > min_y) & (nn > max(2 * min_area, 1e-6))
    return T[up]


def drawn_rasters(E, force=False):
    """-> (reg, Hv, Ha): Hv = roofs + facades (building mass as drawn), Ha = Hv + detail / landmark / signage meshes (everything drawn)"""
    cache = os.path.join(E, 'drawn_raster.npz')
    M = json.load(open(os.path.join(E, 'manifest.json'))); reg = M['region']
    if os.path.exists(cache) and not force and os.path.getmtime(cache) > os.path.getmtime(os.path.join(E, 'manifest.json')):
        z = np.load(cache); return reg, z['hv'].astype(np.float32), z['ha'].astype(np.float32)
    X0, Z0 = reg['x0'], reg['z0']; NX, NZ = int(reg['x1'] - X0), int(reg['z1'] - Z0)
    Hv = np.full((NZ, NX), -np.inf, np.float32); Ha = np.full((NZ, NX), -np.inf, np.float32)
    t0 = time.time()
    for r in M['meshes']:
        if r.get('lod') or r['name'].startswith('facadeLod') or r['kind'] in ('far', 'land', 'asphalt', 'sidewalk', 'markings'): continue
        if r['kind'] not in ('roofs', 'facade', 'detail', 'generic', 'signage'): continue
        c = r.get('center') or [0, 0, 0]
        g = read_glb(os.path.join(E, r['file'])); P = g['attrs']['POSITION'].copy(); P[:, 0] += c[0]; P[:, 2] += c[2]
        I = g['index'].reshape(-1, 3)
        if r['kind'] == 'roofs': raster_tris(Hv, up_tris(P, I), X0, Z0)
        elif r['kind'] == 'facade': scatter_edges(Hv, P, I, X0, Z0)
        else:
            raster_tris(Ha, up_tris(P, I, min_area=2.0), X0, Z0)
            scatter_edges(Ha, P, I, X0, Z0, step=1.0)
    hv = np.where(np.isfinite(Hv), Hv, 0.0).astype(np.float32); ha = np.maximum(hv, np.where(np.isfinite(Ha), Ha, 0.0)).astype(np.float32)
    np.savez_compressed(cache, hv=hv.astype(np.float16), ha=ha.astype(np.float16))
    print('[island_boxes] drawn raster %d x %d m in %.0f s' % (NX, NZ, time.time() - t0))
    return reg, hv, ha


def max_rects(mask, min_side=2, max_rects=16, stop_frac=0.08):
    """greedy cover of a boolean mask by maximal rectangles (largest first) -> [(r0, c0, r1, c1)] exclusive ends"""
    m = mask.copy(); total = m.sum(); out = []
    while m.sum() > stop_frac * total and len(out) < max_rects:
        best = (0, None); h = np.zeros(m.shape[1], int)
        for r in range(m.shape[0]):
            h = np.where(m[r], h + 1, 0)
            st = []   # histogram largest rectangle
            for c in range(len(h) + 1):
                hc = h[c] if c < len(h) else 0
                start = c
                while st and st[-1][1] >= hc:
                    s, sh = st.pop()
                    area = sh * (c - s)
                    if area > best[0] and sh >= min_side and (c - s) >= min_side: best = (area, (r - sh + 1, s, r + 1, c))
                    start = s
                st.append((start, hc))
        if not best[1]: break
        r0, c0, r1, c1 = best[1]; out.append(best[1]); m[r0:r1, c0:c1] = False
    return out


def select(E, use_raster=True):
    C = json.load(open(os.path.join(E, 'collision.json')))
    rows, stats = [], {'box_in': 0, 'tiers_kept': 0, 'cyl': 0, 'equipment': 0, 'dropped_phantom': 0, 'split': 0, 'split_rects': 0}
    for s in C['solids']:
        if s['k'] == EQUIP_KIND and s['t'] == 0:
            x0, y0, z0, x1, y1, z1 = s['bb']
            if min(x1 - x0, z1 - z0) >= EQUIP_MIN_SIDE and (y1 - y0) >= EQUIP_MIN_H:
                rows.append([x0, y0, z0, x1, y1, z1, 'equipment', 'equip']); stats['equipment'] += 1
            continue
        if s['k'] not in KEEP_KINDS: continue
        x0, y0, z0, x1, y1, z1 = s['bb']
        if s['t'] == 0:
            if (x1 - x0) < 1.2 and (z1 - z0) < 1.2: continue
            h = y1 - y0
            if h >= 3.0: rows.append([x0, y0, z0, x1, y1, z1, KEEP_KINDS[s['k']], 'box']); stats['box_in'] += 1
            elif y0 >= 3.0 and h >= 0.4: rows.append([x0, y0, z0, x1, y1, z1, KEEP_KINDS[s['k']], 'tier']); stats['tiers_kept'] += 1
        elif s['t'] == 1:   # CYL: par = [cx, cz, r_bottom, r_top, ...]
            cx, cz, ra, rb = s['p'][0], s['p'][1], s['p'][2], s['p'][3]
            r = min(ra, rb) if min(ra, rb) > 0.3 else max(ra, rb)
            if r < 0.6 or (y1 - y0) < 0.8: continue
            for a in (22.5, 45.0, 67.5):
                hx, hz = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
                rows.append([cx - hx, y0, cz - hz, cx + hx, y1, cz + hz, KEEP_KINDS[s['k']], 'cyl'])
            stats['cyl'] += 1
    if not use_raster: return rows, stats
    reg, hv, ha = drawn_rasters(E)
    X0, Z0 = reg['x0'], reg['z0']; NZ, NX = ha.shape
    out = []
    for b in rows:
        x0, y0, z0, x1, y1, z1, k, src = b
        if src != 'box' or (x1 - x0) < 4.0 or (z1 - z0) < 4.0: out.append(b); continue
        c0, c1 = int(round(x0 - X0)), int(round(x1 - X0)); r0, r1 = int(round(z0 - Z0)), int(round(z1 - Z0))
        c0, c1, r0, r1 = max(c0, 0), min(c1, NX), max(r0, 0), min(r1, NZ)
        if c1 - c0 < 2 or r1 - r0 < 2: out.append(b); continue
        drawn = ha[r0:r1, c0:c1] >= y1 - NEAR_TOP
        cov = float(drawn.mean())
        if cov < 0.15: stats['dropped_phantom'] += 1; continue
        if cov >= 0.85 or (x1 - x0) < 8.0 or (z1 - z0) < 8.0: out.append(b); continue
        # fill 1-cell holes (windows / edge sampling) before the rectangle cover
        d = drawn.copy(); d[1:-1, 1:-1] |= (drawn[:-2, 1:-1] & drawn[2:, 1:-1]) | (drawn[1:-1, :-2] & drawn[1:-1, 2:])
        rects = max_rects(d)
        if not rects: stats['dropped_phantom'] += 1; continue
        stats['split'] += 1; stats['split_rects'] += len(rects)
        for (a0, b0, a1, b1) in rects:
            out.append([X0 + c0 + b0, y0, Z0 + r0 + a0, X0 + c0 + b1, y1, Z0 + r0 + a1, k, 'split'])
    return out, stats


FILL_MIN_CELLS, FILL_PASSES, FILL_PCT = 16, 3, 10


def box_raster(rows, reg, shape):
    """highest box top per 1 m cell, the audit's (island_coll_audit.py) cell rounding"""
    X0, Z0 = reg['x0'], reg['z0']; NZ, NX = shape
    Hb = np.zeros((NZ, NX), np.float32)
    for x0, y0, z0, x1, y1, z1, *_ in rows:
        c0, c1 = max(int(np.floor(x0 - X0 + 0.5)), 0), min(int(np.floor(x1 - X0 + 0.5)), NX)
        r0, r1 = max(int(np.floor(z0 - Z0 + 0.5)), 0), min(int(np.floor(z1 - Z0 + 0.5)), NZ)
        if c1 > c0 and r1 > r0: np.maximum(Hb[r0:r1, c0:c1], y1, out=Hb[r0:r1, c0:c1])
    return Hb


def fill_hollow(rows, reg, hv, stats):
    """(island r04) rule 5: drawn building mass with no box under it (hv > 3 m and > box top + 1.5 m) that is NOT a 1-2 m facade rim of a box
    (a box within 2 cells already reaches that height), in 8-connected patches >= 16 m2: covered by maximal rectangles (min 2 x 2 m) with
    top = the 10th percentile of the drawn top in the rectangle (never above most of what is drawn), bottom 0; up to 3 passes for stepped
    roofs. Round 03's audit: 3.64 % of the island's building cells were such hollows (west-side pier sheds 11-15 m, stepped crowns,
    buildings whose solid is not a kept kind); they had no anchor / roof index."""
    from scipy import ndimage
    X0, Z0 = reg['x0'], reg['z0']; NZ, NX = hv.shape
    added = []
    for ps in range(FILL_PASSES):
        Hb = box_raster(rows + added, reg, hv.shape)
        hol = (hv > 3.0) & (hv > Hb + 1.5)
        P = np.pad(Hb, 2)
        nmax = np.max(np.stack([P[2 + dy:2 + dy + NZ, 2 + dx:2 + dx + NX] for dy in range(-2, 3) for dx in range(-2, 3)]), 0)
        cand = hol & ~(nmax >= hv - 1.5)
        lab, n = ndimage.label(cand, structure=np.ones((3, 3), bool))
        if not n: break
        sizes = np.bincount(lab.ravel()); sl = ndimage.find_objects(lab)
        k0 = len(added)
        for i in range(1, n + 1):
            if sizes[i] < FILL_MIN_CELLS: continue
            s = sl[i - 1]; m = lab[s] == i
            for (a0, b0, a1, b1) in max_rects(m, min_side=2, max_rects=24, stop_frac=0.1):
                cells = m[a0:a1, b0:b1]
                h = hv[s][a0:a1, b0:b1][cells]
                if h.size < 4: continue
                top = float(np.percentile(h, FILL_PCT))
                if top <= 3.0: continue
                added.append([X0 + s[1].start + b0, 0.0, Z0 + s[0].start + a0, X0 + s[1].start + b1, round(top, 3), Z0 + s[0].start + a1, 'drawn', 'fill'])
        stats['fill_pass%d' % ps] = len(added) - k0
        if len(added) == k0: break
    stats['fill'] = len(added)
    return rows + added


def main():
    E = sys.argv[1]
    t0 = time.time()
    rows, stats = select(E)
    if os.environ.get('ISLAND_BOX_FILL', '1') == '1':
        reg, hv, ha = drawn_rasters(E)
        rows = fill_hollow(rows, reg, hv, stats)
    rows = [[round(float(v), 3) for v in r[:6]] + [str(r[6]), str(r[7])] for r in rows]
    json.dump({'note': 'WHBox cubes, browser metres [x0, y0, z0, x1, y1, z1, kind, source]; tools/export/island_boxes.py', 'stats': stats, 'boxes': rows},
              open(os.path.join(E, 'whboxes.json'), 'w'))
    print('[island_boxes] %d boxes in %.0f s %s' % (len(rows), time.time() - t0, json.dumps(stats)))


if __name__ == '__main__':
    main()
