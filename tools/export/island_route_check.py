#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A): route check of a traversal telemetry CSV (Source/WebHomage/Traversal/WebTravScript: -WHTravScript + -WHTravCsv) against the
city export the map was built from.  Answers the M1 acceptance questions for one route:

  fall-through  feet below the water plane (z < -2 m), or the body deep inside a WHBox (>= 0.6 m from every face) for >= 0.15 s
  stuck         moving input held (stick / swing / zip) but speed < 0.4 m/s for >= 1.0 s (perch / idle without input is fine)
  mid-air       a SUPPORTED mode (ground / perch / land) with no surface under the feet: neither a WHBox top (footprint contains the feet,
                top within 0.45 m) nor the street (feet <= 0.5 m) -- or a box top that is a phantom (drawn roof > 1.5 m lower, coll_audit grid)
  wall-air      wall mode with no box face within 1.2 m of the feet
  web-air       a web anchor (anchor_x/y/z while swinging, zt_x/y/z zip target) farther than 1.0 m from every WHBox and above the street
                (z > 0.5 m): a web stuck to nothing; counted once per distinct anchor
  facadeLod     distance from every hero position to the nearest facadeLod (bare-mass) tile of the build (target: none within 1.2 km)
(island r02, traversal r20 "collision = drawn triangles": the WHBox cubes are only an index now) DRAWN-surface checks:
  mid_air_drawn   a SUPPORTED frame whose feet have no DRAWN surface within 0.45 m: street, drawn_raster.npz tops (hv / ha, 3 x 3 cells),
                  collision.json solid tops (footprint + capsule radius), fire-escape kit platforms (mesh/fireescape/*.glb up-facing quads)
  feet_overlap    frames where the hero capsule (R 0.36 m, feet + 0.05 .. feet + 1.8 m) penetrates >= 0.08 m into a parapet / coping /
                  fire-escape / trunk solid of collision.json (+ UE-only kit fire-escape decks and street-tree trunks); feet_point_inside = the
                  feet column itself inside the solid
  wall_air_drawn  wall mode with no collision.json solid / drawn raster mass within 1.2 m of the feet or hips
  web_air_drawn   a web / zip anchor (z > 0.5 m) with no WHBox, no collision.json solid and no drawn raster mass within 1.0 m
  swing           critic test 1: per web release (web_on 1 -> 0) the time to the next web (web_on 0 -> 1); ground + land share of frames;
                  distinct swing anchors
  land_events     every landing (mode -> land): feet height above the nearest drawn surface under the feet and what it is

    python3 tools/export/island_route_check.py <export_dir> <telemetry.csv> [more.csv ...] [--out report.json]

Telemetry units: UE metres (x east, y south = browser z, z up = browser y)."""
import csv, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from island_coll_audit import boxes_of

SUPPORTED = ('ground', 'perch', 'land')
# (island r01 resume) x_m / y_m / z_m are the traversal BODY CENTRE, UWebTraversalComponent::H = 0.95 m above the feet
# (WebTravCharacter.cpp: PosM = capsule bottom / 100 + H). The first version compared z_m with box tops / the street as if it were the feet,
# which flagged every street frame (z_m = 0.95) as mid-air and would have missed real roof floats by 0.95 m.
BODY_H = 0.95


def load_boxes(E):
    B = np.array([[b[0], b[2], b[1], b[3], b[5], b[4]] for b in boxes_of(E)], np.float64)  # -> UE metres: x0, y0(=z0), z0(=y0), x1, y1, z1
    return B


def lod_tiles(E):
    M = json.load(open(os.path.join(E, 'manifest.json')))
    T = []
    for r in M['meshes']:
        if r['name'].startswith('facadeLod'):
            c = r['center']; T.append((c[0] - 128, c[2] - 128, c[0] + 128, c[2] + 128))
    return np.array(T, np.float64) if T else np.zeros((0, 4))


R_CAP, CAP_H, PEN = 0.36, 1.8, 0.08
SUP_KINDS = ('wall', 'roof', 'parapet', 'coping', 'cornice', 'ledge', 'equipment', 'bulkhead', 'watertower', 'fireescape', 'skylight', 'spire', 'hero',
             'park', 'pier', 'glass')
OVL_KINDS = ('parapet', 'coping', 'fireescape', 'trunk')
# (island r04) landing strips beside the stair wells / ladder hatches are 0.15-0.35 m2 (street_kit.py r04): count them (r03: 0.5 m2 = whole landings only)
KIT_MIN_AREA = float(os.environ.get('ISLAND_KIT_MIN_AREA', '0.12'))


class Drawn:
    """(island r02) what is drawn, for the r20 checks: raster tops + collision.json solids + kit fire-escape platforms + UE street-tree trunks"""
    CELL = 8.0

    def __init__(self, E):
        import glob
        from glbio import read_glb
        M = json.load(open(os.path.join(E, 'manifest.json'))); self.reg = M['region']
        z = np.load(os.path.join(E, 'drawn_raster.npz')); self.hv = z['hv'].astype(np.float32); self.ha = z['ha'].astype(np.float32)
        C = json.load(open(os.path.join(E, 'collision.json'))); K = C['surfaceKinds']; T = C['kinds']
        rows = []   # x0, y0, z0, x1, y1, z1 (UE metres: y = browser z, z = up), kind, shape (0 box, 1 cyl)
        for sd in C['solids']:
            k = K[sd['k']]; t = T[sd['t']]
            if t not in ('BOX', 'CYL') or (k not in SUP_KINDS and k not in OVL_KINDS): continue
            x0, y0, z0, x1, y1, z1 = sd['bb']
            rows.append((x0, z0, y0, x1, z1, y1, k, 1 if t == 'CYL' else 0))
        n_kit = 0
        for f in sorted(glob.glob(os.path.join(E, 'mesh', 'fireescape', 'fireescape__t*.glb'))):
            if os.path.basename(f).startswith('._'): continue
            g = read_glb(f); P = g['attrs']['POSITION']; N = g['attrs']['NORMAL']
            c = [r['center'] for r in json.load(open(os.path.join(E, 'streetkit.json')))['fireescape_files'] if os.path.basename(r['file']) == os.path.basename(f)][0]
            Q = P.reshape(-1, 4, 3); NQ = N.reshape(-1, 4, 3)[:, 0]
            up = (NQ[:, 1] > 0.9)
            for q in Q[up]:
                lo, hi = q.min(0), q.max(0)
                if hi[1] - lo[1] > 0.05 or (hi[0] - lo[0]) * (hi[2] - lo[2]) < KIT_MIN_AREA: continue   # stairs (sloped) / tiny caps
                rows.append((lo[0] + c[0], lo[2] + c[2], hi[1] - 0.08, hi[0] + c[0], hi[2] + c[2], hi[1], 'fireescape_kit', 0)); n_kit += 1
        n_tr = 0
        sp = os.path.join(E, 'streettrees.json')
        if os.path.exists(sp):
            seen = set()
            for pool, its in json.load(open(sp)).items():
                if not pool.endswith('-bark'): continue   # one trunk per tree position (the l0 / l1 LOD pools share positions)
                for it in its:
                    key = (round(it['x'], 1), round(it['z'], 1))
                    if key in seen: continue
                    seen.add(key); r = 0.2 * it.get('s', 1.0)
                    rows.append((it['x'] - r, it['z'] - r, it['y'], it['x'] + r, it['z'] + r, it['y'] + 3.0, 'trunk_ue', 1)); n_tr += 1
        self.S = np.array([r[:6] for r in rows], np.float64); self.k = np.array([r[6] for r in rows]); self.cyl = np.array([r[7] for r in rows], bool)
        self.grid = {}
        for i, (x0, y0, _, x1, y1, _) in enumerate(self.S):
            for gx in range(int(math.floor((x0 - 1) / self.CELL)), int(math.floor((x1 + 1) / self.CELL)) + 1):
                for gy in range(int(math.floor((y0 - 1) / self.CELL)), int(math.floor((y1 + 1) / self.CELL)) + 1):
                    self.grid.setdefault((gx, gy), []).append(i)
        self.grid = {k: np.array(v, np.int64) for k, v in self.grid.items()}
        self.counts = {'solids': len(rows), 'kit_fireescape_platforms': n_kit, 'ue_street_trunks': n_tr}

    def near(self, x, y):
        return self.grid.get((int(math.floor(x / self.CELL)), int(math.floor(y / self.CELL))), np.zeros(0, np.int64))

    def raster_tops(self, x, y):
        c, r = int(math.floor(x - self.reg['x0'])), int(math.floor(y - self.reg['z0']))
        out = []
        for a in (self.hv, self.ha):
            if 0 <= r < a.shape[0] and 0 <= c < a.shape[1]:
                out.append(a[max(0, r - 1):r + 2, max(0, c - 1):c + 2].ravel())
        return np.concatenate(out) if out else np.zeros(0)

    def support(self, x, y, z, tol=0.45):
        """-> (what, dz) of the nearest drawn surface under / at the feet within tol, else (None, best dz)"""
        if z <= 0.5: return 'street', z
        best = (None, math.inf)
        idx = self.near(x, y)
        if idx.size:
            S = self.S[idx]
            inx = (S[:, 0] - R_CAP <= x) & (x <= S[:, 3] + R_CAP) & (S[:, 1] - R_CAP <= y) & (y <= S[:, 4] + R_CAP)
            if inx.any():
                d = np.abs(S[inx, 5] - z); j = int(np.argmin(d))
                if d[j] < best[1]: best = (str(self.k[idx][inx][j]), float(d[j]))
        t = self.raster_tops(x, y)
        if t.size:
            d = np.abs(t - z); j = float(np.min(d))
            if j < best[1]: best = ('drawn_top', j)
        return (best[0], best[1]) if best[1] <= tol else (None, best[1])

    def overlap(self, x, y, z):
        """-> list of (kind, penetration_m, feet_point_inside) for parapet / coping / fire-escape / trunk solids the capsule penetrates"""
        idx = self.near(x, y); out = []
        if not idx.size: return out
        S = self.S[idx]; kk = self.k[idx]; cy = self.cyl[idx]
        sel = np.isin(kk, OVL_KINDS + ('fireescape_kit', 'trunk_ue'))
        lo, hi = z + 0.05, z + CAP_H
        sel &= (S[:, 2] < hi) & (S[:, 5] > lo)
        for i in np.nonzero(sel)[0]:
            x0, y0, z0, x1, y1, z1 = S[i]
            if cy[i]:
                cx, cyy, rc = (x0 + x1) / 2, (y0 + y1) / 2, min(x1 - x0, y1 - y0) / 2
                d = math.hypot(x - cx, y - cyy) - rc; inside = d < 0
            else:
                dx = max(x0 - x, 0.0, x - x1); dy = max(y0 - y, 0.0, y - y1); d = math.hypot(dx, dy); inside = d == 0.0
                if inside: d = -min(x - x0, x1 - x, y - y0, y1 - y)
            # a solid whose top is at / below the feet + step is something the hero stands on or steps over, not a penetration
            if z1 <= z + 0.1: continue
            pen = R_CAP - d
            if pen >= PEN: out.append((str(kk[i]), round(float(pen), 3), bool(inside)))
        return out

    def mass_near(self, ax, ay, az, rad=1.0):
        idx = self.near(ax, ay)
        if idx.size:
            S = self.S[idx]
            dx = np.maximum(np.maximum(S[:, 0] - ax, ax - S[:, 3]), 0); dy = np.maximum(np.maximum(S[:, 1] - ay, ay - S[:, 4]), 0)
            dz = np.maximum(np.maximum(S[:, 2] - az, az - S[:, 5]), 0)
            if float(np.min(np.sqrt(dx * dx + dy * dy + dz * dz))) <= rad: return True
        t = self.raster_tops(ax, ay)
        return bool(t.size and float(np.max(t)) >= az - rad)


def check(E, csv_path, B, L, audit_hv=None, reg=None, D=None):
    rows = list(csv.DictReader(open(csv_path)))
    f = lambda r, k: float(r[k]) if r.get(k) not in (None, '') else 0.0
    ev = {'fall_through': [], 'stuck': [], 'mid_air': [], 'wall_air': [], 'web_air': []}
    seen_anchor = set(); n_anchor = 0
    inside_t = 0.0; stuck_t = 0.0; prev_t = None; lod_min = math.inf
    n_sup = 0
    ex = {'mid_air_drawn': [], 'feet_overlap': [], 'web_air_drawn': [], 'wall_air_drawn': [], 'land_events': []}
    ovl_kinds = {}; n_point_inside = 0
    seen_anchor_d = set(); swing_anchors = set()
    web_prev = None; release_t = None; gaps = []; n_gl = 0; prev_mode = None
    for r in rows:
        t = f(r, 't'); dt = 0.0 if prev_t is None else max(0.0, t - prev_t); prev_t = t
        x, y, zc = f(r, 'x_m'), f(r, 'y_m'), f(r, 'z_m'); mode = r['mode']
        z = zc - BODY_H   # feet
        if len(L):
            dx = np.maximum(np.maximum(L[:, 0] - x, x - L[:, 2]), 0); dy = np.maximum(np.maximum(L[:, 1] - y, y - L[:, 3]), 0)
            lod_min = min(lod_min, float(np.min(np.hypot(dx, dy))))
        # boxes containing the feet column
        inxy = (B[:, 0] <= x) & (x <= B[:, 3]) & (B[:, 1] <= y) & (y <= B[:, 4])
        # fall-through
        if z < -2.0: ev['fall_through'].append([round(t, 3), 'below water', round(z, 2)])
        mid = z + 0.9
        deep = inxy & (B[:, 2] + 0.6 < mid) & (mid < B[:, 5] - 0.6) & (B[:, 0] + 0.6 < x) & (x < B[:, 3] - 0.6) & (B[:, 1] + 0.6 < y) & (y < B[:, 4] - 0.6)
        if deep.any() and mode != 'wall':
            inside_t += dt
            if inside_t >= 0.15 and (not ev['fall_through'] or ev['fall_through'][-1][1] != 'inside box' or t - ev['fall_through'][-1][0] > 1.0):
                ev['fall_through'].append([round(t, 3), 'inside box', round(z, 2)])
        else: inside_t = 0.0
        # stuck
        moving_input = abs(f(r, 'in_move_x')) + abs(f(r, 'in_move_y')) > 0.2 or f(r, 'in_swing') > 0.5 or f(r, 'in_zip') > 0.5
        if moving_input and f(r, 'speed_mps') < 0.4 and mode not in ('perch',):
            stuck_t += dt
            if stuck_t >= 1.0 and (not ev['stuck'] or t - ev['stuck'][-1][0] > 1.0): ev['stuck'].append([round(t, 3), mode, round(x, 1), round(y, 1), round(z, 1)])
        else: stuck_t = 0.0
        # mid-air on a supported mode
        if mode in SUPPORTED:
            n_sup += 1
            tops = B[inxy, 5] if inxy.any() else np.zeros(0)
            near_box = tops.size and np.min(np.abs(tops - z)) <= 0.45
            street = z <= 0.5
            phantom = False
            if near_box and audit_hv is not None and reg is not None:
                c, rw = int(x - reg['x0']), int(y - reg['z0'])
                if 0 <= rw < audit_hv.shape[0] and 0 <= c < audit_hv.shape[1]:
                    phantom = float(audit_hv[rw, c]) < z - 1.5
            if not (near_box or street) or phantom:
                ev['mid_air'].append([round(t, 3), mode, r['sub'], round(x, 1), round(y, 1), round(z, 2), 'phantom box' if phantom else 'no surface'])
        for kx, ky, kz in (('anchor_x', 'anchor_y', 'anchor_z'), ('zt_x', 'zt_y', 'zt_z')):
            ax, ay, az = f(r, kx), f(r, ky), f(r, kz)
            if ax == 0.0 and ay == 0.0 and az == 0.0: continue
            k = (round(ax, 1), round(ay, 1), round(az, 1))
            if k in seen_anchor: continue
            seen_anchor.add(k); n_anchor += 1
            if az <= 0.5: continue
            dx = np.maximum(np.maximum(B[:, 0] - ax, ax - B[:, 3]), 0); dy = np.maximum(np.maximum(B[:, 1] - ay, ay - B[:, 4]), 0)
            dz = np.maximum(np.maximum(B[:, 2] - az, az - B[:, 5]), 0)
            dmin = float(np.min(np.sqrt(dx * dx + dy * dy + dz * dz))) if len(B) else math.inf
            if dmin > 1.0: ev['web_air'].append([round(t, 3), kx[:-2], round(ax, 1), round(ay, 1), round(az, 1), round(dmin, 2)])
        if D is not None:
            if mode in SUPPORTED:
                what, dz = D.support(x, y, z)
                if what is None: ex['mid_air_drawn'].append([round(t, 3), mode, r['sub'], round(x, 2), round(y, 2), round(z, 2), round(dz, 2)])
            if mode == 'land' and prev_mode != 'land':
                what, dz = D.support(x, y, z, tol=0.45)
                ex['land_events'].append([round(t, 3), round(x, 2), round(y, 2), round(z, 2), what, round(dz, 2)])
            if mode == 'wall' and not (D.mass_near(x, y, z + 0.9, rad=1.2) or D.mass_near(x, y, z + 0.1, rad=1.2)):
                ex['wall_air_drawn'].append([round(t, 3), round(x, 2), round(y, 2), round(z, 2)])
            ov = D.overlap(x, y, z)
            if ov:
                ex['feet_overlap'].append([round(t, 3), mode, round(x, 3), round(y, 3), round(z, 2), ov[:3]])
                for k_, _, ins in ov: ovl_kinds[k_] = ovl_kinds.get(k_, 0) + 1
                n_point_inside += int(any(o[2] for o in ov))
            for kx, ky, kz in (('anchor_x', 'anchor_y', 'anchor_z'), ('zt_x', 'zt_y', 'zt_z')):
                ax, ay, az = f(r, kx), f(r, ky), f(r, kz)
                if (ax == 0.0 and ay == 0.0 and az == 0.0) or az <= 0.5: continue
                kk_ = (round(ax, 1), round(ay, 1), round(az, 1))
                if kx == 'anchor_x' and f(r, 'web_on') > 0.5: swing_anchors.add(kk_)
                if kk_ in seen_anchor_d: continue
                seen_anchor_d.add(kk_)
                boxd = np.min(np.sqrt(np.maximum(np.maximum(B[:, 0] - ax, ax - B[:, 3]), 0) ** 2 + np.maximum(np.maximum(B[:, 1] - ay, ay - B[:, 4]), 0) ** 2
                                      + np.maximum(np.maximum(B[:, 2] - az, az - B[:, 5]), 0) ** 2)) if len(B) else math.inf
                if boxd > 1.0 and not D.mass_near(ax, ay, az): ex['web_air_drawn'].append([round(t, 3), kx[:-2], round(ax, 1), round(ay, 1), round(az, 1)])
            web = f(r, 'web_on') > 0.5 if 'web_on' in r else mode == 'swing'
            if web_prev is not None:
                if web_prev and not web: release_t = t
                elif web and not web_prev and release_t is not None: gaps.append([round(release_t, 3), round(t - release_t, 3)]); release_t = None
            web_prev = web
            if mode in ('ground', 'land'): n_gl += 1
        prev_mode = mode
        if mode == 'wall':
            near = (B[:, 0] - 1.2 <= x) & (x <= B[:, 3] + 1.2) & (B[:, 1] - 1.2 <= y) & (y <= B[:, 4] + 1.2) & (B[:, 2] - 0.5 <= z) & (z <= B[:, 5] + 0.5)
            if not near.any(): ev['wall_air'].append([round(t, 3), round(x, 1), round(y, 1), round(z, 2)])
    dur = f(rows[-1], 't') - f(rows[0], 't') if rows else 0
    path = sum(math.dist((f(a, 'x_m'), f(a, 'y_m'), f(a, 'z_m')), (f(b, 'x_m'), f(b, 'y_m'), f(b, 'z_m'))) for a, b in zip(rows, rows[1:]))
    modes = {}
    for r in rows: modes[r['mode']] = modes.get(r['mode'], 0) + 1
    return {'csv': os.path.basename(csv_path), 'frames': len(rows), 'seconds': round(dur, 2), 'path_m': round(path, 1), 'modes': modes,
            'supported_frames': n_sup, 'fall_through': len(ev['fall_through']), 'stuck': len(ev['stuck']), 'mid_air_frames': len(ev['mid_air']),
            'wall_air_frames': len(ev['wall_air']), 'anchors': n_anchor, 'web_air': len(ev['web_air']), 'facadeLod_min_dist_m': None if lod_min == math.inf else round(lod_min, 1), 'events': ev,
            'drawn': None if D is None else {
                'mid_air_drawn_frames': len(ex['mid_air_drawn']), 'feet_overlap_frames': len(ex['feet_overlap']), 'feet_overlap_by_kind': ovl_kinds,
                'feet_point_inside_frames': n_point_inside, 'web_air_drawn': len(ex['web_air_drawn']), 'wall_air_drawn_frames': len(ex['wall_air_drawn']),
                'swing': {'releases_rewebbed': len(gaps), 'unanswered_release_at_s': None if release_t is None else round(release_t, 3),
                          'max_reweb_gap_s': max((g[1] for g in gaps), default=None), 'reweb_gaps_over_0_5s': sum(1 for g in gaps if g[1] > 0.5),
                          'ground_land_frac': round(n_gl / max(1, len(rows)), 4), 'distinct_swing_anchors': len(swing_anchors), 'gaps': gaps},
                'land_events': ex['land_events'], 'events': {k: v[:200] for k, v in ex.items() if k != 'land_events'}},
            'start': [f(rows[0], 'x_m'), f(rows[0], 'y_m'), f(rows[0], 'z_m')] if rows else None,
            'end': [f(rows[-1], 'x_m'), f(rows[-1], 'y_m'), f(rows[-1], 'z_m')] if rows else None}


def main():
    a = sys.argv[1:]
    out = None
    if '--out' in a: i = a.index('--out'); out = a[i + 1]; del a[i:i + 2]
    E, csvs = a[0], a[1:]
    B, L = load_boxes(E), lod_tiles(E)
    hvp = os.path.join(E, 'coll_audit_hv.npy')
    hv = np.load(hvp).astype(np.float32) if os.path.exists(hvp) else None
    reg = json.load(open(os.path.join(E, 'manifest.json')))['region']
    D = Drawn(E) if os.path.exists(os.path.join(E, 'drawn_raster.npz')) else None   # (island r02)
    res = [check(E, c, B, L, hv, reg, D) for c in csvs]
    summ = {'routes': len(res), 'seconds': round(sum(r['seconds'] for r in res), 1), 'fall_through': sum(r['fall_through'] for r in res),
            'stuck': sum(r['stuck'] for r in res), 'mid_air_frames': sum(r['mid_air_frames'] for r in res), 'wall_air_frames': sum(r['wall_air_frames'] for r in res),
            'anchors': sum(r['anchors'] for r in res), 'web_air': sum(r['web_air'] for r in res),
            'facadeLod_min_dist_m': min((r['facadeLod_min_dist_m'] for r in res if r['facadeLod_min_dist_m'] is not None), default=None),
            'boxes': len(B), 'facadeLod_tiles': len(L), 'drawn': None if D is None else D.counts}
    rep = {'summary': summ, 'routes': res}
    if out: json.dump(rep, open(out, 'w'), indent=1)
    for r in res:
        print('%-34s %5.1f s %6.0f m  fall %d  stuck %d  mid-air %d  wall-air %d  web-air %d/%d  lod-dist %s  modes %s' % (r['csv'], r['seconds'], r['path_m'], r['fall_through'], r['stuck'],
              r['mid_air_frames'], r['wall_air_frames'], r['web_air'], r['anchors'], r['facadeLod_min_dist_m'], r['modes']))
        if r.get('drawn'):
            d = r['drawn']; sw = d['swing']
            print('    drawn: wall-air %d' % d['wall_air_drawn_frames'], end='')
            print('  mid-air %d  feet-overlap %d %s (point inside %d)  web-air %d  | swing: re-web gaps %d, max %s s, >0.5 s %d, ground+land %.1f %%, anchors %d  | landings %s' % (
                d['mid_air_drawn_frames'], d['feet_overlap_frames'], d['feet_overlap_by_kind'], d['feet_point_inside_frames'], d['web_air_drawn'],
                sw['releases_rewebbed'], sw['max_reweb_gap_s'], sw['reweb_gaps_over_0_5s'], 100 * sw['ground_land_frac'], sw['distinct_swing_anchors'],
                [(e[0], e[4], e[5]) for e in d['land_events']]))
    print('TOTAL', json.dumps(summ))


if __name__ == '__main__':
    main()
