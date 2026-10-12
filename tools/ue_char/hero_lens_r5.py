#!/usr/bin/env python3
"""Round-05 hero lens: give the flat lens discs a convex dome (critic r04: 'the lenses are flat white discs with no specular highlight or
curvature').  Unreal-side only: edits the derived SK_Hero.glb in $P2_SCRATCH/ueimport/ in place (the browser GLB is untouched).
Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.

For each lens (the 'Lens' primitive, split into left / right by x): fit the plane of the disc (PCA), take the outward side (toward +Z, the
character's front), and push every vertex out by  h * (1 - (rho / R)^2)  along the plane normal (rho = distance from the lens centre in the
plane, R = the largest rho; the rim stays where the frame holds it, so no gap opens).  Vertex normals are recomputed from the domed faces.
Positions / normals are rewritten in place in the BIN chunk (same accessors, same counts); the accessor min / max is refreshed.

  python3 tools/ue_char/hero_lens_r5.py SK_Hero.glb [--height 0.007]
"""
import sys, json, struct
import numpy as np


def main(path, height=0.007):
    raw = bytearray(open(path, 'rb').read())
    n = struct.unpack_from('<I', raw, 12)[0]
    g = json.loads(bytes(raw[20:20 + n]))
    boff = 20 + n + 8                                   # start of the BIN data
    body = next(nd for nd in g['nodes'] if nd.get('name') == 'SpiderMan')
    prims = g['meshes'][body['mesh']]['primitives']
    lens = next(p for p in prims if g['materials'][p['material']]['name'] == 'Lens')

    def view(ai):
        a = g['accessors'][ai]; v = g['bufferViews'][a['bufferView']]
        off = boff + v.get('byteOffset', 0) + a.get('byteOffset', 0)
        return a, off, v.get('byteStride', 12)

    def read(ai):
        a, off, st = view(ai)
        return np.array([struct.unpack_from('<3f', raw, off + i * st) for i in range(a['count'])], np.float64)

    def write(ai, arr):
        a, off, st = view(ai)
        for i, r in enumerate(arr): struct.pack_into('<3f', raw, off + i * st, *[float(x) for x in r])
        if 'min' in a and a.get('type') == 'VEC3':
            a['min'] = [float(x) for x in arr.min(0)]; a['max'] = [float(x) for x in arr.max(0)]

    P = read(lens['attributes']['POSITION']); N = read(lens['attributes']['NORMAL'])
    ia = g['accessors'][lens['indices']]; iv = g['bufferViews'][ia['bufferView']]
    ioff = boff + iv.get('byteOffset', 0) + ia.get('byteOffset', 0)
    fmt = {5123: '<H', 5125: '<I', 5121: '<B'}[ia['componentType']]; sz = struct.calcsize(fmt)
    F = np.array([struct.unpack_from(fmt, raw, ioff + i * sz)[0] for i in range(ia['count'])]).reshape(-1, 3)
    out = P.copy(); report = {}
    for side, m in (('L', P[:, 0] > 0), ('R', P[:, 0] <= 0)):
        idx = np.where(m)[0]
        if len(idx) < 4: continue
        c = P[idx].mean(0)
        u, s, vt = np.linalg.svd(P[idx] - c, full_matrices=False)
        nrm = vt[2]
        if nrm[2] < 0: nrm = -nrm                                 # outward = character front (+Z)
        e1 = vt[0]; e2 = np.cross(nrm, e1)
        rel = P[idx] - c
        rho = np.hypot(rel @ e1, rel @ e2)
        Rr = rho.max()
        out[idx] = P[idx] + nrm[None, :] * (height * (1 - (rho / Rr) ** 2))[:, None]
        report[side] = dict(radius_m=round(float(Rr), 4), flatness_m=round(float(s[2] / np.sqrt(len(idx))), 5), normal=[round(float(x), 3) for x in nrm])
    fn = np.cross(out[F[:, 1]] - out[F[:, 0]], out[F[:, 2]] - out[F[:, 0]])
    nn = np.zeros_like(out)
    for k in range(3): np.add.at(nn, F[:, k], fn)
    nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
    flip = (nn * N).sum(1) < 0                                    # keep the original facing
    nn[flip] *= -1
    write(lens['attributes']['POSITION'], out); write(lens['attributes']['NORMAL'], nn)
    js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    new = bytearray(b'glTF' + struct.pack('<II', 2, 20 + len(js) + (len(raw) - 20 - n)) + struct.pack('<I', len(js)) + b'JSON' + js) + raw[20 + n:]
    open(path, 'wb').write(bytes(new))
    print(json.dumps(dict(path=path, height_m=height, lenses=report, verts=len(P))))


if __name__ == '__main__':
    h = float(sys.argv[sys.argv.index('--height') + 1]) if '--height' in sys.argv else 0.007
    main(sys.argv[1], h)
