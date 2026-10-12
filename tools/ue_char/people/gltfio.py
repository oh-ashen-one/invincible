"""Minimal glTF I/O for the people pipeline (numpy). Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.

read_person(): one static mesh (positions, normals, uv, tris, base-colour image) from a Tripo GLB, node transform applied.
write_static_glb(): the same arrays back into a single-primitive GLB tools/skinfit/skinfit.py can consume (PNG base colour).
"""
import io, json, struct, sys, os
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'skinfit'))
import skinfit  # noqa: E402  (read_glb, accessor, trs, image_bytes)

Image.MAX_IMAGE_PIXELS = None


def read_person(path):
    j, b = skinfit.read_glb(path)
    node = next(n for n in j['nodes'] if 'mesh' in n)
    p = j['meshes'][node['mesh']]['primitives'][0]
    P = skinfit.accessor(j, b, p['attributes']['POSITION'])
    N = skinfit.accessor(j, b, p['attributes']['NORMAL'])
    UV = skinfit.accessor(j, b, p['attributes']['TEXCOORD_0'])
    F = skinfit.accessor(j, b, p['indices']).reshape(-1, 3).astype(np.int64)
    M = skinfit.trs(node)
    P = P @ M[:3, :3].T + M[:3, 3]
    N = N @ M[:3, :3].T
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    mat = j['materials'][p['material']]
    ti = mat['pbrMetallicRoughness']['baseColorTexture']['index']
    img = j['images'][j['textures'][ti]['source']]
    im = Image.open(io.BytesIO(skinfit.image_bytes(j, b, img))).convert('RGB')
    return P, N, UV, F, im


def write_static_glb(path, P, N, UV, F, im, name='Person'):
    buf = bytearray()
    views, accs = [], []

    def view(raw, target=None):
        while len(buf) % 4:
            buf.append(0)
        v = {'buffer': 0, 'byteOffset': len(buf), 'byteLength': len(raw)}
        if target:
            v['target'] = target
        buf.extend(raw)
        views.append(v)
        return len(views) - 1

    def acc(arr, ctype, typ, target=None, minmax=False):
        raw = np.ascontiguousarray(arr).tobytes()
        a = {'bufferView': view(raw, target), 'componentType': ctype, 'count': int(arr.shape[0]), 'type': typ}
        if minmax:
            a['min'] = [float(v) for v in arr.min(0)]
            a['max'] = [float(v) for v in arr.max(0)]
        accs.append(a)
        return len(accs) - 1

    prim = {'attributes': {'POSITION': acc(P.astype(np.float32), 5126, 'VEC3', 34962, True),
                           'NORMAL': acc(N.astype(np.float32), 5126, 'VEC3', 34962),
                           'TEXCOORD_0': acc(UV.astype(np.float32), 5126, 'VEC2', 34962)},
            'indices': acc(F.reshape(-1).astype(np.uint32), 5125, 'SCALAR', 34963), 'material': 0}
    bio = io.BytesIO()
    im.save(bio, 'PNG')
    imv = view(bio.getvalue())
    j = {'asset': {'version': '2.0', 'generator': 'people pipeline'},
         'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'name': name, 'mesh': 0}],
         'meshes': [{'name': name, 'primitives': [prim]}],
         'materials': [{'name': name, 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0.0, 'roughnessFactor': 0.8}}],
         'textures': [{'source': 0}], 'images': [{'mimeType': 'image/png', 'bufferView': imv}],
         'bufferViews': views, 'accessors': accs}
    while len(buf) % 4:
        buf.append(0)
    j['buffers'] = [{'byteLength': len(buf)}]
    js = json.dumps(j, separators=(',', ':')).encode()
    while len(js) % 4:
        js += b' '
    total = 12 + 8 + len(js) + 8 + len(buf)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A))
        f.write(js)
        f.write(struct.pack('<II', len(buf), 0x004E4942))
        f.write(bytes(buf))
