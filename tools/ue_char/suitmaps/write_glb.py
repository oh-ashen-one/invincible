"""Write the upgraded AI-suit skin GLB + the UE-ready PNG maps.

    python3 tools/ue_char/suitmaps/write_glb.py <suit>

Starts from the ORIGINAL skinfit GLB (git HEAD copy kept in _scratch/.../orig/, so reruns are idempotent) and keeps its
58 joint nodes, names, skin and inverse bind matrices, vertex count/order, UVs and triangles verbatim. Replaced:
POSITION/NORMAL/JOINTS_0/WEIGHTS_0 from geom.npz (seam weld, back-emblem flatten); added: TANGENT (MikkTSpace from
bake_normal.py), normalTexture, metallicRoughness + occlusion (one ORM texture), cleaned basecolor. Textures are
WebP (EXT_texture_webp, as before). Also writes art/night1/characters/suits/<suit>_{basecolor,normal_ogl,orm}.png
(normal is OpenGL/+Y: tick "Flip Green Channel" when importing into UE) and verifies the tangent-space convention by
rebuilding object-space normals from (T, B = cross(N, T) * w, N) and the map, against Cycles' object-space bake.

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import io, os, sys, json, struct, subprocess
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_glb, accessor, SCRATCH, ART, skin_path, orig_skin  # noqa: E402

MAX_TILT = np.radians(28.0)   # tiny / degenerate UV islands bake spikes; clamp them


def clean_normal(path, mask):
    n = cv2.imread(path)[..., ::-1].astype(np.float32) / 255 * 2 - 1
    n[..., 2] = np.maximum(n[..., 2], 1e-3)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    tilt = np.arccos(np.clip(n[..., 2], -1, 1))
    spike = tilt > np.radians(45)
    xy = n[..., :2]; r = np.linalg.norm(xy, axis=-1, keepdims=True) + 1e-9
    s = np.minimum(np.sin(tilt), np.sin(MAX_TILT))[..., None]
    n2 = np.concatenate([xy / r * s, np.cos(np.minimum(tilt, MAX_TILT))[..., None]], -1)
    n2[spike] = (0, 0, 1)                                   # spikes are artefacts, not detail: flat
    n2[~mask] = (0, 0, 1)
    return n2, float(spike[mask].mean()), float((tilt[mask] > MAX_TILT).mean())


def webp(arr_u8, q):
    bio = io.BytesIO(); Image.fromarray(arr_u8).save(bio, 'WEBP', quality=q, method=6); return bio.getvalue()


def verify(nmap, UV, N, T, w, onrm_path, n=4000):
    ob = cv2.imread(onrm_path, cv2.IMREAD_UNCHANGED)[..., ::-1].astype(np.float32) * 2 - 1
    H = nmap.shape[0]
    rng = np.random.default_rng(0); idx = rng.choice(len(UV), n, replace=False)
    px = np.clip((UV[idx] * H).astype(int), 0, H - 1)
    t = nmap[px[:, 1], px[:, 0]]; o = ob[px[:, 1], px[:, 0]]
    o /= np.linalg.norm(o, axis=1, keepdims=True) + 1e-9
    tilt = np.arccos(np.clip(t[:, 2], -1, 1)) > np.radians(4)     # only texels with actual detail
    res = {}
    for name, sgn in (('w', 1.0), ('-w', -1.0)):
        B = np.cross(N[idx], T[idx]) * (w[idx] * sgn)[:, None]
        rec = T[idx] * t[:, :1] + B * t[:, 1:2] + N[idx] * t[:, 2:3]
        rec /= np.linalg.norm(rec, axis=1, keepdims=True)
        ang = np.degrees(np.arccos(np.clip((rec * o).sum(1), -1, 1)))
        res[name] = round(float(np.median(ang[tilt])), 2) if tilt.any() else None
    res['samples_with_detail'] = int(tilt.sum())
    return res


def main():
    suit = sys.argv[1]
    d = os.path.join(SCRATCH, suit)
    j, b = read_glb(orig_skin(suit))
    prim = j['meshes'][0]['primitives'][0]; A = prim['attributes']
    UV = accessor(j, b, A['TEXCOORD_0']); F = accessor(j, b, prim['indices'])
    g = np.load(os.path.join(d, 'geom.npz'))
    tan = np.load(os.path.join(d, 'tangents2.npy'))
    T, w = tan[:, :3].astype(np.float64), tan[:, 3].astype(np.float64)
    N = g['N'].astype(np.float64)
    # re-orthogonalise T against N (Gram-Schmidt), glTF wants unit xyz and w = +-1
    T = T - N * (T * N).sum(1, keepdims=True); T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)

    mask = cv2.imread(os.path.join(d, 'mask.png'), 0) > 127
    nmap, spike_frac, clamp_frac = clean_normal(os.path.join(d, 'normal_ogl.png'), mask)
    ver = verify(nmap, UV, N, T, w, os.path.join(d, 'onrm_bump.exr'))
    print(f'{suit}: normal spikes flattened {spike_frac * 100:.2f}%, clamped {clamp_frac * 100:.2f}%; '
          f'tangent check median error deg {ver}')
    n_u8 = ((nmap * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)
    bc = np.array(Image.open(os.path.join(d, 'bc.png')).convert('RGB'))
    orm = np.array(Image.open(os.path.join(d, 'orm.png')).convert('RGB'))
    os.makedirs(ART, exist_ok=True)
    Image.fromarray(bc).save(os.path.join(ART, f'{suit}_basecolor.png'))
    Image.fromarray(n_u8).save(os.path.join(ART, f'{suit}_normal_ogl.png'))
    Image.fromarray(orm).save(os.path.join(ART, f'{suit}_orm.png'))

    # ---------------- rebuild the binary chunk ----------------
    views = j['bufferViews']; accs = j['accessors']
    out = bytearray()

    def add_view(raw, target=None):
        nonlocal out
        while len(out) % 4: out += b'\0'
        v = {'buffer': 0, 'byteOffset': len(out), 'byteLength': len(raw)}
        if target: v['target'] = target
        out += raw; views_new.append(v); return len(views_new) - 1

    views_new = []
    remap = {}
    replace = {A['POSITION']: g['P'].astype(np.float32), A['NORMAL']: N.astype(np.float32),
               A['JOINTS_0']: g['J'].astype(np.uint8), A['WEIGHTS_0']: g['W'].astype(np.float32)}
    img_views = {im['bufferView'] for im in j['images']}
    for ai, a in enumerate(accs):
        if 'bufferView' not in a: continue
        if ai in replace:
            arr = np.ascontiguousarray(replace[ai])
            a['bufferView'] = add_view(arr.tobytes(), 34962); a.pop('byteOffset', None)
            a['componentType'] = {np.dtype(np.float32): 5126, np.dtype(np.uint8): 5121}[arr.dtype]
            if ai == A['POSITION']:
                a['min'] = [float(v) for v in arr.min(0)]; a['max'] = [float(v) for v in arr.max(0)]
        else:
            vi = a['bufferView']
            if vi not in remap:
                v = views[vi]; o = v.get('byteOffset', 0)
                nv = add_view(b[o:o + v['byteLength']], v.get('target'))
                if 'byteStride' in v: views_new[nv]['byteStride'] = v['byteStride']
                remap[vi] = nv
            a['bufferView'] = remap[vi]
    tang = np.concatenate([T, w[:, None]], 1).astype(np.float32)
    accs.append({'bufferView': add_view(tang.tobytes(), 34962), 'componentType': 5126, 'count': len(tang), 'type': 'VEC4'})
    A['TANGENT'] = len(accs) - 1
    name = j['meshes'][0]['name']
    ims = [('basecolor', webp(bc, 88)), ('normal', webp(n_u8, 90)), ('orm', webp(orm, 88))]
    j['images'] = [{'name': f'{name}_{k}', 'mimeType': 'image/webp', 'bufferView': add_view(raw)} for k, raw in ims]
    j['textures'] = [{'sampler': 0, 'extensions': {'EXT_texture_webp': {'source': i}}} for i in range(3)]
    j['materials'] = [{'name': 'SkinSuit', 'pbrMetallicRoughness': {
        'baseColorTexture': {'index': 0}, 'metallicRoughnessTexture': {'index': 2},
        'metallicFactor': 1.0, 'roughnessFactor': 1.0},
        'normalTexture': {'index': 1, 'scale': 1.0}, 'occlusionTexture': {'index': 2, 'strength': 1.0}}]
    j['bufferViews'] = views_new
    while len(out) % 4: out += b'\0'
    j['buffers'] = [{'byteLength': len(out)}]
    j['asset']['generator'] = 'spider-man-2 tools/skinfit/skinfit.py + tools/ue_char/suitmaps'
    js = json.dumps(j, separators=(',', ':')).encode()
    while len(js) % 4: js += b' '
    dst = skin_path(suit)
    with open(dst, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(out)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(out), 0x004E4942)); f.write(bytes(out))
    info = json.load(open(os.path.join(d, 'maps.json')))
    info.update(tangent_check_deg=ver, normal_spike_frac=spike_frac, glb_bytes=os.path.getsize(dst),
                glb_bytes_before=os.path.getsize(os.path.join(SCRATCH, 'orig', suit + '.glb')),
                texture_bytes={k: len(r) for k, r in ims})
    json.dump(info, open(os.path.join(d, 'maps.json'), 'w'), indent=1)
    print(f'{suit}: wrote {dst} {os.path.getsize(dst) / 1e6:.2f} MB (textures {[round(len(r) / 1e6, 2) for _, r in ims]} MB)')


if __name__ == '__main__':
    main()
