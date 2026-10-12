#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Matched cameras (-WHShotCam) for the PropsM3 verification stills: 4 districts, each a street-level view (1.7 m) of the densest mixed
cluster of PropsM3 placements and a swing-height view (25 m up, 35-75 m away, preferably over a road looking along the avenue axis,
with a clear line of sight over tree crowns and buildings).
Camera positions are checked against the placement ground raster (never inside a building / obstacle, line of sight over open ground).
usage: district_cams.py [--prep DIR] [--out FILE]   (browser metres -> UE cm (x, z, y) * 100)"""
import argparse, json, math, os
from collections import Counter
import numpy as np

PREP = os.path.expanduser('~/sm2-n1/_scratch/final/assets/prep')
ISL = os.path.expanduser('~/sm2-n1/_scratch/island/export/island/layout.json')
X0, Z0 = -960.0, -3520.0   # place_props_m3 raster origin; ground.npz is the 1 m downsample
DISTRICTS = {'midtown': (-500, -560, 700, 1200), 'parksouth': (-234, -1000, 234, -569), 'westpiers': (-960, -2300, -600, 1600), 'downtown': (-700, 2300, 900, 3400)}
PREFER = {'midtown': ('oildrum',), 'parksouth': ('squirrel', 'pigeon'), 'westpiers': ('gull', 'rat'), 'downtown': ('crate', 'oildrum', 'cat', 'pigeon')}   # every class shown somewhere
HFOV = 74.078


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--prep', default=PREP); ap.add_argument('--out', default=os.path.join(PREP, 'district_cams.json'))
    a = ap.parse_args()
    P = json.load(open(os.path.join(a.prep, 'placements.json')))['items']
    g = np.load(os.path.join(a.prep, 'ground.npz')); cls = g['cls']; nogo = g['nogo']; canopy = g['canopy']
    lay = json.load(open(ISL)); streets = [s for s in lay['streets'] if 'x0' in s]
    A = [(k, p) for k, L in P.items() for p in L]; xy = np.array([[p[0], p[2]] for k, p in A]); kinds = np.array([k for k, p in A])
    def c_at(x, z):
        i, j = int(z - Z0), int(x - X0)
        return int(cls[i, j]) if 0 <= i < cls.shape[0] and 0 <= j < cls.shape[1] else 0
    def at(arr, x, z):
        i, j = int(z - Z0), int(x - X0)
        return bool(arr[i, j]) if 0 <= i < arr.shape[0] and 0 <= j < arr.shape[1] else True
    def roomy(x, z):   # a camera spot: open ground, not in a walk band / pool item disc, nothing solid within 2 m
        return c_at(x, z) in (1, 2, 3, 4, 5) and not at(nogo, x, z) and all(c_at(x + dx, z + dz) not in (8, 9) for dx in (-2, 0, 2) for dz in (-2, 0, 2))
    def clear_line(x0, z0, x1, z1):
        n = int(math.hypot(x1 - x0, z1 - z0)) + 1
        return all(c_at(x0 + (x1 - x0) * t / n, z0 + (z1 - z0) * t / n) not in (8, 9) for t in range(n))
    out, info = [], {}
    t = 16.0
    for name, (x0, z0, x1, z1) in DISTRICTS.items():
        m = (xy[:, 0] > x0) & (xy[:, 0] < x1) & (xy[:, 1] > z0) & (xy[:, 1] < z1)
        cands = []
        for i in np.where(m)[0]:
            sel = np.hypot(*(xy - xy[i]).T) < 15
            if at(canopy, xy[i][0], xy[i][1]): continue   # visible from swing height: no tree crown over the cluster
            cands.append((len(set(kinds[sel])) * 10 + sel.sum() + 25 * len(set(kinds[sel]) & set(PREFER[name])), int(i)))
        cands.sort(reverse=True)
        seen = []; fails = {}
        for score, i in cands[:400]:
            sel = np.hypot(*(xy - xy[i]).T) < 15; cx, cz = xy[sel].mean(0)
            if any(math.hypot(cx - a_, cz - b_) < 10 for a_, b_ in seen): continue
            seen.append((cx, cz))
            # street camera: 9-13 m from the cluster centre, open line of sight, standing on open ground
            cam = None
            for r in (10.0, 12.0, 8.0, 14.0):
                for k in range(24):
                    ang = k * math.pi / 12
                    px, pz = cx + math.cos(ang) * r, cz + math.sin(ang) * r
                    if roomy(px, pz) and clear_line(px, pz, cx, cz):
                        cam = (px, pz); break
                if cam: break
            if not cam:
                fails['street'] = fails.get('street', 0) + 1; continue
            # swing-height camera: 25 m up, 35-75 m from the cluster, preferably over an avenue / street looking along it; the ray to the cluster must
            # clear tree crowns (below 14 m) and buildings, and the camera must not sit inside a crown
            def ray_ok(hx, hz):
                n = int(math.hypot(cx - hx, cz - hz))
                for k in range(1, n):
                    f = k / n; x, z = hx + (cx - hx) * f, hz + (cz - hz) * f; h = 25.0 * (1 - f) + 0.3 * f
                    if c_at(x, z) == 8: return False
                    if at(canopy, x, z) and h < 14.0: return False
                return not at(canopy, hx, hz)
            best = None
            for d in (45.0, 55.0, 35.0, 65.0, 75.0):
                for k in range(36):
                    ang = k * math.pi / 18; hx, hz = cx + math.cos(ang) * d, cz + math.sin(ang) * d
                    if c_at(hx, hz) == 8 or not ray_ok(hx, hz): continue
                    score = (3 if c_at(hx, hz) == 6 else 0) + 2 * abs(math.sin(ang)) - abs(d - 50) / 50   # over a road, looking along the avenue axis (z)
                    if best is None or score > best[0]: best = (score, hx, hz)
            if best is None:
                s = min(streets, key=lambda s: math.hypot(max(s['x0'] - cx, 0, cx - s['x1']), max(s['z0'] - cz, 0, cz - s['z1'])))
                hx, hz = cx, cz + 45.0
            else:
                s = None; hx, hz = best[1], best[2]
            if best is not None: break
            fails['high'] = fails.get('high', 0) + 1
        print(name, 'candidate failures', fails, flush=True)
        ue = lambda x, y, z: [round(x * 100.0, 1), round(z * 100.0, 1), round(y * 100.0, 1)]
        out.append({'t': t, 'name': name + '_street', 'ue_pos_cm': ue(cam[0], 1.7, cam[1]), 'ue_target_cm': ue(cx, 0.35, cz), 'fov': HFOV, 'hero_visible': False}); t += 14.0
        out.append({'t': t, 'name': name + '_high', 'ue_pos_cm': ue(hx, 25.0, hz), 'ue_target_cm': ue(cx, 0.0, cz), 'fov': HFOV, 'hero_visible': False}); t += 14.0
        info[name] = {'cluster_centre_m': [round(cx, 1), round(cz, 1)], 'cluster': dict(Counter(kinds[sel].tolist())), 'street_cam_m': [round(cam[0], 1), round(cam[1], 1)],
                      'high_cam_m': [round(hx, 1), 25.0, round(hz, 1)], 'high_ray_clear': best is not None}
    json.dump(out, open(a.out, 'w'), indent=1)
    json.dump(info, open(a.out.replace('.json', '_info.json'), 'w'), indent=1)
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
