#!/usr/bin/env python3
"""Alignment check: street-lamp lights of the author's night export (tools/night/export_night.mjs) against the lamppost
props of our own city export ($SM2_CITY_EXPORT/layout.json, pool 'lamp') inside the export's tile range.
The light sits at the cobra head: prop + 2.9 m * scale along the prop heading (sin ry, cos ry) at 8.75 m * scale (props.js).
Prints raw numbers as JSON; no pass/fail judgement."""
import json
import math
import os
import statistics
import sys
from pathlib import Path

HEAD = 2.9
NIGHT = Path(os.environ.get('SM2_NIGHT_JSON', Path.home() / 'sm2-n1/_scratch/night/export/night_lights.json'))
EXPORT = Path(os.environ.get('SM2_CITY_EXPORT', Path.home() / 'sm2-n1/_scratch/showcase/manhattan/export/midtown3x3'))


def head_of(p):
    s, ry = p.get('s', 1), p.get('ry', 0.0)
    return p['x'] + HEAD * s * math.sin(ry), p['z'] + HEAD * s * math.cos(ry)


def stats(v):
    if not v:
        return None
    v = sorted(v)
    q = lambda f: round(v[min(len(v) - 1, int(f * len(v)))], 3)
    return {'median': round(statistics.median(v), 3), 'p90': q(0.9), 'max': round(v[-1], 3), 'mean': round(statistics.fmean(v), 3)}


def main():
    manifest = json.loads((EXPORT / 'manifest.json').read_text())
    layout = json.loads((EXPORT / 'layout.json').read_text())
    reg = layout['region']
    tx0, tz0, tx1, tz1 = manifest['tiles']
    pools = layout['instances']
    props = pools['lamp']['items']
    night = json.loads(NIGHT.read_text())
    lights = [s for s in night['statics'] if s['cat'] == 'street_lamp' and reg['x0'] <= s['pos'][0] < reg['x1'] and reg['z0'] <= s['pos'][2] < reg['z1']]
    heads = [head_of(p) for p in props]
    cell = 4.0
    grid = {}
    for i, (hx, hz) in enumerate(heads):
        grid.setdefault((math.floor(hx / cell), math.floor(hz / cell)), []).append(i)
    bases = {}
    for i, p in enumerate(props):
        bases.setdefault((math.floor(p['x'] / cell), math.floor(p['z'] / cell)), []).append(i)

    def nearest(index, pts, x, z, rad=3):
        cx, cz, best = math.floor(x / cell), math.floor(z / cell), (1e9, -1)
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                for i in index.get((cx + dx, cz + dz), ()):
                    px, pz = pts[i]
                    d = math.hypot(px - x, pz - z)
                    if d < best[0]:
                        best = (d, i)
        return best

    base_pts = [(p['x'], p['z']) for p in props]
    # light -> nearest prop head (corrected), and -> nearest prop base (raw, no cobra offset)
    corr = [nearest(grid, heads, s['pos'][0], s['pos'][2]) for s in lights]
    raw = [nearest(bases, base_pts, s['pos'][0], s['pos'][2]) for s in lights]
    # prop -> nearest light (corrected: prop head to light)
    lgrid = {}
    for j, s in enumerate(lights):
        lgrid.setdefault((math.floor(s['pos'][0] / cell), math.floor(s['pos'][2] / cell)), []).append(j)
    lpts = [(s['pos'][0], s['pos'][2]) for s in lights]
    prop_to_light = [nearest(lgrid, lpts, hx, hz) for hx, hz in heads]
    # signed offset light - prop base for the matched pairs (what the 2.9 m should explain)
    vec = [(lights[j]['pos'][0] - props[i]['x'], lights[j]['pos'][2] - props[i]['z']) for j, (d, i) in enumerate(raw) if d < 1e8]
    ht = [abs(lights[j]['pos'][1] - (props[i].get('y', 0) + 8.75 * props[i].get('s', 1))) for j, (d, i) in enumerate(corr) if d < 1e8]
    both = lambda lst, t: sum(1 for d, _ in lst if d <= t)
    report = {
        'night_json': str(NIGHT), 'city_export': str(EXPORT), 'tiles': manifest['tiles'], 'region': reg, 'pool': 'lamp',
        'lights_in_range': len(lights), 'lamp_props_in_layout': len(props), 'lights_total_street_lamp': sum(1 for s in night['statics'] if s['cat'] == 'street_lamp'),
        'cobra_offset_m': HEAD,
        'light_to_prop_head (offset-corrected)': {'within_0.5m': both(corr, 0.5), 'within_2m': both(corr, 2.0), 'unmatched_gt_2m': sum(1 for d, _ in corr if d > 2.0), 'distance': stats([d for d, _ in corr if d < 1e8])},
        'light_to_prop_base (raw, no offset)': {'within_0.5m': both(raw, 0.5), 'within_2m': both(raw, 2.0), 'within_3.5m': both(raw, 3.5), 'unmatched_gt_2m': sum(1 for d, _ in raw if d > 2.0), 'distance': stats([d for d, _ in raw if d < 1e8])},
        'prop_head_to_light': {'within_0.5m': both(prop_to_light, 0.5), 'within_2m': both(prop_to_light, 2.0), 'props_without_light_gt_2m': sum(1 for d, _ in prop_to_light if d > 2.0), 'distance': stats([d for d, _ in prop_to_light if d < 1e8])},
        'median_light_minus_prop_base_xz': [round(statistics.median(v[0] for v in vec), 3), round(statistics.median(v[1] for v in vec), 3)] if vec else None,
        'median_horizontal_offset_light_vs_base_m': round(statistics.median(math.hypot(*v) for v in vec), 3) if vec else None,
        'light_height_error_vs_8.75m': stats(ht),
        'prop_y_values': sorted({p.get('y', 0) for p in props})[:5], 'prop_scales': sorted({p.get('s', 1) for p in props})[:5],
    }
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    sys.exit(main())
