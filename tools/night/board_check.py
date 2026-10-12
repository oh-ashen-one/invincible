#!/usr/bin/env python3
"""Where do the author's screen boards sit relative to OUR city (layout.json building footprints, the same axis-aligned boxes the UE city is built from)?
Each board of Content/Night/NightGeometry.json (UE cm; panel centre, normal, size) is classified with probes +-0.5 m along its normal:
  outside_region   centre outside the detailed region of the export (our UE city has no buildings there)
  on_facade        back probe inside a building, front probe free      (correct)
  inside           both probes inside a building (buried)
  behind_facade    front probe inside, back probe free (faces into a building)
  floating         both probes free
Floating / inside / behind boards are projected along +-normal onto the nearest building face within PROJ_M (3 m): the new centre sits 8 cm in front of the face and the normal becomes the face's outward
normal; with no face in reach they are dropped. usage: board_check.py [--write]   (--write: rewrites the boards block of NightGeometry.json: kept boards only, projected)"""
import argparse
import json
import os
from pathlib import Path

PROJ_M = 3.0
OFFSET_M = 0.08
EXPORT = Path(os.environ.get('SM2_BOARD_EXPORT') or (Path(os.environ.get('SM2_CITY_EXPORT', Path.home() / 'sm2-n1/_scratch/showcase/manhattan/export')) / 'midtown3x3'))   # SM2_BOARD_EXPORT: the export folder holding layout.json (island: ~/sm2-n1/_scratch/island/export/island)
GEO = Path(__file__).resolve().parents[2] / 'unreal/WebHomage/Content/Night/NightGeometry.json'


def load_boxes():
    L = json.loads((EXPORT / 'layout.json').read_text())
    return L['region'], [(f['x0'], f['z0'], f['x1'], f['z1'], f['h']) for f in L['footprints']]


def inside(boxes, x, y, z):
    return any(b[0] <= x <= b[2] and b[1] <= z <= b[3] and 0.0 <= y <= b[4] for b in boxes)


def project(boxes, c, n):
    """nearest hit of the line c + t n, |t| <= PROJ_M, on a building face (x or z plane, y <= h) -> (centre, outward normal) or None"""
    best = None
    for (x0, z0, x1, z1, h) in boxes:
        for face, axis, val, out in ((0, 0, x0, -1), (1, 0, x1, 1), (2, 2, z0, -1), (3, 2, z1, 1)):
            if abs(n[axis]) < 1e-3:
                continue
            t = (val - c[axis]) / n[axis]
            if abs(t) > PROJ_M:
                continue
            p = [c[0] + n[0] * t, c[1] + n[1] * t, c[2] + n[2] * t]
            other = 2 if axis == 0 else 0
            lo, hi = (z0, z1) if axis == 0 else (x0, x1)
            if not (lo - 0.01 <= p[other] <= hi + 0.01 and 0.0 <= p[1] <= h):
                continue
            nrm = [0.0, 0.0, 0.0]; nrm[axis] = float(out)
            if best is None or abs(t) < best[0]:
                best = (abs(t), [p[0] + nrm[0] * OFFSET_M, p[1], p[2] + nrm[2] * OFFSET_M], nrm)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    reg, boxes = load_boxes()
    G = json.loads(GEO.read_text())
    B = G['boards']
    N = len(B) // 20
    cls = {'outside_region': 0, 'on_facade': 0, 'inside': 0, 'behind_facade': 0, 'floating': 0}
    fixed = dropped = 0
    out = []
    for i in range(N):
        r = B[i * 20:(i + 1) * 20]
        c = [r[0] / 100.0, r[2] / 100.0, r[1] / 100.0]            # UE cm (X, Y, Z) -> browser m (x, y, z)
        n = [r[3], r[5], r[4]]
        if not (reg['x0'] <= c[0] <= reg['x1'] and reg['z0'] <= c[2] <= reg['z1']):
            cls['outside_region'] += 1
            dropped += 1                                         # no detailed buildings there: a board would float over the far skyline masses
            continue
        pf = [c[k] + 0.5 * n[k] for k in range(3)]
        pb = [c[k] - 0.5 * n[k] for k in range(3)]
        f_in, b_in = inside(boxes, *pf), inside(boxes, *pb)
        k = 'inside' if (f_in and b_in) else 'on_facade' if b_in else 'behind_facade' if f_in else 'floating'
        cls[k] += 1
        if k != 'on_facade':
            hit = project(boxes, c, n)
            if hit is None:
                dropped += 1
                continue
            fixed += 1
            c, nrm = hit[1], hit[2]
            ux, uz = nrm[2], -nrm[0]                              # u axis along the face (UE (X, Y) = (nz, -nx), same relation as the exported panels)
            r[0], r[1], r[2] = c[0] * 100.0, c[2] * 100.0, c[1] * 100.0
            r[3], r[4], r[5] = nrm[0], nrm[2], nrm[1]
            r[6], r[7], r[8] = ux, uz, 0.0
        out.append(r)
    print(json.dumps({'boards': N, 'classes': cls, 'projected_to_facade': fixed, 'dropped': dropped, 'kept': len(out), 'region': reg}))
    if a.write:
        G['boards'] = [v for r in out for v in r]
        G['counts']['boards'] = len(out)
        G['board_report'] = {'classes': cls, 'projected': fixed, 'dropped': dropped}
        GEO.write_text(json.dumps(G))
        meta = GEO.parent / 'CityLights.meta.json'
        M = json.loads(meta.read_text())
        M['geometry_counts']['boards'] = len(out)
        M['board_report'] = G['board_report']
        meta.write_text(json.dumps(M, indent=1))


if __name__ == '__main__':
    main()
