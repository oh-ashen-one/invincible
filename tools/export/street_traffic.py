#!/usr/bin/env python3
"""Stopped / slow avenue traffic for the City test maps (round 08; CITY-SPEC C6: 'avenue seen from swing height: vehicles median 14-22 per frame').

Parked cars alone put ~10 detectable vehicles into the S2 swing view (the first 80 m of the avenue are below the frame), so the four travel lanes carry cars too:
per lane and block a queue at the stop line (0-3 cars, mean 0.9, the red-light platoon the browser's signals produce: stop lines at zA + 4.6 northbound (east half) and zB - 4.6
southbound (west half), ground.js) and sparse free-flow cars behind it. The cars stand still (there is no simulation in the City test maps; P6 owns the moving traffic
and pedestrians: build_city.py puts these cars into their OWN actors under the World Outliner folder City/Traffic so the integrated map can hide or delete them).
Same models, paint mix and item format as street_cars.py. Lane centres +-1.8 / +-5.4 m (Park Av, shifted around its median: +-3.7 / +-7.1). Cars keep clear of the lane-closure
props, of a 14 m disc around every street-level shot camera and of a 3.6 m wide corridor 22 m ahead of it (so the camera lane is empty in front of the lens, like the refs).
Output: <export>/streettraffic.json  {veh_<model>: [items]}
usage: street_traffic.py [export_dir]
"""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from citypaths import EXPORT as _EXPORT, REPO
EXP = (sys.argv[1] if len(sys.argv) > 1 else _EXPORT).rstrip('/') + '/'
lay = json.load(open(EXP + 'layout.json')); veh = json.load(open(EXP + 'vehicles.json')); R = lay['region']
shots = json.load(open(os.path.join(REPO, 'unreal', 'WebHomage', 'Scripts', 'city_shots.json')))
CAMS = [(s['pos'][0], s['pos'][2]) for s in shots if s['pos'][1] < 10.0]
AVS = [-250, 0, 250, 430]
sys.argv = sys.argv[:1]
# reuse hrand / paints from street_cars without re-running it: import the constants by exec of the top part only
src = open(os.path.join(HERE, 'street_cars.py')).read().split('# ---------------------------------------------------------------- obstacles')[0]
ns = {'__file__': os.path.join(HERE, 'street_cars.py')}; exec(compile(src, 'street_cars_head', 'exec'), ns)
hrand, PAL, TAXI, VANC = ns['hrand'], ns['PAL'], ns['TAXI'], ns['VANC']
I = lay['instances']
def pts(k): return [(it['x'], it['z']) for it in (I.get(k, {}).get('items') or [])]
road_obst = np.array(pts('cone') + pts('drum') + pts('sawhorse') + pts('barrier') + pts('rolloff') + pts('dumpster'))

def pick(a, b):
    r = hrand(a, b, 11); h = hrand(a, b, 12)
    if r < 0.14: return 'veh_taxi' if h < 0.15 else 'veh_taxi_hy' if h < 0.6 else 'veh_taxi_mv' if h < 0.85 else 'veh_taxi_gr'
    if r < 0.47: return ['veh_sedan', 'veh_sedan2', 'veh_hatch'][int(h * 3) % 3]
    if r < 0.955: return ['veh_suv', 'veh_cross', 'veh_suv2', 'veh_pickup'][int(h * 4) % 4]
    return 'veh_van'

def cam_blocked(x, z):
    for cx, cz in CAMS:
        if math.hypot(x - cx, z - cz) < 14.0: return True
        if abs(x - cx) < 3.6 and cz - 22.0 < z < cz + 6.0: return True
    return False

blocks = []
for s in lay['streets']:
    if s.get('kind') != 'avenue' or 'x0' not in s: continue
    ax = (s['x0'] + s['x1']) / 2
    if ax in AVS and s['z1'] - s['z0'] >= 30: blocks.append((ax, s['z0'], s['z1']))
