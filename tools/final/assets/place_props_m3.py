#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""PA phase 2: deterministic placements of the supplied props / animals on the island (CPU only, reads exported data, writes JSON + audit).

Ground model: a 0.5 m raster of the island built from the SAME exports the Unreal maps are built from
  (~/sm2-n1/_scratch/island/export/island: sidewalks / asphalt / highway / park water meshes, layout.json footprints + pools + zip points;
   ~/sm2-n1/_scratch/terrain/export: Central Park ground / paths / drives / water / furniture, coast lawns, plaza paving, piers + sheds, rocks)
  classes: LAWN, PATH, PLAZA, PIER (allowed ground) | SIDEWALK, ROAD, WATER, BUILD, OBST (never), with the surface height per cell.
Rules (owner/orchestrator brief 2026-10-08, PLAN.md section 6):
  * nothing within 2 m of a crosswalk or of the crowd walking band (AWHLifeCrowd bands around every walk.txt sidewalk edge: avenue -2.25..+0.25 m,
    street -1.65..+0.2 m, +roadward; crosswalk = the walk.txt crosswalk segment with a 2.5 m half width), nothing on roads, sidewalks or water
  * allowed ground: park lawns / paths, coast lawns, plazas / promenades (paved city surface outside every walk band), pier decks
  * paved city surface only >= 6 m from any road (plazas / promenade interiors, never a street sidewalk, with or without crowd walkers)
  * drums / crates stand against a wall (1.0-1.8 m from a footprint / pier shed) or a waterfront railing, never free on a path
  * >= 2 m from building footprints / pier sheds (doorways), >= 4 m from signal masts / posts, clear of every existing pool item and park furniture
  * animals: never on roofs / perches: every instance must be >= 3 m (3D) from every traversal zip point (roof edges, corners, ledges, lamp tops ...)
  * pigeons in flocks of 5-15; flat ground only (height spread < 4 cm under the footprint)
