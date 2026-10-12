#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F (round 05): ray-tracing proxies of the city trees, one merged mesh per city tile (round-04 critic: the 42 k leaf / crown
instances in the ray-tracing scene cost ~0.6 ms of FrameTime - GPUTime; merge them into <= 1 k ray-tracing instances).

Input : tree_proxy_dump.py json (every tree HISM instance's world matrix, read from the rebuilt level) + the browser export's proto GLBs
        (the same files build_city.py imported; mesh-local frame verified against the imported meshes' bounds) + the leaf textures.
Output: <out>/tiles/RTPack_<n>.glb (glTF, metres; one mesh RTP_<i>_<j> per tile, tile-local, SM2_PERF_PROXY_PACK tiles per file), <out>/tiles.json (tile centre in UE cm, triangle / tree counts), <out>/report.json.
Each tile mesh has two primitives: 'leaf' (leaf cards + crown masses) and 'bark'. perf_apply.py step rt_proxy_trees imports them into
/Game/PerfF/RTProxy, places one actor per tile (ray tracing only: not in the main / depth pass, no shadow, no distance field) and takes the
original tree HISMs out of the ray-tracing scene. Raster, shadows, distance fields of the trees are untouched.

Reduction (a proxy for ray-traced GI / reflection occlusion, never rasterised):
  leaf cards  every k-th card of each tree is kept (k per class: LOD0 street / small trees + hedges SM2_PERF_PROXY_K0 (default 1 = every card), others SM2_PERF_PROXY_K1 (16);
              the phase changes per tree), scaled about its centre by sqrt(k * coverage * SM2_PERF_PROXY_COVER): the expected occluding area
              of the tree stays the leaf texture's alpha coverage (the as-found alpha-masked any-hit), with ONE opaque, cheap card instead of k masked ones
  crown masses (trees_*_crownfar, 100 triangles) kept whole
  bark        the largest triangles of each bark mesh up to SM2_PERF_PROXY_BARK_AREA of its area, at most SM2_PERF_PROXY_BARK_MAX triangles (trunk + main limbs)
usage: tree_proxy_build.py --dump <tree_dump.json> --export <export/midtown3x3> --out <dir> [--tile-m 200]"""
import argparse, json, os, struct, sys, math, time
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..'))
K0 = int(os.environ.get('SM2_PERF_PROXY_K0', '1'))   # round 05: 6 / 4 decimated the near (LOD0) street trees next to the street-level cameras: blotchy canopy GI (S1 crop 0.913 at k 4); 1 keeps every card, shrunk to its coverage
K1 = int(os.environ.get('SM2_PERF_PROXY_K1', '16'))
COVER = float(os.environ.get('SM2_PERF_PROXY_COVER', '3.5'))   # round 05: 1.0 (texture coverage at the near-field clip) left the S1 canopy 1.32x as bright as found; the material's distance boost fills cards beyond 25 m
BARK_AREA = float(os.environ.get('SM2_PERF_PROXY_BARK_AREA', '0.6'))
BARK_MAX = int(os.environ.get('SM2_PERF_PROXY_BARK_MAX', '160'))
PACK = int(os.environ.get('SM2_PERF_PROXY_PACK', '40'))   # tiles per GLB file
LEAF_TEX = {'ash': 'ash.png', 'oak': 'oak.png', 'pine': 'pine.png', 'aspen': 'aspen.png'}


def read_glb(p):
    b = open(p, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20 + n]); binoff = 20 + n + 8; blob = b[binoff:]
    CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
    NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

    def acc(i):
        a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        dt = CT[a['componentType']]; nc = NC[a['type']]
        stride = bv.get('byteStride')
        if stride and stride != nc * np.dtype(dt).itemsize:
            raw = np.frombuffer(blob, dtype=np.uint8, count=stride * a['count'], offset=off).reshape(a['count'], stride)
            return raw[:, :nc * np.dtype(dt).itemsize].copy().view(dt).reshape(a['count'], nc)
        return np.frombuffer(blob, dtype=dt, count=a['count'] * nc, offset=off).reshape(a['count'], nc).copy()
    P, N, UV, I = [], [], [], []
    base = 0
    for m in js['meshes']:
        for pr in m['primitives']:
            at = pr['attributes']
            p = acc(at['POSITION']).astype(np.float64)
            n = acc(at['NORMAL']).astype(np.float64) if 'NORMAL' in at else np.zeros_like(p)
            uv = acc(at['TEXCOORD_0']).astype(np.float64) if 'TEXCOORD_0' in at else np.zeros((len(p), 2))
            idx = acc(pr['indices']).reshape(-1).astype(np.int64) if 'indices' in pr else np.arange(len(p))
            P.append(p); N.append(n); UV.append(uv); I.append(idx + base); base += len(p)
    return np.concatenate(P), np.concatenate(N), np.concatenate(UV), np.concatenate(I).reshape(-1, 3)


# glTF (metres, y up) -> UE mesh-local (cm, z up). Chosen per mesh by the imported mesh's bounds (tree_dump.json), see pick_axes
AXES = {'xzy': (np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], float)),        # UE = (x, z, y)   (swap: det -1)
        'x-zy': (np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)),      # UE = (x, -z, y)
        '-xzy': (np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float))}      # UE = (-x, z, y)


def pick_axes(P, origin, extent):
    best = None
    for k, A in AXES.items():
        q = P @ A * 100.0
        lo, hi = q.min(0), q.max(0)
        err = np.abs((lo + hi) / 2 - origin).max() + np.abs((hi - lo) / 2 - extent).max()
        if best is None or err < best[1]: best = (k, err)
    return best


def cards(I, nv):
    """triangle -> card id (connected components over shared vertices)"""
    parent = np.arange(nv)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b, c in I:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra; parent[find(rc)] = ra
    roots = np.array([find(v) for v in range(nv)])
    _, cid = np.unique(roots[I[:, 0]], return_inverse=True)
    return cid


_tex = {}


def alpha_of(name):
    if name not in _tex:
        im = Image.open(os.path.join(WT, 'public', 'assets', 'eztree', 'leaves', LEAF_TEX[name])).convert('RGBA')
        _tex[name] = np.asarray(im)[:, :, 3].astype(np.float32) / 255.0
    return _tex[name]


def card_coverage(P, UV, I, cid, texname, thr=0.5):
    """per card: fraction of the card's texels with alpha > thr (the material's near-field clip), sampled on a 12 x 12 grid over its triangles"""
    a = alpha_of(texname); h, w = a.shape
    nc = cid.max() + 1
    cov_sum = np.zeros(nc); cnt = np.zeros(nc)
    g = np.linspace(0.02, 0.98, 12)
    uu, vv = np.meshgrid(g, g); m = (uu + vv) <= 1.0; uu, vv = uu[m], vv[m]
    t0, t1, t2 = UV[I[:, 0]], UV[I[:, 1]], UV[I[:, 2]]
    for s, t in zip(uu, vv):
        uv = t0 + (t1 - t0) * s + (t2 - t0) * t
        x = np.clip((uv[:, 0] % 1.0) * (w - 1), 0, w - 1).astype(int); y = np.clip((uv[:, 1] % 1.0) * (h - 1), 0, h - 1).astype(int)
        np.add.at(cov_sum, cid, (a[y, x] > thr).astype(float)); np.add.at(cnt, cid, 1.0)
    return cov_sum / np.maximum(cnt, 1)


def tri_area(P, I):
    return 0.5 * np.linalg.norm(np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]), axis=1)


def write_glb(path, meshes):
    """meshes: list of (mesh name, prims); prims: list of (material name, P (n,3) metres glTF frame, N (n,3), I (m,3)). One node + one mesh per entry
    (Interchange makes one static mesh per glTF mesh: several tiles per file = far fewer import tasks), shared materials 'leaf' / 'bark'."""
    bufs, views, accs, mats, jmeshes, nodes = [], [], [], [], [], []
    off = 0
    matidx = {}

    def add(arr, target, typ, ct, minmax=False):
        nonlocal off
        raw = arr.tobytes(); pad = (-len(raw)) % 4
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(raw), 'target': target})
        bufs.append(raw + b'\0' * pad); off += len(raw) + pad
        a = {'bufferView': len(views) - 1, 'componentType': ct, 'count': int(arr.shape[0]), 'type': typ}
        if minmax: a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        accs.append(a); return len(accs) - 1
    for mname, prims in meshes:
        mprims = []
        for name, P, N, I in prims:
            if len(I) == 0: continue
            pa = add(P.astype(np.float32), 34962, 'VEC3', 5126, True)
            na = add(N.astype(np.float32), 34962, 'VEC3', 5126)
            ua = add(np.zeros((len(P), 2), np.float32), 34962, 'VEC2', 5126)
            ia = add(I.astype(np.uint32).reshape(-1), 34963, 'SCALAR', 5125)
            if name not in matidx: matidx[name] = len(mats); mats.append({'name': name, 'doubleSided': True})
            mprims.append({'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua}, 'indices': ia, 'material': matidx[name]})
        nodes.append({'mesh': len(jmeshes), 'name': mname}); jmeshes.append({'name': mname, 'primitives': mprims})
    js = {'asset': {'version': '2.0', 'generator': 'sm2 perf tree_proxy_build'}, 'scene': 0, 'scenes': [{'nodes': list(range(len(nodes)))}], 'nodes': nodes,
          'meshes': jmeshes, 'materials': mats, 'buffers': [{'byteLength': off}], 'bufferViews': views, 'accessors': accs}
    jb = json.dumps(js, separators=(',', ':')).encode(); jb += b' ' * ((-len(jb)) % 4)
    bb = b''.join(bufs)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(bb)))
        f.write(struct.pack('<II', len(jb), 0x4E4F534A)); f.write(jb)
        f.write(struct.pack('<II', len(bb), 0x004E4942)); f.write(bb)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dump', required=True); ap.add_argument('--export', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--tile-m', type=float, default=float(os.environ.get('SM2_PERF_PROXY_TILE_M', '200')))
    a = ap.parse_args()
    t0 = time.time()
    D = json.load(open(a.dump))
    man = json.load(open(os.path.join(a.export, 'manifest.json')))
    protos = {p['name']: p for p in man['protos']}
    os.makedirs(os.path.join(a.out, 'tiles'), exist_ok=True)
    for f in os.listdir(os.path.join(a.out, 'tiles')):
        if f.endswith('.glb'): os.remove(os.path.join(a.out, 'tiles', f))
    T = a.tile_m * 100.0
    tiles = {}   # (i, j) -> {'leaf': [(P, N, I)], 'bark': [...], 'trees': n}
    rep = {'k0': K0, 'k1': K1, 'cover': COVER, 'bark_area': BARK_AREA, 'bark_max': BARK_MAX, 'tile_m': a.tile_m, 'meshes': {}}
    for comp in D['components']:
        mname = comp['mesh_name'][3:] if comp['mesh_name'].startswith('SM_') else comp['mesh_name']
        base = mname.rsplit('_v', 1)[0] if ('_v' in mname and mname.rsplit('_v', 1)[1].isdigit()) else mname
        pr = protos.get(base)
        if not pr: print('no proto for', comp['mesh_name']); continue
        P, N, UV, I = read_glb(os.path.join(a.export, pr['file']))
        ax, err = pick_axes(P, np.array(comp['bounds_origin']), np.array(comp['bounds_extent']))
        A = AXES[ax]; PL = P @ A * 100.0; NL = N @ A
        kind = 'bark' if base.endswith('_bark') else ('crown' if 'crown' in base else 'leaf')
        info = {'axes': ax, 'bounds_err_cm': round(float(err), 2), 'instances': len(comp['instances']), 'src_tris': int(len(I)), 'kind': kind}
        if kind == 'leaf':
            cid = cards(I, len(P)); nc = int(cid.max()) + 1
            tex = os.path.basename(((pr.get('mat') or {}).get('map') or 'ash.png')).rsplit('.', 1)[0]
            cov = card_coverage(P, UV, I, cid, tex if tex in LEAF_TEX else 'ash')
            k = K0 if ('_l0_' in base or base.startswith('ez_hedge')) else K1
            # card centres (mesh-local, cm) for the scaling
            csum = np.zeros((nc, 3)); ccnt = np.zeros(nc)
            vid = np.unique(I.reshape(-1)); vcard = np.zeros(len(P), int); vcard[I[:, 0]] = cid; vcard[I[:, 1]] = cid; vcard[I[:, 2]] = cid
            np.add.at(csum, vcard[vid], PL[vid]); np.add.at(ccnt, vcard[vid], 1)
            cc = csum / np.maximum(ccnt, 1)[:, None]
            f = np.sqrt(np.clip(k * cov * COVER, 0.0, 64.0))
            info.update({'cards': nc, 'k': k, 'texture': tex, 'coverage_mean': round(float(cov.mean()), 3), 'scale_mean': round(float(f.mean()), 3)})
            phases = []
            for ph in range(k):
                keep = np.where(cid % k == ph)[0]
                kc = np.unique(cid[keep]); keep_v = np.unique(I[keep].reshape(-1))
                remap = -np.ones(len(P), int); remap[keep_v] = np.arange(len(keep_v))
                Pk = cc[vcard[keep_v]] + (PL[keep_v] - cc[vcard[keep_v]]) * f[vcard[keep_v]][:, None]
                phases.append((Pk, NL[keep_v], remap[I[keep]]))
            info['proxy_tris_per_tree'] = int(np.mean([len(x[2]) for x in phases]))
        elif kind == 'crown':
            phases = [(PL, NL, I)]; info['proxy_tris_per_tree'] = int(len(I))
        else:
            ar = tri_area(PL, I); order = np.argsort(-ar); cum = np.cumsum(ar[order]) / max(ar.sum(), 1e-9)
            n = int(min(BARK_MAX, np.searchsorted(cum, BARK_AREA) + 1)); sel = order[:n]
            keep_v = np.unique(I[sel].reshape(-1)); remap = -np.ones(len(P), int); remap[keep_v] = np.arange(len(keep_v))
            phases = [(PL[keep_v], NL[keep_v], remap[I[sel]])]
            info.update({'proxy_tris_per_tree': n, 'bark_area_kept': round(float(cum[n - 1]), 3)})
        rep['meshes'][base] = info
        grp = 'bark' if kind == 'bark' else 'leaf'
        for ii, m in enumerate(comp['instances']):
            M = np.array(m, float).reshape(4, 4)   # row-vector convention: world = [p, 1] @ M
            wpos = M[3, :3]
            key = (int(math.floor(wpos[0] / T)), int(math.floor(wpos[1] / T)))
            Pk, Nk, Ik = phases[ii % len(phases)]
            W = Pk @ M[:3, :3] + M[3, :3]
            R = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=1, keepdims=True)
            Wn = Nk @ R
            if np.linalg.det(M[:3, :3]) < 0: Ik = Ik[:, ::-1]
            t = tiles.setdefault(key, {'leaf': [], 'bark': [], 'trees': 0})
            t[grp].append((W, Wn, Ik))
            if grp == 'leaf' and kind != 'crown' or kind == 'crown': t['trees'] += 1
    inv = AXES['xzy'].T   # UE world (cm) -> glTF (m): the importer maps glTF back with the same axes the protos used (checked: every proto picked 'xzy')
    out_tiles = []
    pack, npack = [], 0
    for (i, j), t in sorted(tiles.items()):
        cx, cy = (i + 0.5) * T, (j + 0.5) * T
        prims = []
        ntri = {}
        for grp in ('leaf', 'bark'):
            if not t[grp]: continue
            Ps, Ns, Is, b = [], [], [], 0
            for W, Wn, Ik in t[grp]:
                Ps.append(W); Ns.append(Wn); Is.append(Ik + b); b += len(W)
            Pw = np.concatenate(Ps); Pw[:, 0] -= cx; Pw[:, 1] -= cy
            prims.append((grp, (Pw @ inv) / 100.0, np.concatenate(Ns) @ inv, np.concatenate(Is)))
            ntri[grp] = int(sum(len(x) for x in Is))
        name = ('RTP_%d_%d' % (i, j)).replace('-', 'm')
        pack.append((name, prims))
        out_tiles.append({'name': name, 'center_cm': [cx, cy, 0.0], 'tris': ntri, 'trees': t['trees'], 'file': 'RTPack_%02d' % npack})
        if len(pack) >= PACK:
            write_glb(os.path.join(a.out, 'tiles', 'RTPack_%02d.glb' % npack), pack); pack = []; npack += 1
    if pack: write_glb(os.path.join(a.out, 'tiles', 'RTPack_%02d.glb' % npack), pack)
    rep['tiles'] = len(out_tiles)
    rep['tris_total'] = sum(sum(x['tris'].values()) for x in out_tiles)
    rep['tris_leaf'] = sum(x['tris'].get('leaf', 0) for x in out_tiles); rep['tris_bark'] = sum(x['tris'].get('bark', 0) for x in out_tiles)
    rep['tris_max_tile'] = max(sum(x['tris'].values()) for x in out_tiles)
    rep['src_instances'] = sum(len(c['instances']) for c in D['components'])
    rep['axes_used'] = sorted(set(v['axes'] for v in rep['meshes'].values()))
    rep['secs'] = round(time.time() - t0, 1)
    json.dump(out_tiles, open(os.path.join(a.out, 'tiles.json'), 'w'), indent=0)
    json.dump(rep, open(os.path.join(a.out, 'report.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'meshes'}))
    if rep['axes_used'] != ['xzy']: print('WARNING: protos imported with other axes than xzy:', rep['axes_used']); sys.exit(3)


if __name__ == '__main__':
    main()
