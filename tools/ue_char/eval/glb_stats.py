"""UV / texture stats for GLB assets (system python3: numpy + Pillow). Fan homage, not official Marvel/Sony/Insomniac.

  python3 tools/ue_char/eval/glb_stats.py OUT_JSON GLB [GLB ...]
Per primitive: verts, tris, UV coverage % of 0..1 (rasterised 512^2, all overlapping islands merged), UV islands
(union-find over shared vertices), median texel density px/m for the base-colour texture, texture sizes, and
the share of triangles whose UVs overlap another triangle's UVs (mirrored/stacked islands; sampled).
"""
import json, struct, sys, io
import numpy as np
from PIL import Image, ImageDraw
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(p):
    b = open(p, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20 + n])
    bin_ = b[20 + n + 8:]
    return g, bin_


def acc(g, bin_, i):
    a = g['accessors'][i]
    bv = g['bufferViews'][a['bufferView']]
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    dt = CT[a['componentType']]
    nc = NC[a['type']]
    stride = bv.get('byteStride')
    if stride and stride != np.dtype(dt).itemsize * nc:
        raw = np.frombuffer(bin_, np.uint8, stride * a['count'], o).reshape(a['count'], stride)
        return raw[:, :np.dtype(dt).itemsize * nc].copy().view(dt).reshape(a['count'], nc)
    return np.frombuffer(bin_, dt, a['count'] * nc, o).reshape(a['count'], nc)


def img_size(g, bin_, ti):
    tx = g['textures'][ti]
    src = tx.get('source', tx.get('extensions', {}).get('EXT_texture_webp', {}).get('source'))
    im = g['images'][src]
    if 'bufferView' in im:
        bv = g['bufferViews'][im['bufferView']]
        data = bin_[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
        return list(Image.open(io.BytesIO(data)).size)
    return None


out = {}
for p in sys.argv[2:]:
    g, bin_ = load(p)
    rec = {'prims': []}
    for m in g.get('meshes', []):
        for pr in m['primitives']:
            A = pr['attributes']
            pos = acc(g, bin_, A['POSITION']).astype(float)
            idx = acc(g, bin_, pr['indices']).ravel().astype(int).reshape(-1, 3)
            r = {'mesh': m.get('name'), 'verts': len(pos), 'tris': len(idx), 'attrs': sorted(A)}
            mat = g['materials'][pr['material']] if 'material' in pr else {}
            pb = mat.get('pbrMetallicRoughness', {})
            maps = {}
            for k, t in (('baseColor', pb.get('baseColorTexture')), ('metalRough', pb.get('metallicRoughnessTexture')),
                         ('normal', mat.get('normalTexture')), ('occlusion', mat.get('occlusionTexture')),
                         ('emissive', mat.get('emissiveTexture'))):
                if t:
                    maps[k] = img_size(g, bin_, t['index'])
            r['maps'] = maps
            r['material'] = mat.get('name')
            if 'TEXCOORD_0' in A:
                uv = acc(g, bin_, A['TEXCOORD_0']).astype(float)
                S = 512
                im = Image.new('L', (S, S), 0)
                d = ImageDraw.Draw(im)
                cnt = np.zeros((S, S), np.uint16)
                for t in idx:
                    d.polygon([(float(uv[k, 0] * S), float(uv[k, 1] * S)) for k in t], fill=255)
                r['uv_coverage_pct'] = round(100 * float(np.asarray(im).astype(bool).mean()), 1)
                r['uv_outside_01_pct'] = round(100 * float(((uv < -1e-3) | (uv > 1.001)).any(1).mean()), 2)
                par = np.arange(len(pos))
                def f(x):
                    while par[x] != x:
                        par[x] = par[par[x]]; x = par[x]
                    return x
                for t in idx:
                    a0 = f(t[0]); par[f(t[1])] = a0; par[f(t[2])] = a0
                r['uv_islands'] = len({f(i) for i in np.unique(idx)})
                if 'baseColor' in maps and maps['baseColor']:
                    W = maps['baseColor'][0]
                    a3 = np.linalg.norm(np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]]), axis=1) / 2
                    u = uv * W
                    e1, e2 = u[idx[:, 1]] - u[idx[:, 0]], u[idx[:, 2]] - u[idx[:, 0]]
                    a2 = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) / 2
                    ok = a3 > 1e-10
                    dens = np.sqrt(a2[ok] / a3[ok])
                    r['texel_px_per_m_median'] = round(float(np.median(dens)), 1)
                    r['texel_p10_p90'] = [round(float(np.percentile(dens, 10)), 1), round(float(np.percentile(dens, 90)), 1)]
                    # stretch: ratio of triangle's uv-area/3d-area vs median (log2 spread)
                    rr = np.log2(np.maximum(dens, 1e-3) / np.median(dens))
                    r['texel_ratio_outside_2x_pct'] = round(100 * float((np.abs(rr) > 1).mean()), 1)
            rec['prims'].append(r)
    rec['skin_joints'] = [len(s['joints']) for s in g.get('skins', [])]
    rec['anims'] = len(g.get('animations', []))
    out[p] = rec
    print(p, json.dumps(rec)[:900])
json.dump(out, open(sys.argv[1], 'w'), indent=1)