Output: <out>/placements.json {kind: [[x, y, z, ry, s, c0, c1, c2, c3], ...]} (browser metres, ry = yaw of the model's +Z about +y), audit.json, audit_*.png
usage: place_props_m3.py [--out DIR]
"""
import argparse, json, math, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ISL = os.path.expanduser('~/sm2-n1/_scratch/island/export/island')
TER = os.path.expanduser('~/sm2-n1/_scratch/terrain/export')
LIFE = os.path.join(WT, 'unreal/WebHomage/Scripts/life_data_island')
OUT = os.path.expanduser('~/sm2-n1/_scratch/final/assets/prep')
RES = 0.5
X0, Z0, X1, Z1 = -960.0, -3520.0, 960.0, 3380.0
W, H = int((X1 - X0) / RES), int((Z1 - Z0) / RES)
NONE, LAWN, PATH, PLAZA, PIER, SIDEWALK, ROAD, WATER, BUILD, OBST = range(10)
CNAME = ['none', 'lawn', 'path', 'plaza', 'pier', 'sidewalk', 'road', 'water', 'build', 'obst']
ALLOWED = (LAWN, PATH, PLAZA, PIER, SIDEWALK)   # SIDEWALK = the city's paved surfaces (plazas, promenades); every street sidewalk is inside NOGO
SIZE = {'oildrum': 0.32, 'crate': 0.42, 'pigeon': 0.2, 'gull': 0.32, 'cat': 0.32, 'squirrel': 0.25, 'rat': 0.25}   # footprint radius (m)
ANIMALS = ('pigeon', 'gull', 'cat', 'squirrel', 'rat')


# ------------------------------------------------------------------------------------------------ io helpers
def read_glb(path):
    data = open(path, 'rb').read()
    off, js, binc = 12, None, b''
    while off < len(data):
        ln, ty = struct.unpack_from('<II', data, off); ch = data[off + 8: off + 8 + ln]
        if ty == 0x4E4F534A: js = json.loads(ch)
        elif ty == 0x004E4942: binc = ch
        off += 8 + ln
    CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    def acc(i):
        a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
        n, c, dt = a['count'], NC[a['type']], np.dtype(CT[a['componentType']])
        st = bv.get('byteStride', 0); o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        if st and st != dt.itemsize * c:
            raw = np.frombuffer(binc, np.uint8, st * (n - 1) + dt.itemsize * c, o)
            return np.lib.stride_tricks.as_strided(raw, (n, dt.itemsize * c), (st, 1)).copy().view(dt).reshape(n, c)
        return np.frombuffer(binc, dt, n * c, o).reshape(n, c)
    tris = []
    for ni, node in enumerate(js.get('nodes', [])):
        if 'mesh' not in node: continue
        M = np.eye(4)
        if 'matrix' in node: M = np.array(node['matrix']).reshape(4, 4).T
        elif 'translation' in node: M[:3, 3] = node['translation']
        for p in js['meshes'][node['mesh']]['primitives']:
            P = acc(p['attributes']['POSITION']).astype(np.float64)
            P = P @ M[:3, :3].T + M[:3, 3]
            I = acc(p['indices']).ravel().astype(np.int64) if 'indices' in p else np.arange(len(P))
            tris.append(P[I.reshape(-1, 3)])
    return np.concatenate(tris) if tris else np.zeros((0, 3, 3))


def hrand(*a):
    h = 2166136261
    for v in a:
        h ^= int(abs(v) * 1000003.0 + (7 if v < 0 else 0)) & 0xFFFFFFFF; h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xFFFFFFFF; h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)


def ij(x, z):
    return ((np.asarray(z) - Z0) / RES).astype(np.int64), ((np.asarray(x) - X0) / RES).astype(np.int64)


# ------------------------------------------------------------------------------------------------ raster
class Ground:
    def __init__(self):
        self.cls = np.zeros((H, W), np.uint8)
        self.hgt = np.full((H, W), -9.0, np.float32)

    def tris(self, T, c, height=True, bbox=False):
        """rasterise triangles (browser metres) as class c; ground classes also write the surface height (max over meshes)"""
        n = 0
        for t in T:
            xs, zs = t[:, 0], t[:, 2]
            i0, i1 = int((zs.min() - Z0) / RES), int(math.ceil((zs.max() - Z0) / RES))
            j0, j1 = int((xs.min() - X0) / RES), int(math.ceil((xs.max() - X0) / RES))
            i0, j0, i1, j1 = max(i0, 0), max(j0, 0), min(i1, H - 1), min(j1, W - 1)
            if i1 < i0 or j1 < j0: continue
            if bbox:
                self.cls[i0:i1 + 1, j0:j1 + 1] = c; n += 1; continue
            jj, ii = np.meshgrid(np.arange(j0, j1 + 1), np.arange(i0, i1 + 1))
            x = X0 + (jj + 0.5) * RES; z = Z0 + (ii + 0.5) * RES
            a, b, cc = t
            d = (b[2] - cc[2]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[2] - cc[2])
            if abs(d) < 1e-12: continue
            l1 = ((b[2] - cc[2]) * (x - cc[0]) + (cc[0] - b[0]) * (z - cc[2])) / d
            l2 = ((cc[2] - a[2]) * (x - cc[0]) + (a[0] - cc[0]) * (z - cc[2])) / d
            l3 = 1 - l1 - l2
            ins = (l1 >= -0.05) & (l2 >= -0.05) & (l3 >= -0.05)
            if not ins.any():   # a triangle smaller than a cell: its centroid cell
                ci, cj = ij(t[:, 0].mean(), t[:, 2].mean()); ins = (ii == ci) & (jj == cj)
                if not ins.any(): continue
            sub = self.cls[i0:i1 + 1, j0:j1 + 1]; sub[ins] = c
            if height:
                y = l1 * a[1] + l2 * b[1] + l3 * cc[1]
                hs = self.hgt[i0:i1 + 1, j0:j1 + 1]; hs[ins] = np.maximum(hs[ins], y[ins])
            n += 1
        return n

    def rect(self, x0, z0, x1, z1, c, y=None):
        i0, j0 = ij(x0, z0); i1, j1 = ij(x1, z1)
        i0, i1 = sorted((int(np.clip(i0, 0, H - 1)), int(np.clip(i1, 0, H - 1)))); j0, j1 = sorted((int(np.clip(j0, 0, W - 1)), int(np.clip(j1, 0, W - 1))))
        self.cls[i0:i1 + 1, j0:j1 + 1] = c
        if y is not None: self.hgt[i0:i1 + 1, j0:j1 + 1] = y

    def disc(self, mask, x, z, r):
        i, j = ij(x, z); k = int(math.ceil(r / RES))
        i0, i1, j0, j1 = max(i - k, 0), min(i + k, H - 1), max(j - k, 0), min(j + k, W - 1)
        if i1 < i0 or j1 < j0: return
        jj, ii = np.meshgrid(np.arange(j0, j1 + 1), np.arange(i0, i1 + 1))
        m = np.hypot(X0 + (jj + 0.5) * RES - x, Z0 + (ii + 0.5) * RES - z) <= r
        mask[i0:i1 + 1, j0:j1 + 1] |= m

    def poly(self, mask, pts):
        im = Image.new('1', (W, H), 0)
        ImageDraw.Draw(im).polygon([((x - X0) / RES, (z - Z0) / RES) for x, z in pts], fill=1)
        mask |= np.asarray(im, bool)


def point_in_poly(x, z, poly):
    """vectorised even-odd test"""
    x = np.asarray(x); z = np.asarray(z); inside = np.zeros(x.shape, bool)
    px, pz = poly[:, 0], poly[:, 1]
    for k in range(len(poly)):
        xa, za, xb, zb = px[k - 1], pz[k - 1], px[k], pz[k]
        c = ((za > z) != (zb > z)) & (x < (xb - xa) * (z - za) / (zb - za + 1e-12) + xa)
        inside ^= c
    return inside


def isl_tris(m):
    """island export meshes are stored relative to their tile centre (manifest 'center'); terrain export meshes are absolute"""
    return read_glb(os.path.join(ISL, m['file'])) + np.array(m.get('center') or [0, 0, 0], np.float64)


def build_ground(log):
    G = Ground()
    lay = json.load(open(os.path.join(ISL, 'layout.json')))
    ter = json.load(open(os.path.join(TER, 'terrain.json')))
    man = json.load(open(os.path.join(ISL, 'manifest.json')))
    tman = json.load(open(os.path.join(TER, 'manifest.json')))
    # land outline first: everything inside the island polygon starts as LAWN-less 'none' land; the meshes define the surface
    land = np.zeros((H, W), bool); G.poly(land, ter['landPoly'])
    # ground meshes, low priority first
    for m in tman['meshes']:
        src = m['src']; f = os.path.join(TER, m['file'])
        if m['kind'] == 'ground':
            c = PATH if src in ('parkPaths', 'park-hexpavers') else ROAD if src == 'park-drives' else PLAZA if src == 'plazaPaving' else LAWN
            if c == LAWN: G.tris(read_glb(f), c)
    for m in man['meshes']:
        if m['kind'] == 'land': G.tris(isl_tris(m), LAWN)
    for m in tman['meshes']:
        src = m['src']; f = os.path.join(TER, m['file'])
        if m['kind'] == 'ground' and src in ('parkPaths', 'park-hexpavers', 'plazaPaving'):
            G.tris(read_glb(f), PATH if src != 'plazaPaving' else PLAZA)
    n = 0
    for m in man['meshes']:
        if m['kind'] == 'sidewalk': n += G.tris(isl_tris(m), SIDEWALK)
    log('sidewalk tris', n)
    n = 0
    for m in man['meshes']:
        if m['kind'] == 'asphalt' or m['src'] == 'highwayRoad': n += G.tris(isl_tris(m), ROAD)
    for m in tman['meshes']:
        if m['src'] == 'park-drives': n += G.tris(read_glb(os.path.join(TER, m['file'])), ROAD)
    log('road tris', n)
    # streets rects as road too (intersections / any asphalt the meshes miss)
    for s in lay['streets']:
        if 'x0' in s: G.rect(s['x0'], s['z0'], s['x1'], s['z1'], ROAD, 0.0)
    for p in ter['piers']:
        G.rect(p['x0'], p['z0'], p['x1'], p['z1'], PIER, -9.0)   # deck height comes from the drawn coast meshes below (planks 0.15-0.3 m)
    # waterfront (island export 'coast-*' meshes: promenade, pier decks, seawall, rails, bollards, pickets): up-facing surfaces near street level
    # give the ground height; anything standing above the deck (rails, bollards, kiosks, lamp posts) is an obstacle (triangle bounding boxes)
    nu = no = 0
    G.rail = np.zeros((H, W), bool)   # waterfront rails / bollards / pickets: what drums and crates may stand against
    for m in man['meshes']:
        if not m['src'].startswith('coast-'): continue
        T = isl_tris(m)
        nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); up = nrm[:, 1] / (np.linalg.norm(nrm, axis=1) + 1e-12) > 0.9
        ymax, ymin = T[:, :, 1].max(1), T[:, :, 1].min(1)
        deck = up & (ymax < 0.45) & (ymin > -0.2)
        for t in T[deck]:
            i0, j0 = ij(t[:, 0].min(), t[:, 2].min()); i1, j1 = ij(t[:, 0].max(), t[:, 2].max())
            i0, i1, j0, j1 = max(int(i0), 0), min(int(i1), H - 1), max(int(j0), 0), min(int(j1), W - 1)
            if i1 < i0 or j1 < j0: continue
            hs = G.hgt[i0:i1 + 1, j0:j1 + 1]; np.maximum(hs, float(t[:, 1].mean()), out=hs); nu += 1
        stand = ~deck & (ymax > 0.3) & (ymin < 3.0)
        before = G.cls == OBST
        no += G.tris(T[stand], OBST, height=False, bbox=True)
        G.rail |= (G.cls == OBST) & ~before
    log('coast deck tris', nu, 'coast obstacle tris', no)
    # water: outside the land polygon and not pier; park water meshes and the ponds
    wet = ~land & (G.cls != PIER)
    for m in tman['meshes']:
        if m['kind'] == 'water':
            T = read_glb(os.path.join(TER, m['file'])); G.tris(T, WATER, height=False)
    for w in ter['water']:
        if w.get('pts'):
            mk = np.zeros((H, W), bool); G.poly(mk, w['pts']); G.cls[mk] = WATER
    for m in man['meshes']:
        if m['src'] == 'parkWater': G.tris(isl_tris(m), WATER, height=False)
    G.cls[wet & (G.cls != ROAD)] = WATER
    # buildings: footprints, pier sheds, park sites (the museum)
    for f in lay['footprints']:
        G.rect(f['x0'], f['z0'], f['x1'], f['z1'], BUILD)
    for p in ter['piers']:
        s = p.get('shed')
        if s: G.rect(s['x0'], s['z0'], s['x1'], s['z1'], BUILD)
    for r in ter['sites'].values():
        G.rect(r['x0'], r['z0'], r['x1'], r['z1'], BUILD)
    # obstacles: park furniture / set pieces / reservoir coping / pickets (triangle bounding boxes), rocks
    n = 0
    for m in tman['meshes']:
        if m['kind'] in ('furniture', 'setpieces', 'edge', 'shore'):
            n += G.tris(read_glb(os.path.join(TER, m['file'])), OBST, height=False, bbox=True)
    log('obstacle tris', n)
    rk = np.zeros((H, W), bool)
    for x, z, r in ter['rocks']: G.disc(rk, x, z, r)
    G.cls[rk] = OBST
    # Central Park grass (parkmask.rgba: R density, G tuft height / 1 m, 1 m texels): animals only where the lawn is mowed (tufts <= 12 cm),
    # taller meadow / woodland tufts would bury a 0.25 m animal
    mk = ter['mask']; M = np.fromfile(os.path.join(TER, mk['file']), np.uint8).reshape(mk['h'], mk['w'], 4)
    tall = (M[..., 0] > 0) & (M[..., 1] > 30)
    ii, jj = np.nonzero(tall)
    xs, zs = mk['x0'] + (jj + 0.5) * mk['texel'], mk['z0'] + (ii + 0.5) * mk['texel']
    for dx in (-0.25, 0.25):
        for dz in (-0.25, 0.25):
            ci, cj = ij(xs + dx, zs + dz); ok = (ci >= 0) & (ci < H) & (cj >= 0) & (cj < W)
            sel = G.cls[ci[ok], cj[ok]] == LAWN
            G.cls[ci[ok][sel], cj[ok][sel]] = OBST
    log('tall park grass texels', int(tall.sum()))
    # canopy (for the verification cameras only): street / park / coast tree crowns, ~4 m radius
    G.canopy = np.zeros((H, W), bool)
    for src in (lay['instances'], ter['instances']):
        for k, v in src.items():
            if k.startswith('trunks-') and not k.endswith(('-mid', '-far')):
                for it in v.get('items') or []: G.disc(G.canopy, it['x'], it['z'], 4.0 * it.get('s', 1.0))
    return G, lay, ter


# ------------------------------------------------------------------------------------------------ rule masks
def nogo_masks(G, lay, ter, log):
    """NOGO = cells where nothing may stand: walk bands + 2 m, crosswalks + 2 m, signal masts 4 m, existing pool items / trees"""
    nogo = np.zeros((H, W), bool)
    pts, edges = {}, []
    for l in open(os.path.join(LIFE, 'walk.txt')):
        p = l.split()
        if not p or p[0].startswith('#'): continue
        if p[0] == 'P': pts[int(p[1])] = (float(p[2]), float(p[3]))
        elif p[0] == 'E': edges.append((int(p[2]), int(p[3]), int(p[4]), int(p[5]), int(p[7])))
    nb = nc = 0
    for a, b, kind, axis, side in edges:
        A, B = np.array(pts[a]), np.array(pts[b]); d = B - A; L = np.linalg.norm(d)
        if L < 1e-3: continue
        u = d / L; ext = 2.0
        if kind == 0:   # sidewalk: walk band (avenue -2.25..0.25 / street -1.65..0.2, +roadward), each edge extended by the 2 m clearance
            lo, hi = (-2.25, 0.25) if axis == 0 else (-1.65, 0.2)
            rw = side * np.array([-u[1], u[0]])   # roadward unit (right of a->b when side = +1)
            lo -= 2.0; hi += 2.0
            q = [A - u * ext + rw * lo, B + u * ext + rw * lo, B + u * ext + rw * hi, A - u * ext + rw * hi]; nb += 1
        else:           # crosswalk: 2.5 m half width + 2 m
            nrm = np.array([-u[1], u[0]]); hw = 2.5 + 2.0
            q = [A - u * ext - nrm * hw, B + u * ext - nrm * hw, B + u * ext + nrm * hw, A - u * ext + nrm * hw]; nc += 1
        G.poly(nogo, [tuple(v) for v in q])
    log('walk band polygons', nb, 'crosswalk polygons', nc)
    for l in open(os.path.join(LIFE, 'signals.txt')):
        p = l.split()
        if p and p[0] in ('M', 'P'): G.disc(nogo, float(p[1]), float(p[2]), 4.0)
    # existing pool items (street furniture, kiosks, trees ...) and park lamps / benches: their own footprint + 0.6 m
    R = {'bench': 1.5, 'benchFar': 0, 'cart': 1.8, 'cart2': 1.6, 'kiosk': 3.0, 'busstop': 3.0, 'shelter': 3.0, 'news': 2.5, 'dumpster': 2.0, 'rolloff': 3.5,
         'subway': 3.0, 'subwaypit': 3.0, 'bikekiosk': 4.0, 'bike': 1.2, 'shed': 0, 'shedtop': 0, 'stack': 3.0, 'billboard': 0}
    skip = ('Far', 'far', '-mid', 'crown', 'lod1', 'antenna', 'dish', 'hvac', 'vents', 'roofplants', 'flags', 'propContactAO', 'blade', 'lampPool', 'parkLampPool', 'doorman', 'xfar', 'trees-')
    obst = []
    for k, v in lay['instances'].items():
        if any(s in k for s in skip): continue
        r = R.get(k, 1.1)
        if r <= 0: continue
        for it in v.get('items') or []:
            if it.get('y', 0) > 1.0: continue
            obst.append((it['x'], it['z'], r))
    for k, v in ter['instances'].items():
        if v.get('kind') != 'pool' or any(s in k for s in ('Far', 'far', '-mid', 'crown', 'lod1', 'Pool', 'trees-')): continue
        r = 1.2 if 'trunk' in k or 'bark' in k else R.get(k, 1.1)
        for it in v.get('items') or []: obst.append((it['x'], it['z'], r))
    # lamp light-pool decals (park: 3 m discs; street: 7.6 m quads offset 2.4 m along the lamp's facing): they read as white discs in daylight
    for it in (lay['instances'].get('parkLampPool') or {}).get('items') or []: obst.append((it['x'], it['z'], 3.3))
    for it in (lay['instances'].get('lampPool') or {}).get('items') or []:
        ry = it.get('ry', 0.0); obst.append((it['x'] + math.sin(ry) * 2.4, it['z'] + math.cos(ry) * 2.4, 4.6))
    for k, v in ter['instances'].items():   # matrix instances (picnic blankets, reeds): [x, y, z, ry, sx, sy, sz, ...]
        if v.get('kind') == 'matrix':
            for it in v.get('items') or []: obst.append((it[0], it[2], 1.2 + 0.8 * max(it[4], it[6])))
    for x, z, r in obst: G.disc(nogo, x, z, r)
    log('pool obstacles', len(obst))
    return nogo


# ------------------------------------------------------------------------------------------------ placement
class Placer:
    def __init__(self, G, nogo, lay, log):
        self.G, self.nogo, self.log = G, nogo, log
        cls = G.cls
        self.d_build = ndimage.distance_transform_edt(cls != BUILD).astype(np.float32) * RES
        self.d_bad = ndimage.distance_transform_edt(~np.isin(cls, (ROAD, WATER, OBST, NONE))).astype(np.float32) * RES
        self.d_water = ndimage.distance_transform_edt(cls != WATER).astype(np.float32) * RES
        self.d_nogo = ndimage.distance_transform_edt(~nogo).astype(np.float32) * RES
        self.d_road = ndimage.distance_transform_edt(~np.isin(cls, (ROAD, NONE))).astype(np.float32) * RES
        self.d_rail = ndimage.distance_transform_edt(~G.rail).astype(np.float32) * RES
        Z = np.array([p['p'] for p in lay['zipPoints']]); self.zip = cKDTree(Z)
        self.placed = {k: [] for k in SIZE}; self.trees = {}
        self.reject = {}

    def ok(self, kind, x, z, build_clear=2.0):
        """the per-instance rule check; returns ground y or None"""
        i, j = ij(x, z)
        if not (0 < i < H - 1 and 0 < j < W - 1): return self._rej('outside')
        r = SIZE[kind]
        c = self.G.cls[i, j]
        if c not in ALLOWED: return self._rej('class_' + CNAME[c])
        if self.d_nogo[i, j] < r: return self._rej('walkband_crosswalk_signal_pool')
        if self.d_bad[i, j] < r + 0.3: return self._rej('near_road_water_obst_sidewalk')
        if self.d_build[i, j] < build_clear: return self._rej('near_building')
        if c == SIDEWALK and self.d_road[i, j] < 6.0: return self._rej('street_sidewalk')   # paved city surface: plazas / promenade interiors only
        k = int(math.ceil(r / RES))
        win = self.G.hgt[i - k:i + k + 1, j - k:j + k + 1]; cw = self.G.cls[i - k:i + k + 1, j - k:j + k + 1]
        if not np.isin(cw, ALLOWED).all(): return self._rej('footprint_class')
        if win.max() - win.min() > 0.04 or win.min() < -1: return self._rej('not_flat')
        y = float(win.max())
        if y > 1.5: return self._rej('too_high')
        if kind in ANIMALS:
            d, _ = self.zip.query([x, y, z])
            if d < 3.0: return self._rej('zip_point_3m')
        return y

    def _rej(self, why):
        self.reject[why] = self.reject.get(why, 0) + 1
        return None

    def spaced(self, kind, x, z, dmin, kinds=None):
        for k in (kinds or [kind]):
            for p in self.placed[k][-4000:]:
                if (p[0] - x) ** 2 + (p[2] - z) ** 2 < dmin * dmin: return False
        return True

    def clear_of_all(self, x, z, r):
        for k, L in self.placed.items():
            rr = r + SIZE[k]
            for p in L:
                if abs(p[0] - x) < rr and abs(p[2] - z) < rr and (p[0] - x) ** 2 + (p[2] - z) ** 2 < rr * rr: return False
        return True

    def hugs(self, kind, x, z):
        """drums / crates stand against something (a shed wall, a railing, a fence, the pier edge), never free in the middle of a path"""
        i, j = ij(x, z); r = SIZE[kind]
        wall = 1.0 <= float(self.d_build[i, j]) <= 1.8          # against a shed / building wall (footprint rects are the wall's outer bound)
        rail = r + 0.1 <= float(self.d_rail[i, j]) <= r + 0.6   # against a waterfront railing / bollard line
        return (wall or rail) and self.G.cls[i, j] != PATH

    def put(self, kind, x, y, z, ry, s=1.0, cd=(0, 0, 0, 0)):
        self.placed[kind].append([round(x, 3), round(y, 3), round(z, 3), round(ry, 4), round(s, 3)] + [round(float(v), 4) for v in cd])


def cells(G, classes, step, seed):
    """jittered sample points (one per step x step metres) on the given ground classes"""
    m = np.isin(G.cls, classes)
    k = int(step / RES)
    sub = m[::k, ::k]
    ii, jj = np.nonzero(sub)
    out = []
    for a, b in zip(ii, jj):
        x = X0 + (b * k + 0.5) * RES; z = Z0 + (a * k + 0.5) * RES
        out.append((x + (hrand(x, z, seed) - 0.5) * step * 0.8, z + (hrand(z, x, seed + 1) - 0.5) * step * 0.8))
    out.sort(key=lambda p: hrand(p[0], p[1], seed + 2))
    return out


def place_all(G, nogo, lay, ter, log):
    P = Placer(G, nogo, lay, log)
    animal_cd = lambda x, z, s: (hrand(x, z, s), 0.4 + 0.6 * hrand(z, x, s + 1), 0.8 + 0.4 * hrand(x + 1, z, s + 2), 0.92 + 0.12 * hrand(x, z + 1, s + 3))
    prop_cd = lambda x, z, s: (0.0, 0.0, 0.0, 0.9 + 0.15 * hrand(x, z, s))
    benches = [(it['x'], it['z']) for it in lay['instances']['bench']['items']]
    # ---- pigeons: flocks of 5-15 near benches on lawns / paths / plazas, plus open plaza and park-path spots; flocks >= 30 m apart
    anchors = []
    for bx, bz in benches:
        a = hrand(bx, bz, 11) * 6.283; anchors.append((bx + math.cos(a) * 3.2, bz + math.sin(a) * 3.2))
    anchors.sort(key=lambda p: hrand(p[0], p[1], 12))
    anchors = anchors + cells(G, (PLAZA,), 12.0, 13) + cells(G, (PATH,), 25.0, 14)
    flocks = []
    for cx, cz in anchors:
        if len(P.placed['pigeon']) >= 900: break
        if any((fx - cx) ** 2 + (fz - cz) ** 2 < 30 ** 2 for fx, fz in flocks): continue
        if P.ok('pigeon', cx, cz) is None: continue
        want = 5 + int(hrand(cx, cz, 15) * 11)   # 5..15
        mem = []
        for t in range(60):
            if len(mem) >= want: break
            a = hrand(cx, cz, 100 + t) * 6.283; rr = 2.2 * math.sqrt(hrand(cz, cx, 200 + t))
            x, z = cx + math.cos(a) * rr, cz + math.sin(a) * rr
            if any((m[0] - x) ** 2 + (m[2] - z) ** 2 < 0.36 ** 2 for m in mem): continue
            y = P.ok('pigeon', x, z)
            if y is None: continue
            mem.append((x, y, z))
        if len(mem) < 5: continue
        flocks.append((cx, cz))
        head = hrand(cx, cz, 16) * 6.283   # a loose common heading (they drift into the wind), +-70 deg each
        for x, y, z in mem:
            P.put('pigeon', x, y, z, head + (hrand(x, z, 17) - 0.5) * 2.4, 0.92 + 0.16 * hrand(z, x, 18), animal_cd(x, z, 19))
    log('pigeon flocks', len(flocks), 'birds', len(P.placed['pigeon']))
    # ---- gulls: waterfront (piers, coast lawns / plazas within 25 m of water), 1-3 per spot, spots >= 20 m apart
    gspots = [p for p in cells(G, (PIER, LAWN, PLAZA, PATH), 8.0, 21) if P.d_water[ij(*p)] < 25.0]
    gs = []
    for cx, cz in gspots:
        if len(P.placed['gull']) >= 80: break
        if any((fx - cx) ** 2 + (fz - cz) ** 2 < 20 ** 2 for fx, fz in gs): continue
        n = 1 + int(hrand(cx, cz, 22) * 3); got = 0
        for t in range(12):
            if got >= n: break
            x, z = cx + (hrand(cx, cz, 30 + t) - 0.5) * 3.0, cz + (hrand(cz, cx, 40 + t) - 0.5) * 3.0
            if not P.clear_of_all(x, z, SIZE['gull'] + 0.2): continue
            y = P.ok('gull', x, z)
            if y is None: continue
            P.put('gull', x, y, z, hrand(x, z, 23) * 6.283, 0.9 + 0.2 * hrand(z, x, 24), animal_cd(x, z, 25)); got += 1
        if got: gs.append((cx, cz))
    log('gull spots', len(gs), 'gulls', len(P.placed['gull']))
    # ---- squirrels: mowed lawn / path within 1.3-5.8 m of a park / coast tree trunk, >= 8 m apart
    trunks = []
    for src in (lay['instances'], ter['instances']):
        for k, v in src.items():
            if k in ('trunks-park', 'trunks-elm', 'trunks-conifer', 'trunks-small') or k.startswith('ez-park') and k.endswith('l0-bark'):
                trunks += [(it['x'], it['z']) for it in v.get('items') or []]
    trunks = sorted(set((round(x, 2), round(z, 2)) for x, z in trunks), key=lambda p: hrand(p[0], p[1], 31))
    for tx, tz in trunks:
        if len(P.placed['squirrel']) >= 120: break
        a = hrand(tx, tz, 32) * 6.283; rr = 1.3 + 4.5 * hrand(tz, tx, 33)
        x, z = tx + math.cos(a) * rr, tz + math.sin(a) * rr
        if G.cls[ij(x, z)] not in (LAWN, PATH) or not P.spaced('squirrel', x, z, 8.0) or not P.clear_of_all(x, z, 0.5): continue
        y = P.ok('squirrel', x, z)
        if y is None: continue
        P.put('squirrel', x, y, z, hrand(x, z, 34) * 6.283, 0.9 + 0.2 * hrand(z, x, 35), animal_cd(x, z, 36))
    log('squirrels', len(P.placed['squirrel']), 'of', len(trunks), 'trunks')
    # ---- oil drums: groups of 2-3 against a wall / railing on piers, promenades and plazas (first drum hugs the edge), group spots >= 25 m apart
    dspots = cells(G, (PIER, SIDEWALK, PLAZA), 2.0, 41); ds = []
    for cx, cz in dspots:
        if len(P.placed['oildrum']) >= 150: break
        if any((fx - cx) ** 2 + (fz - cz) ** 2 < 25 ** 2 for fx, fz in ds): continue
        n = 2 + int(hrand(cx, cz, 42) * 2); got = []
        for t in range(16):
            if len(got) >= n: break
            a = hrand(cx, cz, 50 + t) * 6.283; rr = 0.62 * (len(got) > 0) * (1 + 0.15 * hrand(cz, cx, 60 + t))
            x, z = (got[0][0] + math.cos(a) * rr, got[0][2] + math.sin(a) * rr) if got else (cx, cz)
            if any((g[0] - x) ** 2 + (g[2] - z) ** 2 < 0.6 ** 2 for g in got) or not P.clear_of_all(x, z, SIZE['oildrum']): continue
            y = P.ok('oildrum', x, z, build_clear=1.0)
            if y is None or (not got and not P.hugs('oildrum', x, z)): continue
            P.put('oildrum', x, y, z, hrand(x, z, 43) * 6.283, 1.0, prop_cd(x, z, 44)); got.append((x, y, z))
        if got: ds.append((cx, cz))
    log('drum groups', len(ds), 'drums', len(P.placed['oildrum']))
    # ---- crates: stacks of 1-3 against a wall / railing (piers, promenades, plazas, beside food carts), >= 15 m apart
    carts = [(it['x'], it['z']) for k in ('cart', 'cart2') for it in lay['instances'][k]['items']]
    cspots = cells(G, (PIER, SIDEWALK, PLAZA), 2.0, 51) + [(x + 2.6 * math.cos(hrand(x, z, 52) * 6.283), z + 2.6 * math.sin(hrand(x, z, 52) * 6.283)) for x, z in carts]
    cs = []
    for cx, cz in cspots:
        if len(P.placed['crate']) >= 250: break
        if any((fx - cx) ** 2 + (fz - cz) ** 2 < 15 ** 2 for fx, fz in cs): continue
        if not P.clear_of_all(cx, cz, 0.9): continue
        y = P.ok('crate', cx, cz, build_clear=1.0)
        if y is None or not P.hugs('crate', cx, cz): continue
        ry = hrand(cx, cz, 53) * 6.283; n = 1 + int(hrand(cz, cx, 54) * 3); c0 = prop_cd(cx, cz, 55)
        P.put('crate', cx, y, cz, ry, 1.0, c0)
        if n >= 2:   # second crate beside (shares the stack's footprint check)
            x2, z2 = cx + math.cos(ry) * 0.62, cz - math.sin(ry) * 0.62
            y2 = P.ok('crate', x2, z2, build_clear=1.0)
            if y2 is not None and abs(y2 - y) < 0.02:
                P.put('crate', x2, y2, z2, ry + (hrand(x2, z2, 56) - 0.5) * 0.3, 1.0, prop_cd(x2, z2, 57))
                if n >= 3:   # third on top of the first two, turned a little
                    P.put('crate', (cx + x2) / 2, y + 0.64, (cz + z2) / 2, ry + (hrand(cz, cx, 58) - 0.5) * 0.5, 1.0, prop_cd(cz, cx, 59))
        cs.append((cx, cz))
    log('crate stacks', len(cs), 'crates', len(P.placed['crate']))
    # ---- cats: single, on plazas / promenades / piers / lawns 2.5-8 m from a building or pier shed (2.5 m keeps doorways clear), >= 45 m apart
    catc = [p for p in cells(G, (PIER, PLAZA, LAWN, SIDEWALK, PATH), 2.0, 61) if 2.5 <= P.d_build[ij(*p)] <= 8.0]
    for x, z in catc:
        if len(P.placed['cat']) >= 60: break
        if not P.spaced('cat', x, z, 45.0) or not P.clear_of_all(x, z, 0.6): continue
        y = P.ok('cat', x, z, build_clear=2.5)
        if y is None: continue
        P.put('cat', x, y, z, hrand(x, z, 62) * 6.283, 0.9 + 0.15 * hrand(z, x, 63), animal_cd(x, z, 64))
    log('cats', len(P.placed['cat']))
    # ---- rats: sparse (>= 150 m apart): pier edges and park / coast spots within 4 m of water
    ratc = [p for p in cells(G, (PIER, LAWN, PATH), 4.0, 71) if P.d_water[ij(*p)] < 4.0]
    for x, z in ratc:
        if len(P.placed['rat']) >= 40: break
        if not P.spaced('rat', x, z, 150.0) or not P.clear_of_all(x, z, 0.6): continue
        y = P.ok('rat', x, z, build_clear=1.0)
        if y is None: continue
        P.put('rat', x, y, z, hrand(x, z, 72) * 6.283, 0.9 + 0.2 * hrand(z, x, 73), animal_cd(x, z, 74))
    log('rats', len(P.placed['rat']))
    return P


# ------------------------------------------------------------------------------------------------ audit
def audit(P, G, lay, out, log):
    rep = {'counts': {k: len(v) for k, v in P.placed.items()}, 'rejections': P.reject, 'checks': {}}
    allp = [(k, p) for k, L in P.placed.items() for p in L]
    zipd = [P.zip.query([p[0], p[1], p[2]])[0] for k, p in allp if k in ANIMALS]
    rep['checks']['min_zip_point_distance_m_animals'] = round(float(min(zipd)), 2) if zipd else None
    rep['checks']['max_y_m'] = round(max(p[1] for _, p in allp), 3)
    rep['checks']['min_walkband_crosswalk_signal_pool_clearance_m'] = round(float(min(P.d_nogo[ij(p[0], p[2])] - SIZE[k] for k, p in allp)), 2)
    rep['checks']['min_building_distance_m'] = round(float(min(P.d_build[ij(p[0], p[2])] for k, p in allp)), 2)
    rep['checks']['on_class'] = {CNAME[c]: int(sum(1 for k, p in allp if G.cls[ij(p[0], p[2])] == c)) for c in range(10)}
    fl = {}
    # pigeon flock sizes from the placement order (members within 5 m of the flock's first bird)
    sizes = []; cur = []
    for p in P.placed['pigeon']:
        if cur and (p[0] - cur[0][0]) ** 2 + (p[2] - cur[0][2]) ** 2 > 25: sizes.append(len(cur)); cur = []
        cur.append(p)
    if cur: sizes.append(len(cur))
    rep['checks']['pigeon_flock_sizes'] = {'n': len(sizes), 'min': min(sizes) if sizes else 0, 'max': max(sizes) if sizes else 0}
    json.dump(rep, open(os.path.join(out, 'audit.json'), 'w'), indent=1)
    log(json.dumps(rep))
    # top-view audit image of the island (1 px = 2 m) + crops
    pal = np.array([[20, 30, 60], [70, 120, 60], [150, 140, 110], [170, 160, 150], [120, 90, 60], [110, 110, 110], [45, 45, 45], [30, 60, 120], [90, 70, 80], [160, 40, 40]], np.uint8)
    img = pal[G.cls[::4, ::4]].copy(); img[P.nogo[::4, ::4]] = (img[P.nogo[::4, ::4]] * 0.5 + np.array([200, 160, 0]) * 0.5).astype(np.uint8)
    col = {'pigeon': (80, 160, 255), 'gull': (255, 255, 255), 'squirrel': (255, 140, 0), 'cat': (255, 0, 255), 'rat': (255, 0, 0), 'oildrum': (0, 80, 255), 'crate': (255, 220, 0)}
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    for k, p in allp:
        u, v = (p[0] - X0) / (RES * 4), (p[2] - Z0) / (RES * 4)
        d.ellipse([u - 1.5, v - 1.5, u + 1.5, v + 1.5], fill=col[k])
    im.save(os.path.join(out, 'audit_island.png'))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=OUT)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    log = lambda *m: print('[place]', *m, flush=True)
    G, lay, ter = build_ground(log)
    nogo = nogo_masks(G, lay, ter, log)
    G.nogo = nogo
    P = place_all(G, nogo, lay, ter, log)
    P.nogo = nogo
    json.dump({'frame': 'browser metres: x east, y up, z south; UE cm = (x, z, y) * 100; ry = yaw of the model +Z about +y (UE yaw = -ry)',
               'custom_data': 'c0 phase 0..1, c1 activity 0..1, c2 rate 0.8..1.2, c3 albedo brightness', 'items': P.placed},
              open(os.path.join(a.out, 'placements.json'), 'w'))
    audit(P, G, lay, a.out, log)
    np.savez_compressed(os.path.join(a.out, 'ground.npz'), cls=G.cls[::2, ::2], nogo=nogo[::2, ::2], canopy=G.canopy[::2, ::2])


if __name__ == '__main__':
    main()
