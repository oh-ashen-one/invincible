#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A), PLAN-firstpass §5 Nanite spike, decision INPUT only (no perf numbers: perf is an exclusive later run).

The facade / roof meshes are non-Nanite because they carry 8 / 5 full-precision UV data channels (export_city.mjs packing). Nanite keeps at
most 4 UV sets (quantised). The question this script answers from the export alone: how much of that per-vertex data is really per-vertex?
If the data rows (every channel except UV0) collapse to a few thousand distinct rows per tile, they fit a small per-tile data texture
addressed by ONE row-index channel, leaving UV0 + index = 2 channels -> Nanite-eligible.

    python3 tools/export/nanite_spike.py <export_dir> [out.json]
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glbio import read_glb


def rows_of(g, skip_uv0=True):
    A = g['attrs']; cols = []
    for k in sorted(A):
        if k in ('POSITION', 'NORMAL') or (skip_uv0 and k == 'TEXCOORD_0'): continue
        cols.append(np.asarray(A[k], np.float32).reshape(len(A['POSITION']), -1))
    return np.concatenate(cols, axis=1) if cols else np.zeros((len(A['POSITION']), 0), np.float32)


def main():
    E = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(E, 'nanite_spike.json')
    M = json.load(open(os.path.join(E, 'manifest.json')))
    res = {}
    for kind in ('facade', 'roofs'):
        per = []
        for r in M['meshes']:
            if r['kind'] != kind or r.get('lod') or r['name'].startswith('facadeLod'): continue
            g = read_glb(os.path.join(E, r['file']))
            R = rows_of(g)
            # quantise like a texture would store it (fp16) before counting distinct rows
            Q = np.ascontiguousarray(R.astype(np.float16)).view(np.uint8).reshape(len(R), -1)
            uniq = len(np.unique(Q, axis=0)) if len(Q) else 0
            per.append({'file': r['file'], 'verts': int(len(R)), 'tris': int(len(g['index']) // 3), 'data_floats_per_vertex': int(R.shape[1]),
                        'distinct_rows': int(uniq), 'channels': r.get('uv')})
        if not per: continue
        v = np.array([p['verts'] for p in per]); u = np.array([p['distinct_rows'] for p in per]); f = per[0]['data_floats_per_vertex']
        res[kind] = {'tiles': len(per), 'verts_total': int(v.sum()), 'tris_total': int(sum(p['tris'] for p in per)), 'data_floats_per_vertex': f,
                     'distinct_rows_total': int(u.sum()), 'distinct_rows_max_tile': int(u.max()), 'rows_per_vertex': round(float(u.sum() / max(v.sum(), 1)), 4),
                     # one RGBA16F texel holds 4 floats -> texels per row = ceil(f / 4); a tile's table = rows x texels
                     'texels_per_row_rgba16f': int(np.ceil(f / 4)),
                     'table_texels_max_tile': int(u.max() * np.ceil(f / 4)),
                     'per_vertex_bytes_now': f * 4, 'per_vertex_bytes_indexed': 4,
                     'vertex_data_mb_now': round(float(v.sum() * f * 4 / 1e6), 1),
                     'table_mb_indexed': round(float(u.sum() * np.ceil(f / 4) * 8 / 1e6), 2),
                     'channels_example': per[0]['channels'], 'per_tile': per}
    json.dump(res, open(out, 'w'), indent=1)
    for k, v in res.items():
        print(k, {kk: vv for kk, vv in v.items() if kk not in ('per_tile', 'channels_example')})


if __name__ == '__main__':
    main()
