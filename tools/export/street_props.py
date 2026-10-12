#!/usr/bin/env python3
"""Supplemental street furniture along both sidewalks of the avenues (round 05): one hydrant, one trash can, one newspaper box and one tree pit
(iron-fenced pit prototype) every ~20 m of frontage, mid-block as well as at the corners (the browser's pools cluster them at the corners:
17 hydrants along 520 m of 5th Av). Uses the browser's own prototypes (pools hydrant / trash / newsbox / pit) and adds items to the same pools; build_city.py
appends them to the ISM instances.  Output: <export>/streetprops.json  {pool: [ {x,y,z,ry,s,e:{aTint,aState}} ]}
usage: street_props.py [export_dir]"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from street_faces import load_faces, EXPORT
EXP = sys.argv[1] if len(sys.argv) > 1 else EXPORT
lay = json.load(open(EXP + 'layout.json'))
faces = load_faces(EXP)
streets = [s for s in lay['streets'] if 'x0' in s]

def hrand(*a):
    h = 2166136261
    for v in a:
        h ^= int(abs(v) * 1000003.0) & 0xFFFFFFFF; h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xFFFFFFFF; h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)

def in_street(x, z):
    return any(s['x0'] <= x <= s['x1'] and s['z0'] <= z <= s['z1'] for s in streets)

def curb_distance(f, u):
    O = np.array(f['O']); T = np.array(f['T']); N = np.array(f['N'])
    for n in np.arange(1.0, 12.0, 0.1):
        p = O + T * u + N * n
        if in_street(p[0], p[1]): return float(n)
    return 5.0

# existing obstacles: every instance of the street-level pools + lamps / poles + trees
obst = []
for k in ('hydrant', 'trash', 'newsbox', 'pit', 'pit2', 'bench', 'planter', 'mailbox', 'bikerack', 'signpole', 'lamp', 'mast', 'post', 'shed', 'meter', 'payphone', 'kiosk', 'busstop'):
    for i in lay['instances'].get(k, {}).get('items') or []: obst.append((i['x'], i['z'], 1.8 if k in ('shed', 'busstop') else 1.1))
for k, v in lay['instances'].items():
    if k.startswith('trees') or k.startswith('trunks'):
        for i in v.get('items') or []: obst.append((i['x'], i['z'], 1.2))
obst = np.array(obst) if obst else np.zeros((0, 3))

def free(x, z, r=1.4):
    if len(obst) == 0: return True
    d = np.hypot(obst[:, 0] - x, obst[:, 1] - z)
    return bool((d > np.maximum(obst[:, 2], r)).all())

HYD = [(0.8, 0.05, 0.03), (0.9, 0.7, 0.05), (0.55, 0.55, 0.53), (0.8, 0.05, 0.03)]
TRASH = [(0.02, 0.05, 0.03), (0.12, 0.12, 0.13), (0.03, 0.05, 0.1), (0.08, 0.08, 0.09)]
NEWS = [(0.75, 0.06, 0.05), (0.06, 0.15, 0.6), (0.85, 0.65, 0.05), (0.06, 0.45, 0.12), (0.55, 0.55, 0.57)]
out = {'hydrant': [], 'trash': [], 'newsbox': [], 'pit': []}
stats = {'stations': 0}
for fi, f in enumerate(faces):
    if abs(f['N'][0]) < 0.9: continue  # avenue frontage only
    O = np.array(f['O']); T = np.array(f['T']); N = np.array(f['N'])
    W = f['W']; u = 6.0 + 4.0 * hrand(f['seed'], 1)
    while u < W - 4.0:
        nc = curb_distance(f, u)
        ny = math.atan2(N[0], N[1])   # yaw that turns the model's +z toward the street
        def put(pool, du, n, tint, ry):
            for nud in (0.0, 1.6, -1.6, 3.2, -3.2):
                uu = u + du + nud
                if uu > W - 1.0 or uu < 1.0: continue
                p = O + T * uu + N * n
                if free(p[0], p[1], 1.1): break
            else: return
            out[pool].append({'x': round(float(p[0]), 3), 'y': 0.15, 'z': round(float(p[1]), 3), 'ry': round(ry, 4), 's': 1, 'e': {'aTint': list(tint), 'aState': 0}})
        r = hrand(f['seed'], u)
        put('hydrant', 0.0, nc - 0.55, HYD[int(r * len(HYD)) % len(HYD)], hrand(f['seed'], u, 2) * 6.28)
        put('trash', 3.4, nc - 0.75, TRASH[int(hrand(f['seed'], u, 3) * len(TRASH)) % len(TRASH)], hrand(f['seed'], u, 4) * 6.28)
        put('newsbox', 7.2, nc - 0.65, NEWS[int(hrand(f['seed'], u, 5) * len(NEWS)) % len(NEWS)], ny + (1.5708 if hrand(f['seed'], u, 6) < 0.5 else -1.5708))
        put('pit', 12.5, nc - 1.05, (0.029, 0.029, 0.029), 1.5708 if abs(N[0]) > 0.5 else 0.0)
        stats['stations'] += 1
        u += 18.0 + 4.0 * hrand(f['seed'], u, 7)
json.dump(out, open(EXP + 'streetprops.json', 'w'))
print({k: len(v) for k, v in out.items()}, stats)
