#!/usr/bin/env python3
"""Parked cars and yellow taxis along the avenue curbs (round 08; critic r07 gap 'streets are empty', CITY-SPEC C4 / C6 / C8).

Placement rules come from the browser game (src/world/layout.js, npc/traffic.js parkedFor) so the Unreal port parks where the browser parks:
  * the 22 m avenues (a +- 11 m) carry a curb lane of 3.6 m on both sides; a car stands at a +- (10.75 - half width) = ~9.6 m, nose along the lane's
    direction (west curb southbound, east curb northbound: right-hand traffic), +- 0.12 m / 0.02 rad noise;
  * no parking lane on Park Av (avenues[5] = 430: median instead of a lane), in a painted bike lane (BIKE_LANES: west curb of avenues[2], east curb of avenues[6] and
    avenues[1] z -560..640) and in the red bus lane (BUS_LANES: west curb of avenues[4], east curb of avenues[3] for z > -60, ...); the bus lane is painted from
    zA + 5.2 + 14 to zB - 5.2 - 14 of each block, the 14 m at each end stay plain asphalt, so bus-lane sides keep parked cars only there;
  * 9.5 m clear of each block end (crosswalk, stop line, bulb-outs), 3 m clear of hydrants, 12 m of bus stops / bike docks, lane-closure cones / drums / sawhorses /
    barriers / roll-offs are obstacles.
Mix (the browser's parked mix with more taxis, the round target says 'cars and yellow taxis'): ~24 % yellow taxis (4 bodies), 4 % vans, sedans / hatch 32 %, SUVs / crossovers 45 %.
Paint: the browser's NYC paint mix (vehinst.js PAL, linear), taxi yellow 0xf5a900.
Output: <export>/streetcars.json  {veh_<model>: [ {x,y,z,ry,s,e:{aTint,aState}} ]}  (same item format as layout.json pool items / streetprops.json; ry = browser yaw about +y,
nose at yaw 0 along +x: nose direction (cos ry, -sin ry) in (x, z)); build_city.py adds the items to the ISMs.
usage: street_cars.py [export_dir] [--density D]   (D = slot fill probability, default 0.92)
"""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from citypaths import EXPORT as _EXPORT
args = [a for a in sys.argv[1:] if not a.startswith('--')]
EXP = (args[0] if args else _EXPORT).rstrip('/') + '/'
DENSITY = float(sys.argv[sys.argv.index('--density') + 1]) if '--density' in sys.argv else 0.92
lay = json.load(open(EXP + 'layout.json')); veh = json.load(open(EXP + 'vehicles.json'))
SHOTS = json.load(open(os.path.join(HERE, '..', '..', 'unreal', 'WebHomage', 'Scripts', 'city_shots.json')))
CAMS = [(c['pos'][0], c['pos'][2]) for c in SHOTS if c['pos'][1] < 10.0]   # street-level shot cameras: no car within 15 m (it would fill the frame) or in the 22 m ahead corridor
REGION = lay['region']                       # exported tiles: asphalt exists only inside
AVS = [-610, -430, -250, 0, 250, 430, 610]
HALF = 11.0; KEEP = 9.5; CURB_EDGE = 10.75

def hrand(*a):
    h = 2166136261
    for v in a:
        h ^= int(abs(v) * 1000003.0) & 0xFFFFFFFF; h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xFFFFFFFF; h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)

def lin(c): return [((c >> 16) & 255) / 255.0, ((c >> 8) & 255) / 255.0, (c & 255) / 255.0]
def lin2(c): return [v ** 2.2 for v in lin(c)]
PAL = [lin2(c) for c in (0x0e0e0f, 0x151517, 0x1b1c1f, 0x101418, 0xe2e2df, 0xd8d8d4, 0xcfcfca, 0xe6e3da, 0xa9adb1, 0x9c9fa3, 0xb7b9bb, 0x8e9296, 0x6d7074, 0x55585c, 0x44474b,
       0x1b2a4a, 0x223a63, 0x2f4c7a, 0x5a1216, 0x6e1a1a, 0x8a1f1f, 0xb3a98f, 0x9b8f75, 0x2c3d2e, 0x44563f, 0x6b86a0, 0x4a3a2c, 0x3b4450, 0x7c8a8f, 0x2a2d33)]
TAXI = lin2(0xf5a900); VANC = [lin2(c) for c in (0xd6d6d2, 0xcfccc4, 0xc9c9c7, 0xd9d7d0)]

def cam_blocked(x, z):
    return any(math.hypot(x - cx, z - cz) < 15.0 or (abs(x - cx) < 3.6 and cz - 22.0 < z < cz + 6.0) for cx, cz in CAMS)

def side_rule(i, side, z):
    """'none' (no parking lane / bike lane), 'bus' (red bus lane in mid-block), 'full'"""
    if i == 5: return 'none'                                                        # Park Av: median instead of a parking lane
    if (i == 2 and side < 0) or (i == 6 and side > 0) or (i == 1 and side > 0 and -560 < z < 640): return 'none'   # painted curb-side bike lane
    if (i == 4 and side < 0) or (i == 3 and side > 0 and z > -60) or (i == 6 and side < 0) or (i == 1 and side < 0 and z < -560): return 'bus'
    return 'full'

def pick(seed_a, seed_b, taxi_p):
    r = hrand(seed_a, seed_b, 1); h = hrand(seed_a, seed_b, 2)
    if r < taxi_p: return 'veh_taxi' if h < 0.15 else 'veh_taxi_hy' if h < 0.55 else 'veh_taxi_mv' if h < 0.8 else 'veh_taxi_gr'   # the browser's taxi body mix (fewer Crown Vics)
    r = (r - taxi_p) / (1 - taxi_p)
    if r < 0.36: return ['veh_sedan', 'veh_sedan2', 'veh_hatch'][int(h * 3) % 3]
    if r < 0.93: return ['veh_suv', 'veh_cross', 'veh_suv2', 'veh_pickup'][int(h * 4) % 4]
    return 'veh_van'

