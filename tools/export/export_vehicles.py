#!/usr/bin/env python3
"""Vehicle prototypes for the Unreal port (round 08): parked cars and taxis along the avenue curbs.

Source: public/assets/city/vehicles.glb, the browser game's own Blender-built car models (tools/blender/city_vehicles.py; 13 models x 3 LODs, model frame
+x forward, y up, wheels on y = 0, TEXCOORD_1.x = material part id, COLOR_0 = baked ambient occlusion). Only LOD0 of a chosen set of models is exported.
The browser paints the models through the atlas vehicles_atlas2.webp; that atlas carries real-game / Marvel-universe liveries (Daily Bugle, Roxxon, Oscorp,
'Wolf & Sheep', taxi toppers, van and bus liveries ...) and is NOT used by the Unreal port (docs/night1/city/IP_EXCLUSIONS.md): the exported UVs are zeroed,
every part gets a plain colour instead, and paint takes the per-instance tint (M_CityProp part 1) like the browser's traffic.
Vertex colour (COLOR_0, linear) = part colour x mix(1, ao, 0.55) (the browser's AO weighting); TEXCOORD_1 = (part, 0) so M_CityProp / partmat.js roughness, metal,
glass, lights and emission apply unchanged.
Writes <export>/proto/veh_<name>.glb and appends one record per model to manifest.json 'protos' (idempotent; build_city.py reads them like every other proto)
plus <export>/vehicles.json {name: {len, wid, hh, taxi}} for street_cars.py.
usage: export_vehicles.py [export_dir]
"""
import json, os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glbio import write_glb
from citypaths import EXPORT as _EXPORT, REPO
EXP = (sys.argv[1] if len(sys.argv) > 1 else _EXPORT).rstrip('/') + '/'
SRC = os.path.join(REPO, 'public', 'assets', 'city', 'vehicles.glb')
# models exported: 4 sedan / hatch bodies, 3 SUV bodies, a pickup, a van, and the 4 taxi bodies (yellow, no topper decals)
MODELS = ['sedan', 'sedan2', 'hatch', 'suv', 'suv2', 'cross', 'pickup', 'van', 'taxi', 'taxi_hy', 'taxi_mv', 'taxi_gr']
# linear colour per material part (vehicles_atlas2 cell means, converted to linear; paint (1) stays white: the instance tint multiplies it)
PCOL = {0: (0.42, 0.42, 0.40), 1: (1.0, 1.0, 1.0), 2: (0.36, 0.37, 0.38), 3: (0.02, 0.02, 0.02), 4: (0.6, 0.55, 0.4), 5: (0.008, 0.008, 0.008), 6: (0.006, 0.006, 0.006),
        7: (0.10, 0.10, 0.10), 8: (0.42, 0.02, 0.02), 15: (0.55, 0.45, 0.28)}

def read_meshes(path):
    b = open(path, 'rb').read()
    (jl,) = struct.unpack('<I', b[12:16]); js = json.loads(b[20:20 + jl])
    off = 20 + jl; (bl,) = struct.unpack('<I', b[off:off + 4]); binb = b[off + 8:off + 8 + bl]
    DT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}; NN = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    def acc(i):
        a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]; n = NN[a['type']]
        o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        arr = np.frombuffer(binb, dtype=DT[a['componentType']], count=a['count'] * n, offset=o).reshape(-1, n)
        if a.get('normalized'): arr = arr.astype(np.float64) / np.iinfo(DT[a['componentType']]).max
        return arr
    out = {}
    for node in js['nodes']:
        m = js['meshes'][node['mesh']]; p = m['primitives'][0]
        out[node['name']] = {k: acc(v) for k, v in p['attributes'].items()}
        out[node['name']]['index'] = acc(p['indices']).reshape(-1).astype(np.int64)
    return out

def main():
    meshes = read_meshes(SRC)
    os.makedirs(EXP + 'proto', exist_ok=True)
    man = json.load(open(EXP + 'manifest.json'))
    have = {p['name'] for p in man['protos']}
    meta = {}
    for name in MODELS:
        g = meshes[name]
        P = g['POSITION'].astype(np.float32); N = g['NORMAL'].astype(np.float32)
        part = np.round(g['TEXCOORD_1'][:, 0]).astype(int)
        ao = np.clip(g['COLOR_0'][:, 0], 0, 1) ** (1 / 2.2)            # the browser: ao = pow(COLOR_0.r, 1 / 2.2)
        aoe = np.where(np.isin(part, (2, 5)), ao + (1 - ao) * 0.65, ao)   # wheels sit deep in their wells: softened
        k = 1.0 - 0.55 * (1.0 - aoe)
        col = np.ones((len(P), 4), np.float32)
        for i in range(len(P)): col[i, :3] = np.array(PCOL.get(int(part[i]), (0.4, 0.4, 0.4))) * k[i]
        uv1 = np.stack([part.astype(np.float32), np.zeros(len(P), np.float32)], 1)
        # (r10, critic r09: 'blank plates') part 0 = the two licence-plate quads (front / rear): TEXCOORD_0 = (u, v) across each plate so M_CityCar can draw a generic plate (no real format, no wordmark); everything else keeps zero UVs (no atlas, IP)
        uv0 = np.zeros((len(P), 2), np.float32)
        for sgn in (1.0, -1.0):
            sel = (part == 0) & (np.sign(P[:, 0]) == sgn)
            if sel.any():
                z0, z1, y0, y1 = P[sel, 2].min(), P[sel, 2].max(), P[sel, 1].min(), P[sel, 1].max()
                u = (P[sel, 2] - z0) / max(z1 - z0, 1e-6); v = (P[sel, 1] - y0) / max(y1 - y0, 1e-6)
                uv0[sel] = np.stack([1.0 - u if sgn > 0 else u, v], 1) * 0.98 + 0.01
        attrs = {'POSITION': P, 'NORMAL': N, 'TEXCOORD_0': uv0, 'TEXCOORD_1': uv1, 'COLOR_0': col}
        fn = f'veh_{name}'
        write_glb(EXP + f'proto/{fn}.glb', attrs, g['index'], name=fn)
        mn, mx = P.min(0), P.max(0)
        meta[fn] = {'len': float(mx[0] - mn[0]), 'wid': float(mx[2] - mn[2]), 'hh': float(mx[1]), 'x0': float(mn[0]), 'x1': float(mx[0]), 'taxi': name.startswith('taxi')}
        rec = {'file': f'proto/{fn}.glb', 'name': fn, 'src': fn, 'kind': 'proto', 'tile': [0, 0], 'center': [0, 0, 0],
               'mat': {'type': 'MeshStandardMaterial', 'color': [1, 1, 1], 'roughness': 0.7, 'metalness': 0, 'vertexColors': True, 'map': None, 'alphaTest': 0, 'transparent': False},
               'attrs': ['position', 'normal', 'color', 'uv', 'aPart'], 'verts': int(len(P)), 'tris': int(len(g['index']) // 3), 'uv': ['uv', 'aPart.x'], 'color': True, 'colorNote': None}
        man['protos'] = [p for p in man['protos'] if p['name'] != fn] + [rec]
    json.dump(man, open(EXP + 'manifest.json', 'w'), indent=1)
    json.dump(meta, open(EXP + 'vehicles.json', 'w'), indent=1)
    print('vehicle prototypes:', {k: (round(v['len'], 2), round(v['wid'], 2)) for k, v in meta.items()})

main()
