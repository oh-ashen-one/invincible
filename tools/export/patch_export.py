#!/usr/bin/env python3
"""Post-export clean-up of the exported browser-city meshes for the Unreal port (runs in tools/export/build_city.sh after the export).

Round 04: the Times Square billboard housings (tsFrames) are closed, vertex-colour-black boxes that hover above the plazas. One of them
sits directly over the S5 camera and rendered as an untextured black mass in the top-right of the frame (critic r03). Rule: a dark hovering
housing component of tsFrames (mean luminance < 0.03, bounding-box volume > 300 m3, underside above 8 m) that comes within CLEAR (25) m of any
SHOTLIST camera is removed from the mesh (triangles dropped from the index buffer). Idempotent: a second run finds nothing to remove.

usage: patch_export.py [export_dir]      (default _scratch/city/export/midtown3x3)
"""
import glob, json, os, struct, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from citypaths import EXPORT as _EXPORT
EXPORT = sys.argv[1] if len(sys.argv) > 1 else _EXPORT
SHOTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../unreal/WebHomage/Scripts/city_shots.json')))
CLEAR = 25.0

def read_glb(path):
    b = open(path, 'rb').read()
    (jl,) = struct.unpack('<I', b[12:16]); js = json.loads(b[20:20 + jl])
    off = 20 + jl; (bl,) = struct.unpack('<I', b[off:off + 4]); bin_ = bytearray(b[off + 8:off + 8 + bl])
    return js, bin_

def write_glb(path, js, bin_):
    j = json.dumps(js, separators=(',', ':')).encode()
    j += b' ' * ((4 - len(j) % 4) % 4)
    bn = bytes(bin_) + b'\0' * ((4 - len(bin_) % 4) % 4)
    out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(j) + 8 + len(bn)) + struct.pack('<I4s', len(j), b'JSON') + j + struct.pack('<I4s', len(bn), b'BIN\0') + bn
    open(path, 'wb').write(out)

def accessor(js, bin_, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a['componentType']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(bin_, dtype=dt, count=a['count'] * n, offset=off).reshape(-1, n), off, dt

def components(pos, tri):
    q = np.round(pos * 50).astype(np.int64)
    keys = {}; vid = np.zeros(len(pos), int)
    for i, k in enumerate(map(tuple, q)): vid[i] = keys.setdefault(k, len(keys))
    par = list(range(len(keys)))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b, c in tri:
        ra, rb, rc = find(vid[a]), find(vid[b]), find(vid[c]); par[rb] = ra; par[find(rc)] = ra
    return np.array([find(vid[t[0]]) for t in tri])

man = json.load(open(os.path.join(EXPORT, 'manifest.json')))
removed_total = 0
for r in man['meshes']:
    if not r['name'].startswith('tsFrames'): continue
    path = os.path.join(EXPORT, r['file'])
    js, bin_ = read_glb(path)
    pr = js['meshes'][0]['primitives'][0]
    pos = accessor(js, bin_, pr['attributes']['POSITION'])[0].astype(np.float64)
    col = accessor(js, bin_, pr['attributes']['COLOR_0'])[0].astype(np.float64)
    idx, ioff, idt = accessor(js, bin_, pr['indices'])
    tri = idx.reshape(-1, 3)
    cams = np.array([[s['pos'][0] - r['center'][0], s['pos'][1], s['pos'][2] - r['center'][2]] for s in SHOTS])  # camera in tile-local coordinates
    comp = components(pos, tri)
    drop = np.zeros(len(tri), bool)
    for cid in np.unique(comp):
        sel = comp == cid
        if sel.sum() < 100: continue
        P = pos[tri[sel]].reshape(-1, 3); lo, hi = P.min(0), P.max(0); d = hi - lo
        C = col[tri[sel]].reshape(-1, col.shape[1])[:, :3].mean(0); lum = 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2]
        if lum > 0.03 or d[0] * d[1] * d[2] < 300 or lo[1] < 8: continue
        gap = np.maximum(np.maximum(lo - cams, cams - hi), 0.0); dist = np.sqrt((gap ** 2).sum(1)).min()
        if dist < CLEAR:
            drop |= sel; print(f'{r["file"]}: drop housing {int(sel.sum())} tris, size {d.round(1)}, {dist:.1f} m from a shot camera')
    if drop.any():
        keep = tri[~drop].reshape(-1).astype(idt)
        bin_[ioff:ioff + keep.nbytes] = keep.tobytes()
        js['accessors'][pr['indices']]['count'] = int(len(keep))
        write_glb(path, js, bin_); removed_total += int(drop.sum())
print('tris removed:', removed_total)
