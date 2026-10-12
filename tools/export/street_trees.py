#!/usr/bin/env python3
"""Street trees along both sidewalks of every avenue (round 08; critic r07 gap: 'plant >= 2 street trees per 20 m on both sidewalks', CITY-SPEC C7).

Round 05-07 left 45-100 % of the browser's street trees out of the S1 / S2 corridor (build_city.py thin()) and added iron-fenced tree pits (street_props.py) that
stayed empty: S1 showed empty pits and no tree on the west sidewalk. Round 08 removes that thinning and fills the frontage instead:
  1. trees the browser already placed (layout.json ez-street*-l0-* pools) stay where they are;
  2. every empty tree pit of street_props.py (streetprops.json 'pit') gets a tree;
  3. gaps longer than GAP (9 m) between trees on an avenue sidewalk are filled with new trees (each with its own iron-fenced pit), so every 20 m of avenue frontage carries >= 2 trees
     (block ends keep 7 m clear for crosswalks and corner furniture; lamps, hydrants, signal masts, bus stops and other furniture keep 1.1-1.8 m clear, the tree slides along the curb).
Trees: the browser's three street species (ez_street0..2); high-detail LOD0 within 80 m of a street-level shot camera (S1, S5, S6), LOD1 (half the triangles) elsewhere.
Output: <export>/streettrees.json {pool: [items], '_remove': [[x, z] existing trees to drop]} (pools ez-street{0,1,2}-l{0,1}-{leaves,bark} and 'pit'), same item format as layout.json; build_city.py appends them to the ISMs.
usage: street_trees.py [export_dir]
"""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from citypaths import EXPORT as _EXPORT, REPO
EXP = (sys.argv[1] if len(sys.argv) > 1 else _EXPORT).rstrip('/') + '/'
lay = json.load(open(EXP + 'layout.json')); R = lay['region']
sp = json.load(open(EXP + 'streetprops.json')) if os.path.exists(EXP + 'streetprops.json') else {}
shots = json.load(open(os.path.join(REPO, 'unreal', 'WebHomage', 'Scripts', 'city_shots.json')))
HERO = [(s['pos'][0], s['pos'][2]) for s in shots if s['pos'][1] < 10.0]
AVS = [-250, 0, 250, 430]
LAT = 12.3          # browser tree pits stand 12.3 m from the avenue axis (1.3 m behind the curb)
GAP = 9.0; KEEP = 7.0; MINTREE = 3.0
I = lay['instances']

def hrand(*a):
    h = 2166136261
    for v in a:
        h ^= int(abs(v) * 1000003.0) & 0xFFFFFFFF; h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xFFFFFFFF; h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)

# ---- existing trees (species 0..2, LOD0 pools hold every street tree of the exported region), obstacles on the sidewalks
trees = {}
for sidx in range(3):
    for it in I.get(f'ez-street{sidx}-l0-leaves', {}).get('items', []):
        if R['x0'] - 20 < it['x'] < R['x1'] + 20 and R['z0'] - 20 < it['z'] < R['z1'] + 20: trees[(round(it['x'], 2), round(it['z'], 2))] = sidx
tree_pts = np.array(list(trees.keys())) if trees else np.zeros((0, 2))
obst = []
for k in ('hydrant', 'trash', 'newsbox', 'bench', 'planter', 'mailbox', 'bikerack', 'signpole', 'lamp', 'mast', 'post', 'shed', 'meter', 'payphone', 'kiosk', 'busstop', 'dock', 'bikekiosk', 'subway'):
    for i in I.get(k, {}).get('items') or []: obst.append((i['x'], i['z'], 2.2 if k in ('shed', 'busstop', 'subway') else (1.6 if k in ('lamp', 'mast', 'post') else 1.1)))
obst = np.array(obst)

def cam_near(x, z, r=16.0):
    return any(math.hypot(x - hx, z - hz) < r for hx, hz in HERO)
def tree_near(x, z, r):
    return len(tree_pts) > 0 and bool((np.hypot(tree_pts[:, 0] - x, tree_pts[:, 1] - z) < r).any())
def blocked(x, z):
    return bool((np.hypot(obst[:, 0] - x, obst[:, 1] - z) < np.maximum(obst[:, 2], 1.3)).any())

def lod_pool(x, z):
    d = min(math.hypot(x - hx, z - hz) for hx, hz in HERO)
    return 'l0' if d < 80.0 else 'l1'

