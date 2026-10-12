#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Extracts the Times-Square-like LED screen quads (mesh 'tsScreens*', area >= MIN_AREA m2) from the city export into
unreal/WebHomage/Scripts/look_ts_screens.json: centre (browser metres, x east / y up / z south), unit normal, area. Only geometry is read
(no ad textures, no names): build_look.py places a coloured light in front of each screen at night, because the screens' own ad content is
excluded from the Unreal port (docs/night1/city/IP_EXCLUSIONS.md).
usage: extract_ts_screens.py [export dir = /Users/midir/sm2-n1/_scratch/look/export/midtown3x3] [--min-area 25]"""
import json, struct, sys, os
import numpy as np

def glb_prims(path):
    f = open(path, 'rb').read()
    n = struct.unpack('<I', f[12:16])[0]; j = json.loads(f[20:20 + n]); off = 20 + n
    bl = struct.unpack('<I', f[off:off + 4])[0]; bin_ = f[off + 8:off + 8 + bl]
    for m in j['meshes']:
        for p in m['primitives']:
            at = {}
            for k, a in p['attributes'].items():
                acc = j['accessors'][a]; bv = j['bufferViews'][acc['bufferView']]
                ct = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[acc['componentType']]
                nc = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[acc['type']]
                at[k] = np.frombuffer(bin_, dtype=ct, count=acc['count'] * nc, offset=bv.get('byteOffset', 0) + acc.get('byteOffset', 0)).reshape(-1, nc)
            yield at

def main():
    export = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(os.environ.get('SM2_LOOK_SCRATCH', '/Users/midir/sm2-n1/_scratch/look'), 'export', 'midtown3x3'))
    min_area = float(sys.argv[sys.argv.index('--min-area') + 1]) if '--min-area' in sys.argv else 25.0
    man = json.load(open(os.path.join(export, 'manifest.json')))
    out = []
    for r in man['meshes']:
        if r['name'] != 'tsScreens': continue
        cx, _, cz = r['center']
        for at in glb_prims(os.path.join(export, r['file'])):
            P, N = at['POSITION'], at['NORMAL']
            nq = len(P) // 4
            q = P[:nq * 4].reshape(nq, 4, 3)
            cen = q.mean(1) + np.array([cx, 0.0, cz]); e1 = q[:, 1] - q[:, 0]; e2 = q[:, 3] - q[:, 0]
            area = np.linalg.norm(np.cross(e1, e2), axis=1)
            for i in np.where(area >= min_area)[0]:
                n = N[i * 4]; n = n / max(np.linalg.norm(n), 1e-6)
                # (round 03) edge lengths: h = the edge with the larger vertical component, w = the other (used by the emissive stand-in content quads)
                a1, a2 = e1[i], e2[i]
                hv, wv = (a1, a2) if abs(a1[1]) >= abs(a2[1]) else (a2, a1)
                out.append({'c': [round(float(v), 2) for v in cen[i]], 'n': [round(float(v), 3) for v in n], 'a': round(float(area[i]), 1),
                            'w': round(float(np.linalg.norm(wv)), 2), 'h': round(float(np.linalg.norm(hv)), 2)})
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'unreal', 'WebHomage', 'Scripts', 'look_ts_screens.json')
    json.dump({'_comment': 'LED screen quads of the Times-Square-like district (geometry only), from tools/perf_ue/extract_ts_screens.py', 'screens': out}, open(dst, 'w'))
    print(len(out), 'screens ->', os.path.normpath(dst))

if __name__ == '__main__':
    main()