blocks.sort()
out = {}; n = 0; per_block = []
for ax, z0, z1 in blocks:
    if z1 < R['z0'] + 8 or z0 > R['z1'] - 8: continue
    lanes = (3.7, 7.1) if ax == 430 else (1.8, 5.4)
    cnt_b = 0
    for side in (-1, 1):                       # west half southbound (+z), east half northbound (-z)
        ry = -math.pi / 2 if side < 0 else math.pi / 2
        for li, lat in enumerate(lanes):
            x = ax + side * lat
            stop = (z1 - 4.6 - 1.4) if side < 0 else (z0 + 4.6 + 1.4)      # front bumper of the first queued car
            direction = -1.0 if side < 0 else 1.0                             # z direction from the stop line back into the block (southbound queue extends to smaller z)
            # queue length by hash: 0..4
            u = hrand(ax, z0, side * 7 + li)
            kq = 0 if u < 0.4 else 1 if u < 0.76 else 2 if u < 0.94 else 3
            placed = []                                                       # (z centre, half length)
            frontz = stop
            def add(kind, zc_front):
                global n
                m = veh[kind]; ln = m['len']
                zc = zc_front + direction * ln / 2                            # body centre; front bumper at zc_front
                if zc - ln / 2 < z0 + 6 or zc + ln / 2 > z1 - 6: return False
                if zc < R['z0'] + 6 or zc > R['z1'] - 6: return False
                if len(road_obst) and (np.hypot(road_obst[:, 0] - x, road_obst[:, 1] - zc) < ln / 2 + 1.6).any(): return False
                if cam_blocked(x, zc) or cam_blocked(x, zc - direction * ln / 2) or cam_blocked(x, zc + direction * ln / 2): return False
                if any(abs(zc - pz) < ln / 2 + ph + 1.2 for pz, ph in placed): return False
                cx = (m['x0'] + m['x1']) / 2
                px, pz = x + 0.0 - cx * math.cos(ry) + 0.0, zc + cx * math.sin(ry)
                seedk = hrand(ax, zc, 13)
                tint = VANC[int(seedk * 4) % 4] if kind == 'veh_van' else TAXI if m['taxi'] else PAL[int(seedk * len(PAL)) % len(PAL)]
                yaw = ry + (hrand(ax, zc, 14) - 0.5) * 0.03
                out.setdefault(kind, []).append({'x': round(px + (hrand(ax, zc, 15) - 0.5) * 0.5, 3), 'y': 0.05, 'z': round(pz, 3), 'ry': round(yaw, 4), 's': 1, 'e': {'aTint': [round(v, 4) for v in tint], 'aState': 0}})
                placed.append((zc, ln / 2)); n += 1
                return True
            # queue at the stop line
            for q in range(kq):
                kind = pick(ax * 5.3 + side * 2 + li, z0 + q * 7.7)
                ln = veh[kind]['len']
                if add(kind, frontz): cnt_b += 1
                frontz += direction * (ln + 1.1 + hrand(ax, z0, q + li * 9) * 1.5)
            # free-flow cars behind the queue: one every ~25-45 m
            frontz += direction * (8.0 + hrand(ax, z0, 31 + li + side) * 18.0)
            while True:
                kind = pick(ax * 5.3 + side * 2 + li + 1, z0 + frontz)
                ln = veh[kind]['len']
                zc = frontz + direction * ln / 2
                if zc - ln / 2 < z0 + 6 or zc + ln / 2 > z1 - 6: break
                if hrand(ax, frontz, li + side) < 0.55 and add(kind, frontz): cnt_b += 1
                frontz += direction * (ln + 12.0 + hrand(ax, frontz, 5) * 26.0)
    per_block.append(cnt_b)
json.dump(out, open(EXP + 'streettraffic.json', 'w'))
print({k: len(v) for k, v in sorted(out.items())}, 'lane cars:', n, 'blocks:', len(per_block), 'mean per block %.1f' % (sum(per_block) / max(1, len(per_block))))
