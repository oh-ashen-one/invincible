#!/usr/bin/env python3
"""Pack the author's night-city lights (tools/night/export_night.mjs -> night_lights.json) into the runtime file read by
AWHCityLights: unreal/WebHomage/Content/Night/CityLights.bin (+ CityLights.meta.json). Content/ is generated and git-ignored.

CityLights.bin, little-endian:
  header   4s magic 'SM2L' | u32 version = 1 | u32 count | 40s commit (pinned ~/spiderbench commit, ASCII)        (52 bytes)
  block A  count x ( 16 x float32 + 4 x u8 )                                                                    (68 bytes each)
             f32: pos UE cm (3), dir UE (3: spot axis / rect normal), u UE (3: rect width axis), colour linear RGB (3, max channel 1),
                  intensity (browser units: point/spot irradiance at 1 m, rect radiance), range cm, width cm, height cm
             u8 : category, type (0 point, 1 spot, 2 rect), flags (bit0 day, bit1 noShadow), volume * 255
  block B  count x ( 4 x float32 )  cosO, cosI, radius cm, spec                                                 (16 bytes each)
Browser metres -> UE cm = (x, z, y) * 100; directions use the same swizzle without the scale.
Records are sorted by category, then by 32 m XY cell."""
import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NIGHT = Path(os.environ.get('SM2_NIGHT_JSON', Path.home() / 'sm2-n1/_scratch/night/export/night_lights.json'))
OUT = ROOT / 'unreal/WebHomage/Content/Night'
PINNED = '64d957f92f005a1c1870070079351e30b2395661'
CATS = ['street_lamp', 'park_lamp', 'bridge_lamp', 'shop_front', 'neon', 'screen', 'skyline_flood',
        'window_run', 'window_band', 'board_whole', 'board_tile', 'blade', 'signal']
CAT = {n: i for i, n in enumerate(CATS)}
TYPE = {'point': 0, 'spot': 1, 'rect': 2}
CELL_CM = 3200.0
SIGNAL_STATE = 0   # props.js provider: colour = SIG_COL[it.extra?.aState ?? 0]; the run-time phase is not simulated, so state 0 (red) is baked


def fail(msg):
    raise SystemExit('prep_night: ' + msg)


def sw(v, scale=1.0):
    return (v[0] * scale, v[2] * scale, v[1] * scale)


def make(cat, typ, pos, d, u, premult, rng, w, h, cos_o, cos_i, radius, spec, day, no_shadow, vol):
    m = max(premult)
    if not m > 0:
        return None
    col = tuple(c / m for c in premult)
    flags = (1 if day else 0) | (2 if no_shadow else 0)
    p = sw(pos, 100.0)
    return {'key': (cat, math.floor(p[0] / CELL_CM), math.floor(p[1] / CELL_CM)),
            'a': (*p, *sw(d), *sw(u), *col, m, rng * 100.0, w * 100.0, h * 100.0),
            'u8': (cat, typ, flags, max(0, min(255, round(vol * 255)))),
            'b': (cos_o, cos_i, radius * 100.0, spec)}


def r3(v):
    return round(v, 3)


