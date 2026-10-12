#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island r04: do web ropes pass through street-tree crowns? Per telemetry frame with a rope attached (anchor != 0), the segment from the
hero's hand (body position + 0.6 m) to the anchor is tested against every tree crown of the build: the ez-tree leaf instances of
layout.json + streettrees.json (build_city.py spawns both), crown = ellipsoid fitted to the ez_street leaf protos (centre 6.2 m x scale above the
instance, radii 3.8 m x scale horizontal, 4.3 m x scale vertical), shrunk to 80 % (the dense inner crown: a rope grazing the outer leaves
is not counted). Also counts frames where the HERO body point is inside an inner crown.
usage: island_rope_canopy.py <export_dir> <telemetry.csv> [out.json]"""
import csv, json, math, os, sys
import numpy as np

SHRINK = 0.8


def crowns(E):
    L = json.load(open(os.path.join(E, 'layout.json')))
    pts = []
    for pool, v in (L.get('instances') or {}).items():
        if 'leaves' not in pool or not pool.startswith('ez'): continue
        for it in v.get('items') or []: pts.append((it['x'], it['y'], it['z'], it.get('s', 1.0)))
    sp = os.path.join(E, 'streettrees.json')
    if os.path.exists(sp):
        T = json.load(open(sp)); rm = set((round(a, 1), round(b, 1)) for a, b in T.get('_remove', []))
        for pool, its in T.items():
            if pool.startswith('_') or 'leaves' not in pool: continue
            for it in its: pts.append((it['x'], it['y'], it['z'], it.get('s', 1.0)))
        if rm: pts = [p for p in pts if (round(p[0], 1), round(p[2], 1)) not in rm]
    seen, out = set(), []
    for x, y, z, s in pts:   # l0 / l1 LOD pools share positions
        k = (round(x, 1), round(z, 1))
        if k in seen: continue
        seen.add(k); out.append((x, z, y + 6.2 * s, 3.8 * s * SHRINK, 4.3 * s * SHRINK))   # UE frame: x, y = browser z, z up
    return np.array(out, np.float64)


def seg_hits(C, a, b):
    """indices of ellipsoids (cx, cy, cz, rh, rv) the segment a-b passes through"""
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    m = (C[:, 0] + C[:, 3] > lo[0]) & (C[:, 0] - C[:, 3] < hi[0]) & (C[:, 1] + C[:, 3] > lo[1]) & (C[:, 1] - C[:, 3] < hi[1]) & (C[:, 2] + C[:, 4] > lo[2]) & (C[:, 2] - C[:, 4] < hi[2])
    idx = np.nonzero(m)[0]; hits = []
    for i in idx:
        sc = np.array([C[i, 3], C[i, 3], C[i, 4]])
        p, d = (a - C[i, :3]) / sc, (b - a) / sc
        A = d @ d; B = 2 * p @ d; Cc = p @ p - 1
        disc = B * B - 4 * A * Cc
        if disc < 0 or A < 1e-12: continue
        r = math.sqrt(disc); t0, t1 = (-B - r) / (2 * A), (-B + r) / (2 * A)
        if t1 >= 0 and t0 <= 1: hits.append(int(i))
    return hits


def main():
    E, csvp = sys.argv[1], sys.argv[2]
    C = crowns(E)
    rows = list(csv.DictReader(open(csvp)))
    rope_frames, body_frames, spans = 0, 0, []
    n_rope = 0
    for r in rows:
        t = float(r['t']); P = np.array([float(r['x_m']), float(r['y_m']), float(r['z_m'])])
        ins = [i for i in seg_hits(C, P, P + 1e-3)]
        if ins: body_frames += 1
        ax, ay, az = float(r['anchor_x']), float(r['anchor_y']), float(r['anchor_z'])
        if ax == 0 and ay == 0 and az == 0: continue
        n_rope += 1
        h = seg_hits(C, P + np.array([0, 0, 0.6]), np.array([ax, ay, az]))
        if h:
            rope_frames += 1
            if spans and t - spans[-1][1] < 0.05: spans[-1][1] = t
            else: spans.append([t, t])
    out = {'telemetry': csvp, 'crowns': int(len(C)), 'frames': len(rows), 'rope_frames': n_rope, 'rope_through_crown_frames': rope_frames,
           'rope_through_crown_spans_t': [[round(a, 3), round(b, 3)] for a, b in spans], 'hero_inside_crown_frames': body_frames,
           'pass': rope_frames == 0}
    s = json.dumps(out, indent=1)
    if len(sys.argv) > 3: open(sys.argv[3], 'w').write(s)
    print(json.dumps({k: v for k, v in out.items() if k != 'rope_through_crown_spans_t'}), 'spans', out['rope_through_crown_spans_t'][:20])


if __name__ == '__main__':
    main()
