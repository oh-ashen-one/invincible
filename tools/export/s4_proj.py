#!/usr/bin/env python3
"""(r11) CPU-only preview of the S4 skyline: projects the hinterland boxes (the browser's hinterland.json + the skyline clusters of far_skyline.py / farsky.json) through the S4 camera of city_shots.json
into a 1920x1080 silhouette mask and reports how many 8x8 blocks of the critic's tower box (540,110,900,260) are SKY (no building), i.e. flat bright blocks that no material can texture.
usage: s4_proj.py [export_dir (default citypaths.EXPORT)] [out.png]"""
import sys, os, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from citypaths import EXPORT
ex = sys.argv[1] if len(sys.argv) > 1 else EXPORT
shots = {s['id']: s for s in json.load(open(os.path.join(HERE, '..', '..', 'unreal', 'WebHomage', 'Scripts', 'city_shots.json')))}
S = shots['S4_perch_skyline']; P = np.array(S['pos'], float); T = np.array(S['target'], float); FOV = S.get('fov', 75)
W, H = 1920, 1080; F = (W / 2) / math.tan(math.radians(FOV / 2))
f = T - P; f /= np.linalg.norm(f); r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
def proj(p):
    d = np.asarray(p, float) - P; z = d @ f
    if z < 1: return None
    return (W / 2 + F * (d @ r) / z, H / 2 - F * (d @ u) / z)
items = []
hp = os.path.join(ex, 'hinterland.json')
if os.path.exists(hp): items += json.load(open(hp))['items']
fp = os.path.join(ex, 'farsky.json')
if os.path.exists(fp): items += json.load(open(fp)).get('hinterland', [])
mask = np.zeros((H, W), np.uint8)
for it in items:
    x, y, z, sx, sy, sz, rot = it[:7]
    c, s = math.cos(rot), math.sin(rot); pts = []
    for dx in (-0.5, 0.5):
        for dz in (-0.5, 0.5):
            for yy in (0.0, 1.0):
                px, pz = dx * sx, dz * sz
                pts.append((x + px * c - pz * s, y + yy * sy, z + px * s + pz * c))
    pp = [proj(p) for p in pts]
    if any(q is None for q in pp): continue
    hull = cv2.convexHull(np.round(np.array(pp)).astype(np.int32))
    cv2.fillConvexPoly(mask, hull, 255)
x0, y0, x1, y1 = 540, 110, 900, 260
sky = n = 0
for yy in range(y0, y1 - 7, 8):
    for xx in range(x0, x1 - 7, 8):
        n += 1
        if mask[yy:yy + 8, xx:xx + 8].mean() < 128: sky += 1
top = [int(np.argmax(mask[:, xx] > 0)) if mask[:, xx].any() else H for xx in range(x0, x1)]
print('hinterland items', len(items), '| tower box blocks', n, '| blocks without a building (sky or fogged ground)', sky, '= %.1f %% of the box blocks' % (100.0 * sky / n),
      '| silhouette top row over the box: min %d p25 %d median %d p75 %d max %d' % (min(top), np.percentile(top, 25), np.median(top), np.percentile(top, 75), max(top)))
if len(sys.argv) > 2:
    v = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR); cv2.rectangle(v, (x0, y0), (x1, y1), (0, 255, 255), 1); cv2.rectangle(v, (0, 150), (1300, 300), (0, 255, 0), 1); cv2.imwrite(sys.argv[2], v[60:340, :1500])