new_trees = []     # (x, z, species, source)
new_pits = []
# 2. empty pits of street_props.py get a tree
for it in sp.get('pit', []):
    if not (R['x0'] < it['x'] < R['x1'] and R['z0'] < it['z'] < R['z1']): continue
    if tree_near(it['x'], it['z'], MINTREE) or cam_near(it['x'], it['z']): continue
    new_trees.append((it['x'], it['z'], None, 'pit')); tree_pts = np.vstack([tree_pts, [it['x'], it['z']]])

# 3. fill the gaps on avenue frontage
blocks = []
for s in lay['streets']:
    if s.get('kind') != 'avenue' or 'x0' not in s: continue
    ax = (s['x0'] + s['x1']) / 2
    if ax in AVS and s['z1'] - s['z0'] >= 30: blocks.append((ax, s['z0'], s['z1']))
blocks.sort()
audit = []
for ax, z0, z1 in blocks:
    if z1 < R['z0'] + 10 or z0 > R['z1'] - 10: continue
    lo, hi = max(z0 + KEEP, R['z0'] + 6), min(z1 - KEEP, R['z1'] - 6)
    if hi - lo < 8: continue
    for side in (-1, 1):
        x = ax + side * LAT
        # trees standing in this frontage strip (0..2.5 m of the pit line), sorted along z
        zs = sorted(float(z) for tx, z in (tree_pts if len(tree_pts) else []) if abs(tx - x) < 2.5 and lo - 3 < z < hi + 3)
        anchors = [lo] + [z for z in zs if lo < z < hi] + [hi]
        added = []
        for a, b in zip(anchors[:-1], anchors[1:]):
            n = int(math.ceil((b - a) / GAP)) - 1
            for k in range(1, n + 1):
                zt = a + (b - a) * k / (n + 1)
                for d in (0.0, 1.6, -1.6, 3.0, -3.0, 4.4, -4.4):
                    zz = zt + d
                    if zz < lo or zz > hi or blocked(x, zz) or tree_near(x, zz, 3.4) or cam_near(x, zz): continue
                    added.append(zz); break
        for zz in added:
            new_trees.append((x, zz, None, 'gap')); new_pits.append((x, zz))
            tree_pts = np.vstack([tree_pts, [x, zz]])
        # audit: trees per 20 m window of this frontage
        allz = np.array(sorted(zs + added))
        for w0 in np.arange(lo, hi - 19.9, 20.0):
            audit.append((ax, side, round(float(w0), 1), int(((allz >= w0) & (allz < w0 + 20.0)).sum())))

# existing browser trees within 16 m of a street-level shot camera are removed (a trunk 12 m from the lens fills the frame, S1 x 0-200); their pits go with them
remove = [[x, z] for (x, z) in trees.keys() if cam_near(x, z)]
out = {'_remove': remove}
def put(pool, it): out.setdefault(pool, []).append(it)
for x, z, sidx, src in new_trees:
    sidx = int(hrand(x, z, 3) * 3) % 3
    ry = hrand(x, z, 4) * 6.2832; s = 0.88 + hrand(x, z, 5) * 0.4
    s3 = [round(0.9 + hrand(x, z, 6) * 0.25, 4), round(0.9 + hrand(x, z, 7) * 0.25, 4), round(0.9 + hrand(x, z, 8) * 0.25, 4)]
    lod = lod_pool(x, z)
    item = {'x': round(x, 3), 'y': 0.15, 'z': round(z, 3), 'ry': round(ry, 4), 's': round(s, 4), 's3': s3, 'e': {}}
    put(f'ez-street{sidx}-{lod}-leaves', item); put(f'ez-street{sidx}-{lod}-bark', item)
for x, z in new_pits:
    put('pit', {'x': round(x, 3), 'y': 0.15, 'z': round(z, 3), 'ry': 1.5708, 's': 1, 'e': {'aTint': [0.029, 0.029, 0.029], 'aState': 0}})
json.dump(out, open(EXP + 'streettrees.json', 'w'))
cnt = np.array([a[3] for a in audit]) if audit else np.array([0])
print('removed trees near shot cameras:', len(remove))
print('new trees:', len(new_trees), '(empty pits planted', sum(1 for t in new_trees if t[3] == 'pit'), ', gap fills', sum(1 for t in new_trees if t[3] == 'gap'), ')  new pits:', len(new_pits))
print(f'per-20 m frontage windows: n={len(cnt)} mean {cnt.mean():.2f} min {cnt.min()} share >= 2: {(cnt >= 2).mean() * 100:.0f} %')
json.dump({'windows': audit}, open(EXP + 'streettrees_audit.json', 'w'))