# ---------------------------------------------------------------- obstacles in / next to the roadway
I = lay['instances']
def pts(k): return [(it['x'], it['z']) for it in (I.get(k, {}).get('items') or [])]
road_obst = np.array(pts('cone') + pts('drum') + pts('sawhorse') + pts('barrier') + pts('rolloff') + pts('dumpster') + pts('bikekiosk'))
side_obst = {k: np.array(pts(k)) for k in ('hydrant', 'busstop', 'dock', 'subway')}
def near(arr, x, z, r):
    return len(arr) > 0 and bool((np.hypot(arr[:, 0] - x, arr[:, 1] - z) < r).any())

blocks = []
for s in lay['streets']:
    if s.get('kind') != 'avenue' or 'x0' not in s: continue
    ax = (s['x0'] + s['x1']) / 2
    if ax not in AVS or s['z1'] - s['z0'] < 30: continue
    blocks.append((AVS.index(ax), ax, s['z0'], s['z1']))
blocks.sort(key=lambda b: (b[1], b[2]))

out = {}; stats = {'cars': 0, 'taxis': 0, 'blocks': 0}; windows = []
for i, ax, z0, z1 in blocks:
    L = z1 - z0
    if z1 < REGION['z0'] + 8 or z0 > REGION['z1'] - 8: continue
    for side in (-1, 1):
        rule = side_rule(i, side, (z0 + z1) / 2)
        if rule == 'none': continue
        if rule == 'bus':
            wins = [(z0 + KEEP, z0 + 5.2 + 14.0 - 0.3), (z1 - 5.2 - 14.0 + 0.3, z1 - KEEP)]   # plain asphalt at both block ends (the red paint runs y0 + 14 .. y1 - 14)
        else:
            wins = [(z0 + KEEP, z1 - KEEP)]
        ry = -math.pi / 2 if side < 0 else math.pi / 2            # west curb southbound (+z), east curb northbound (-z)
        placed = []
        for wi, (lo, hi) in enumerate(wins):
            lo = max(lo, REGION['z0'] + 6); hi = min(hi, REGION['z1'] - 6)
            cursor = lo + 0.4 + hrand(ax, z0, side, wi) * 1.4
            n = 0
            while True:
                n += 1
                kind = pick(ax * 3.1 + side, z0 + cursor, 0.24)
                m = veh[kind]; ln = m['len']
                if cursor + ln > hi: break
                zc = cursor + ln / 2
                lat = CURB_EDGE - m['wid'] / 2 + 0.05 - hrand(ax, zc, 5) * 0.14
                x = ax + side * lat
                # the model origin is not its centre: shift so the body centre stands at zc (nose direction d = (cos ry, -sin ry) in (x, z))
                cx = (m['x0'] + m['x1']) / 2
                px, pz = x - cx * math.cos(ry), zc + cx * math.sin(ry)
                gap = 0.85 + hrand(ax, zc, 6) * 0.9
                skip = hrand(ax, zc, 7) > DENSITY
                blocked = (near(road_obst, x, zc, ln / 2 + 1.4)
                           or near(side_obst['hydrant'], ax + side * HALF, zc, ln / 2 + 0.7)
                           or near(side_obst['busstop'], ax + side * (HALF + 1), zc, 12.0) or near(side_obst['dock'], ax + side * HALF, zc, 8.0) or near(side_obst['subway'], ax + side * HALF, zc, 6.0))
                blocked = blocked or cam_blocked(x, zc) or cam_blocked(x, zc - ln / 2) or cam_blocked(x, zc + ln / 2)
                if skip or blocked:
                    cursor += (ln + gap) if skip else 1.2; continue
                seedk = hrand(ax, zc, 8)
                if kind == 'veh_van': tint = VANC[int(seedk * 4) % 4]
                elif m['taxi']: tint = TAXI
                else: tint = PAL[int(seedk * len(PAL)) % len(PAL)]
                yaw = ry + (hrand(ax, zc, 9) - 0.5) * 0.04
                out.setdefault(kind, []).append({'x': round(px, 3), 'y': 0.05, 'z': round(pz, 3), 'ry': round(yaw, 4), 's': 1, 'e': {'aTint': [round(v, 4) for v in tint], 'aState': 0}})
                placed.append(zc); stats['cars'] += 1; stats['taxis'] += int(m['taxi'])
                cursor += ln + gap
        stats['blocks'] += 1
        # per-20 m window audit on the parking sides ('full'): cars per 20 m of the parkable length
        if rule == 'full' and L > 40:
            pz = np.array(placed)
            for w0 in np.arange(z0 + KEEP, z1 - KEEP - 19.9, 20.0):
                if w0 < REGION['z0'] + 6 or w0 + 20 > REGION['z1'] - 6: continue   # asphalt exists only inside the exported tiles
                windows.append((ax, side, round(w0, 1), int(((pz >= w0) & (pz < w0 + 20)).sum())))
json.dump(out, open(EXP + 'streetcars.json', 'w'))
cnt = np.array([w[3] for w in windows]) if windows else np.array([0])
print({k: len(v) for k, v in sorted(out.items())}, stats)
print(f'per-20 m windows on parking sides: n={len(cnt)} mean {cnt.mean():.2f} min {cnt.min()} share >= 2: {(cnt >= 2).mean() * 100:.0f} %')
json.dump({'windows': windows, 'stats': stats}, open(EXP + 'streetcars_audit.json', 'w'))
