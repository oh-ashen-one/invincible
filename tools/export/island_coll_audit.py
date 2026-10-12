#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A): static collision audit of a city export -- does the traversal's collision (the WHBox cubes) match what is DRAWN?
Pure Python (numpy), no Unreal.

    python3 tools/export/island_coll_audit.py <export_dir> [out.json] [--legacy]

  --legacy  audit the round-0 box rule (collision.json BOX solids wall / bulkhead / watertower / spire / hero / glass, >= 3 m tall,
            P4's Look_Boxes) instead of <export_dir>/whboxes.json (tools/export/island_boxes.py, what build_city.py spawns now)

1 m grid over the export region (browser metres, x east, z south), rasters from island_boxes.drawn_rasters():
  H_vis  drawn building mass top (roof up-facing triangles, facade edge tops);  H_all = H_vis + detail / landmark / signage meshes;
  H_box  highest WHBox top.
Over every cell where a building is drawn or boxed (H_vis > 3 m or H_box > 3 m):
  phantom   H_box > H_all + 1.5 m   collision above everything drawn: landing / running in mid-air
  hollow    H_vis > H_box + 1.5 m   drawn building above the collision: the hero sinks into / passes through it  (mass: > 6 m)
Headline numbers are on INTERIOR cells (the 3 x 3 neighbourhood has the same verdict): a 1 m rim along a facade (cornice overhang, raster
edge) is not something a hero lands on. Raw (un-eroded) numbers are reported too. Also: facadeLod meshes inside the detailed region."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from island_boxes import drawn_rasters, select

TOL = 1.5


def legacy_boxes(E):
    C = json.load(open(os.path.join(E, 'collision.json')))
    out = []
    for s in C['solids']:
        if s['t'] != 0 or s['k'] not in (0, 7, 8, 13, 14, 17): continue
        x0, y0, z0, x1, y1, z1 = s['bb']
        if (y1 - y0) < 3.0 or ((x1 - x0) < 1.2 and (z1 - z0) < 1.2): continue
        out.append([x0, y0, z0, x1, y1, z1, s['k'], 'legacy'])
    return out


def boxes_of(E, legacy=False):
    """the WHBox list the build spawns: whboxes.json if present (island_boxes.py), else the legacy rule"""
    p = os.path.join(E, 'whboxes.json')
    if not legacy and os.path.exists(p): return json.load(open(p))['boxes']
    return legacy_boxes(E)


def erode(m):
    e = m.copy()
    e[1:-1, 1:-1] = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:] & m[:-2, :-2] & m[2:, 2:] & m[:-2, 2:] & m[2:, :-2]
    e[0, :] = e[-1, :] = False; e[:, 0] = e[:, -1] = False
    return e


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    legacy = '--legacy' in sys.argv
    E = a[0]
    out_path = a[1] if len(a) > 1 else os.path.join(E, 'coll_audit%s.json' % ('_legacy' if legacy else ''))
    M = json.load(open(os.path.join(E, 'manifest.json')))
    reg, hv, ha = drawn_rasters(E)
    X0, Z0 = reg['x0'], reg['z0']; NZ, NX = hv.shape
    lod_inside = [r['file'] for r in M['meshes'] if r['name'].startswith('facadeLod') and X0 <= r['center'][0] < reg['x1'] and Z0 <= r['center'][2] < reg['z1']]
    B = boxes_of(E, legacy)
    Hb = np.zeros((NZ, NX), np.float32)
    for x0, y0, z0, x1, y1, z1, *_ in B:
        c0, c1 = max(int(np.floor(x0 - X0 + 0.5)), 0), min(int(np.floor(x1 - X0 + 0.5)), NX)
        r0, r1 = max(int(np.floor(z0 - Z0 + 0.5)), 0), min(int(np.floor(z1 - Z0 + 0.5)), NZ)
        if c1 > c0 and r1 > r0: np.maximum(Hb[r0:r1, c0:c1], y1, out=Hb[r0:r1, c0:c1])
    hb = Hb
    bld = (hv > 3.0) | (hb > 3.0)
    phantom = bld & (hb > ha + TOL)
    hollow = bld & (hv > hb + TOL)
    hollow_mass = hollow & (hv > hb + 6.0)
    phantom_mass = phantom & (hb > ha + 6.0)
    ph_i, ho_i, hm_i, pm_i = erode(phantom), erode(hollow), erode(hollow_mass), erode(phantom_mass)
    match = bld & ~phantom & ~hollow
    nb = int(bld.sum())
    pct = lambda m: round(100.0 * float(m.sum()) / max(nb, 1), 2)
    res = {'export': E, 'boxes_source': 'legacy (collision.json BOX, >= 3 m: Look_Boxes rule)' if legacy else 'whboxes.json (island_boxes.py)',
           'region': reg, 'grid_m': 1.0, 'tolerance_m': TOL, 'boxes': len(B), 'building_cells_m2': nb,
           'phantom_pct': pct(ph_i), 'phantom_mass_pct (>6 m)': pct(pm_i), 'hollow_pct': pct(ho_i), 'hollow_mass_pct (>6 m)': pct(hm_i),
           'raw (no erosion)': {'match_pct': pct(match), 'phantom_pct': pct(phantom), 'hollow_pct': pct(hollow), 'hollow_mass_pct': pct(hollow_mass)},
           'facadeLod_meshes_inside_region': len(lod_inside)}
    json.dump(res, open(out_path, 'w'), indent=1)
    np.save(os.path.join(os.path.dirname(out_path), 'coll_audit_ha.npy'), ha.astype(np.float16))
    try:   # map: grey = match, red = phantom (box above drawn), blue = hollow (drawn above box; dark blue > 6 m), black = street
        from PIL import Image
        img = np.zeros((NZ, NX, 3), np.uint8); img[match] = (150, 150, 150); img[hollow] = (90, 140, 255); img[hollow_mass] = (0, 40, 200); img[phantom] = (255, 40, 40)
        Image.fromarray(img).save(os.path.splitext(out_path)[0] + '_map.png')
    except Exception as ex: print('map png failed', ex)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
