#!/usr/bin/env python3
"""Census of street-kit elements whose centre projects into a crop of a shot (pass test of round 05: S1, 4K, x 0-1600, y 800-1700).
Pinhole projection of the shot camera (city_shots.json; horizontal fov as the game's CameraActor uses it), NOT depth-tested: elements hidden by
trees or buildings are counted. The pixel evidence is in the crop images. usage: crop_census.py <shot id> <W> <H> x0 y0 x1 y1"""
import json, math, os, sys
import numpy as np
sid, W, H, x0, y0, x1, y1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), *[int(v) for v in sys.argv[4:8]]
here = os.path.dirname(os.path.abspath(__file__))
shots = {s['id']: s for s in json.load(open(os.path.join(here, '../../unreal/WebHomage/Scripts/city_shots.json')))}
s = shots[sid]
E = json.load(open(os.path.join(__import__('citypaths').EXPORT, 'streetkit.json')))['elements']
pos = np.array(s['pos'], float); tgt = np.array(s['target'], float)
f = tgt - pos; f /= np.linalg.norm(f); r = np.cross(f, [0, 1.0, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
focal = (W / 2) / math.tan(math.radians(s.get('fov', 70)) / 2)
cnt = {}; inside = []
for e in E:
    p = np.array(e[1:4]); d = p - pos; z = d @ f
    if z <= 1.0: continue
    px = W / 2 + focal * (d @ r) / z; py = H / 2 - focal * (d @ u) / z
    if x0 <= px <= x1 and y0 <= py <= y1:
        cnt[e[0]] = cnt.get(e[0], 0) + 1; inside.append((e[0], round(px), round(py), round(z, 1)))
print(json.dumps({'shot': sid, 'crop': [x0, y0, x1, y1], 'projected_element_counts': cnt}))
for i in sorted(inside, key=lambda t: t[3])[:40]: print(' ', i)
