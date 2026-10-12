#!/usr/bin/env python3
"""Island district cameras for -WHShotCam: a street view (1.7 m) and an elevated 40 m view in four districts, positions picked from the island layout.json:
  battery   = the tallest cluster of the south end (z > 2400: Financial District), the nearest avenue segment, looking north
  midtown   = the shot_street camera of the matched set (x 250, z 170) + its 40 m twin
  park      = the Central Park south edge (park tiles' southern boundary z = -896; the avenue segment just south of it, x ~ -20), looking north into the park
  uws       = west of the park (x < -362), z ~ -1500, the avenue segment nearest to (-430, -1500), looking north
usage: gen_island_cams.py [--out FILE]   (default ~/sm2-n1/_scratch/showcase/island_cams.json; browser metres, x east, z south, y up -> UE cm (x, z, y) * 100)"""
import argparse
import json
import math
from pathlib import Path

LAYOUT = Path.home() / 'sm2-n1/_scratch/island/export/island/layout.json'
HFOV = 74.078


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(Path.home() / 'sm2-n1/_scratch/showcase/island_cams.json'))
    a = ap.parse_args()
    L = json.loads(LAYOUT.read_text())
    avs = [((s['x0'] + s['x1']) / 2, (s['z0'] + s['z1']) / 2) for s in L['streets'] if s.get('kind') == 'avenue' and 'x0' in s]
    near = lambda x, z: min(avs, key=lambda p: (p[0] - x) ** 2 + (p[1] - z) ** 2)
    tall = [f for f in L['footprints'] if (f['z0'] + f['z1']) / 2 > 2400 and f['h'] > 90]
    cx = sum((f['x0'] + f['x1']) / 2 for f in tall) / len(tall); cz = sum((f['z0'] + f['z1']) / 2 for f in tall) / len(tall)
    spots = [('battery', near(cx, cz + 60)), ('midtown', (250.0, 170.0)), ('park', near(-20.0, -860.0)), ('uws', near(-430.0, -1500.0))]
    out = []
    t = 15.0
    for name, (x, z) in spots:
        for kind, y, back, ty in (('street', 1.7, 0.0, 6.0), ('high', 40.0, 50.0, 26.0)):
            pos = (x, y, z + back); tgt = (x, ty, z - 200.0)
            ue = lambda p: [round(p[0] * 100.0, 1), round(p[2] * 100.0, 1), round(p[1] * 100.0, 1)]
            out.append({'t': t, 'name': '%s_%s' % (name, kind), 'ue_pos_cm': ue(pos), 'ue_target_cm': ue(tgt), 'fov': HFOV, 'hero_visible': False})
            t += 14.0
    Path(a.out).write_text(json.dumps(out, indent=1))
    print('wrote', a.out, len(out), 'shots; battery cluster centre (%.0f, %.0f), %d tall footprints; spots %s' % (cx, cz, len(tall), [(n, tuple(round(v) for v in p)) for n, p in spots]))


if __name__ == '__main__':
    main()