def geometry(d):
    """Emissive geometry data for build_look.py 'night' (Content/Night/NightGeometry.json): flat per-instance float lists in UE cm.
    Radiances are the browser's pre-exposure values (the build multiplies by K * EmissiveK)."""
    SK = d['screen_k']
    NE = d['neon']['constants']['NEON']
    up = (0.0, 0.0, 1.0)
    out = {'version': 1, 'commit': d['source']['commit'], 'params': {
        'screen_k': SK, 'neon_gain': NE['gain'], 'neon_word': NE['word'], 'neon_glow': NE['glow'], 'neon_led': NE['led'],
        'word_gain': NE['gain'] * NE['word'] * SK, 'board_gain': SK * d['constants']['SL_screen_shading'][0]['value']['uScrBoost'],
        'knee': d['constants']['SL_screen_shading'][1]['value']['uScrKnee'], 'top': d['constants']['SL_screen_shading'][1]['value']['uScrTop']}}
    # ---- neon tubes -> one cylinder per masked side (neon.js tubeMaterial vertex code: sides 0 bottom, 1 right, 2 top, 3 left; ends run R past the corners)
    T = d['neon']['tubes']; assert T['stride'] == 17
    tub = []
    for i in range(T['count']):
        o, t, v = T['data'][i * 17:i * 17 + 3], T['data'][i * 17 + 3:i * 17 + 6], T['data'][i * 17 + 6:i * 17 + 9]
        w, h, rad, mask = T['data'][i * 17 + 9:i * 17 + 13]
        col, flag = T['data'][i * 17 + 13:i * 17 + 16], T['data'][i * 17 + 16]
        led = flag >= 1.0
        k = NE['gain'] * SK * (NE['led'] * 0.85 if led else 1.0)
        for side in range(4):
            if not (int(mask + 0.5) >> side) & 1:
                continue
            p0 = [(0, 0), (w, 0), (w, h), (0, h)][side]
            dr = [(1, 0), (0, 1), (-1, 0), (0, -1)][side]
            length = w if side in (0, 2) else h
            axis = [t[j] * dr[0] + v[j] * dr[1] for j in range(3)]
            start = [o[j] + t[j] * p0[0] + v[j] * p0[1] for j in range(3)]
            c = [start[j] + axis[j] * length / 2 for j in range(3)]
            R = max(rad, 0.008)
            tub += [r3(x) for x in (*sw(c, 100.0), *sw(axis), (length + 2 * R) * 100.0, R * 100.0, 1.0 if led else 0.0, col[0] * k, col[1] * k, col[2] * k)]
    out['tubes'] = tub
    # ---- neon words / icons: centre, width dir (T), normal, size cm, atlas cell, colour
    W = d['neon']['words']; assert W['stride'] == 12
    wd = []
    for i in range(W['count']):
        cx, cy, cz, tx, tz, w, h, cell, cr, cg, cb, seed = W['data'][i * 12:i * 12 + 12]
        wd += [r3(x) for x in (*sw((cx, cy, cz), 100.0), *sw((tx, 0, tz)), *sw((-tz, 0, tx)), w * 100.0, h * 100.0, cell, cr, cg, cb)]
    out['words'] = wd
    # ---- screen boards: one quad per original panel (screenlights.js 'panels'): atlas uv rect (ts_ads, v up) or flat average colour
    bd = []
    for b in d['boards']['boards']:
        for q in b['whole']['panels']:
            uv = q['uv'] or [0, 0, 1, 1]
            avg = q['avg'] or [0.15, 0.15, 0.15]
            bd += [r3(x) for x in (*sw(q['c'], 100.0), *sw(q['n']), *sw(q['u']), q['w'] * 100.0, q['h'] * 100.0, *uv, 1.0 if q['uv'] else 0.0, *avg, 1.0 if q['printed'] else 0.0)]
    out['boards'] = bd
    # ---- blade-sign faces (props.js bladeFaces): two faces per blade, text runs up the face, atlas ts_signs (4 x 16 cells)
    bl = []
    Y0, Y1, Z0, Z1, TH = 3.35, 5.25, 0.25, 1.15, 0.07
    for b in d['blades']:
        if b['hidden']:
            continue
        sn, cs = math.sin(b['ry']), math.cos(b['ry'])
        c = b['cell']
        u0, du = (c % 4) / 4 + 2 / 2048, 0.25 - 4 / 2048
        v0, dv = 1 - (c // 4 + 1) / 16 + 2 / 2048, 1 / 16 - 4 / 2048
        cu, cv, cdu, cdv = u0 + du * 0.05, v0 + dv * 0.03, du * 0.9, dv * 0.94
        for sx in (-1, 1):
            lx, ly, lz = sx * (TH + 0.005), (Y0 + Y1) / 2, (Z0 + Z1) / 2
            pos = (b['x'] + cs * lx + sn * lz, b['y'] + ly, b['z'] - sn * lx + cs * lz)
            wdir = (-sx * sn, 0, -sx * cs)
            nrm = (sx * cs, 0, -sx * sn)
            bl += [r3(x) for x in (*sw(pos, 100.0), *sw(wdir), *sw(nrm), (Z1 - Z0 - 0.14) * 100.0, (Y1 - Y0 - 0.16) * 100.0, cu, cv, cdu, cdv)]
    out['blades'] = bl
    # ---- signal lenses and lamp heads: small emissive solids at the light positions
    sg, lh = [], []
    sig_cols = d['signals'][0]['light']['state_colours_hex'] if d['signals'] else []
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    hexc = sig_cols[SIGNAL_STATE] if sig_cols else 0xff2412
    scol = [lin((hexc >> 16 & 255) / 255), lin((hexc >> 8 & 255) / 255), lin((hexc & 255) / 255)]
    for s in d['signals']:
        if not s['hidden']:
            sg += [r3(x) for x in (*sw(s['light']['pos'], 100.0), *scol)]
    for s in d['statics']:
        if s['cat'] == 'street_lamp':
            m = max(s['color_linear_premult'])
            lh += [r3(x) for x in (*sw(s['pos'], 100.0), *[c / m for c in s['color_linear_premult']])]
    out['signals'] = sg
    out['lamp_heads'] = lh
    out['counts'] = {'tube_segments': len(tub) // 12, 'tube_instances': T['count'], 'words': len(wd) // 15, 'boards': len(bd) // 20,
                     'blade_faces': len(bl) // 15, 'signals': len(sg) // 6, 'lamp_heads': len(lh) // 6}
    return out


def main():
    if not NIGHT.is_file():
        fail(f'missing export {NIGHT} (run: node tools/night/export_night.mjs)')
    raw = NIGHT.read_bytes()
    d = json.loads(raw)
    commit = d.get('source', {}).get('commit')
    if commit != PINNED:
        fail(f'export commit {commit} != pinned {PINNED}')
    recs = []

    def add(r):
        if r:
            recs.append(r)

    for s in d['statics']:
        if s['cat'] not in CAT:
            fail('unknown static category ' + s['cat'])
        t = TYPE[s['type']]
        rect = t == 2
        add(make(CAT[s['cat']], t, s['pos'], s['dir'], s['u'], s['color_linear_premult'], s['range'],
                 s['width'] if rect else 0, s['height'] if rect else 0, s['cosO'], s['cosI'], s['radius'], s['spec'], s['day'], s['noShadow'], s['volume']))
    for f in d['windows']['faces']:
        for b in f['bands']:
            for kind, r in [(CAT['window_band'], b['band']['rect'])] + [(CAT['window_run'], q['rect']) for q in b['runs']]:
                add(make(kind, 2, r['pos'], r['dir'], r['u'], [c * r['intensity'] for c in r['color_linear']], r['range'], r['width'], r['height'], 1.0, 1.0, r['radius'], 1.0, False, False, 0.0))
    for b in d['boards']['boards']:
        for kind, r in [(CAT['board_whole'], b['whole'])] + [(CAT['board_tile'], q) for q in b['tiles']]:
            add(make(kind, 2, r['pos'], r['dir'], r['u'], r['color_linear_premult'], r['range'], r['width'], r['height'], 1.0, 1.0, r['radius'], 1.0, False, False, r['volume']))
    for s in d['blades']:
        if s['hidden'] or not s['light']['color_linear']:
            continue
        L = s['light']  # props.js blade provider: point, colour 0.35 + 0.65 * board colour, intensity 2.2, range 6, radius 0.5, volume 0.1
        add(make(CAT['blade'], 0, L['pos'], [0, -1, 0], [1, 0, 0], [c * L['intensity'] for c in L['color_linear']], L['range'], 0, 0, 0.62, 0.78, L['radius'], 1.0, False, False, L['volume']))
    sig_cols = d['signals'][0]['light']['state_colours_hex'] if d['signals'] else []
    for s in d['signals']:
        if s['hidden']:
            continue
        L = s['light']
        hexc = sig_cols[SIGNAL_STATE]
        lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        col = [lin((hexc >> 16 & 255) / 255), lin((hexc >> 8 & 255) / 255), lin((hexc & 255) / 255)]
        n = math.sqrt(sum(x * x for x in L['dir']))
        add(make(CAT['signal'], 1, L['pos'], [x / n for x in L['dir']], [1, 0, 0], [c * L['intensity'] for c in col], L['range'], 0, 0,
                 math.cos(L['angle']), math.cos(L['angle'] * (1 - L['penumbra'])), L['radius'], 1.0, False, True, L['volume']))
    recs.sort(key=lambda r: r['key'])
    n = len(recs)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / 'CityLights.bin', 'wb') as f:
        f.write(struct.pack('<4sII40s', b'SM2L', 1, n, commit.encode('ascii')))
        for r in recs:
            f.write(struct.pack('<16f4B', *r['a'], *r['u8']))
        for r in recs:
            f.write(struct.pack('<4f', *r['b']))
    counts = {c: 0 for c in CATS}
    lo, hi = [1e18] * 3, [-1e18] * 3
    for r in recs:
        counts[CATS[r['u8'][0]]] += 1
        for k in range(3):
            lo[k], hi[k] = min(lo[k], r['a'][k]), max(hi[k], r['a'][k])
    geo = geometry(d)
    (OUT / 'NightGeometry.json').write_text(json.dumps(geo, separators=(',', ':')))
    meta = {'version': 1, 'geometry_counts': geo['counts'], 'count': n, 'commit': commit, 'source_json': str(NIGHT), 'source_sha256': hashlib.sha256(raw).hexdigest(), 'categories': CATS,
            'counts': counts, 'bbox_ue_cm': {'min': lo, 'max': hi}, 'strides': {'block_a': 68, 'block_b': 16, 'header': 52},
            'signal_state_baked': SIGNAL_STATE, 'bin_bytes': 52 + n * 84}
    (OUT / 'CityLights.meta.json').write_text(json.dumps(meta, indent=1))
    print(json.dumps({'records': n, 'counts': counts, 'bytes': meta['bin_bytes']}))


if __name__ == '__main__':
    main()
