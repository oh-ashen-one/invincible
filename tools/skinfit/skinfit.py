#!/usr/bin/env python3
"""Fit an unrigged Tripo character mesh onto the game's hero skeleton.

The game hero (public/assets/spiderman.glb) is a 58-joint skin with 79 clips. A Tripo mesh has no rig, a slightly
different A-pose (arm angle) and slightly different proportions. This tool:

  1. POSE-FIT   poses the game's own skinned mesh (bone rotations about world axes + uniform bone scales, mirrored
                L/R) until it overlaps the Tripo mesh (symmetric chamfer distance, scipy Powell);
  2. TRANSFER   copies skin weights from the posed game mesh to every Tripo vertex (k nearest vertices, normal-
                compatible only, inverse-distance), keeps the top 4 joints, then smooths them over the Tripo mesh;
  3. UN-POSE    maps each Tripo vertex back into the rig's bind pose with the exact inverse of linear blend
                skinning, v_rest = (sum_j w_j S_j)^-1 v, so the new mesh sits on the unchanged skeleton;
  4. WRITE      a GLB holding the game's exact joint nodes and inverse bind matrices plus the new mesh and a 4096²
                WebP texture (optionally all 79 clips too, for a standalone test character).

Because the skeleton is byte-for-byte the game's, the runtime can bind the new mesh to the live skeleton and every
existing animation, IK layer and procedural pose works unchanged.

usage: skinfit.py TRIPO.glb OUT.glb [--game public/assets/spiderman.glb] [--with-anims] [--report out.json]
"""
import argparse, io, json, math, struct, sys, time
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from PIL import Image

HEIGHT = None  # filled from the game mesh

# ----------------------------------------------------------------------------------------------------------- glTF io
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'glTF', path
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(d[20:20 + jl])
    bl = struct.unpack('<I', d[20 + jl:24 + jl])[0]
    return j, d[28 + jl:28 + jl + bl]


def accessor(j, b, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    n, dt = NC[a['type']], CT[a['componentType']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    item = n * np.dtype(dt).itemsize
    stride = bv.get('byteStride', item)
    if stride == item:
        arr = np.frombuffer(b, dtype=dt, count=a['count'] * n, offset=off).reshape(a['count'], n)
    else:
        raw = np.frombuffer(b, dtype=np.uint8, count=stride * a['count'], offset=off).reshape(a['count'], stride)
        arr = raw[:, :item].copy().view(dt).reshape(a['count'], n)
    arr = arr.astype(np.float64) if dt == np.float32 else arr.copy()
    if a.get('normalized') and dt != np.float32:
        arr = arr.astype(np.float64) / np.iinfo(dt).max
    return arr


def image_bytes(j, b, img):
    bv = j['bufferViews'][img['bufferView']]; o = bv.get('byteOffset', 0)
    return b[o:o + bv['byteLength']]


# ------------------------------------------------------------------------------------------------------ math helpers
def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(n):
    M = np.eye(4)
    if 'matrix' in n: return np.array(n['matrix']).reshape(4, 4).T
    s = np.array(n.get('scale', [1, 1, 1])); q = n.get('rotation', [0, 0, 0, 1]); t = n.get('translation', [0, 0, 0])
    M[:3, :3] = quat_mat(q) * s[None, :]; M[:3, 3] = t
    return M


def axis_angle(axis, ang):
    axis = np.asarray(axis, float); axis /= np.linalg.norm(axis)
    x, y, z = axis; c, s = math.cos(ang), math.sin(ang); C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


# -------------------------------------------------------------------------------------------------------- game model
class Game:
    def __init__(self, path):
        self.j, self.b = j, b = read_glb(path)
        skin = j['skins'][0]
        self.joints = skin['joints']
        self.names = [j['nodes'][i]['name'] for i in self.joints]
        self.jidx = {n: k for k, n in enumerate(self.names)}
        self.ibm = accessor(j, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        self.parent = {}
        for i, n in enumerate(j['nodes']):
            for c in n.get('children', []): self.parent[c] = i
        self.local = {i: trs(j['nodes'][i]) for i in range(len(j['nodes']))}
        mesh_node = next(i for i, n in enumerate(j['nodes']) if 'mesh' in n and j['meshes'][n['mesh']]['name'] == 'SpiderManMesh')
        self.mesh_node = mesh_node
        p = j['meshes'][j['nodes'][mesh_node]['mesh']]['primitives'][0]
        A = p['attributes']
        self.P = accessor(j, b, A['POSITION'])
        self.N = accessor(j, b, A['NORMAL'])
        self.J = accessor(j, b, A['JOINTS_0']).astype(np.int64)
        self.W = accessor(j, b, A['WEIGHTS_0'])
        self.W /= self.W.sum(1, keepdims=True)
        # joint order used for FK: parents before children
        order, seen = [], set()
        def visit(i):
            if i in seen: return
            if i in self.parent and self.parent[i] in self.joints: visit(self.parent[i])
            seen.add(i); order.append(i)
        for i in self.joints: visit(i)
        self.order = order
        # static world transform of the chain above the joint roots (the SpiderRig node etc.)
        self.base = {}
        for i in self.joints:
            chain, k = [], self.parent.get(i)
            while k is not None and k not in self.joints: chain.append(k); k = self.parent.get(k)
            M = np.eye(4)
            for c in reversed(chain): M = M @ self.local[c]
            self.base[i] = M
        self.rest_globals = self.fk({})
        self.rest_pos = {n: self.rest_globals[self.jidx[n]][:3, 3] for n in self.names}

    def fk(self, pose):
        """pose: {joint name: (R 3x3 world-space rotation about the joint, s uniform scale)} -> 58 global matrices."""
        G = {}
        for i in self.order:
            par = self.parent.get(i)
            M = (G[par] if par in G else self.base[i]) @ self.local[i]
            name = self.j['nodes'][i]['name']
            if name in pose:
                R, s = pose[name]
                p = M[:3, 3].copy()
                T = np.eye(4); T[:3, :3] = R
                M = M.copy(); M[:3, :3] = R @ M[:3, :3]
                if s != 1.0: M[:3, :3] = M[:3, :3] * s
                M[:3, 3] = p
            G[i] = M
        return np.stack([G[i] for i in self.joints])

    def skin_mats(self, pose):
        return self.fk(pose) @ self.ibm

    def deform(self, S, P=None, N=None, J=None, W=None):
        P = self.P if P is None else P; J = self.J if J is None else J; W = self.W if W is None else W
        B = np.einsum('vk,vkij->vij', W, S[J])
        Pd = np.einsum('vij,vj->vi', B[:, :3, :3], P) + B[:, :3, 3]
        Nd = None
        if N is not None:
            Nd = np.einsum('vij,vj->vi', B[:, :3, :3], N); Nd /= np.linalg.norm(Nd, axis=1, keepdims=True) + 1e-12
        return Pd, Nd


# --------------------------------------------------------------------------------------------------------- the fit
# parameter vector (mirrored left/right). Angles in radians about WORLD axes (glTF: +X character's left, +Y up,
# +Z forward); scales are multipliers.
PARAMS = [
    ('arm_abduct', 0.0, 0.6),       # upperArm about Z (+ raises the left arm; mirrored for the right)
    ('arm_swing', 0.0, 0.5),        # upperArm about X (forward/back)
    ('elbow', 0.0, 0.6),            # forearm about X (bend)
    ('elbow_z', 0.0, 0.5),          # forearm about Z
    ('shoulder', 0.0, 0.3),         # shoulder about Z (shrug)
    ('ua_s', 1.0, 0.25),            # upperArm scale
    ('fa_s', 1.0, 0.25),            # forearm scale
    ('hand_s', 1.0, 0.3),           # hand scale
    ('thigh_abduct', 0.0, 0.3),     # thigh about Z
    ('thigh_s', 1.0, 0.2),
    ('shin_s', 1.0, 0.2),
    ('spine_s', 1.0, 0.2),          # spine1 scale (torso length)
    ('neck_s', 1.0, 0.3),           # neck scale (head height / size)
    ('head_s', 1.0, 0.3),
]


def pose_from(x):
    v = {k: x[i] for i, (k, _, _) in enumerate(PARAMS)}
    X, Z = np.array([1., 0, 0]), np.array([0, 0, 1.])
    pose = {}
    for side, sg in (('L', 1.0), ('R', -1.0)):
        pose[f'shoulder.{side}'] = (axis_angle(Z, sg * v['shoulder']), 1.0)
        pose[f'upperArm.{side}'] = (axis_angle(Z, sg * v['arm_abduct']) @ axis_angle(X, v['arm_swing']), v['ua_s'])
        pose[f'forearm.{side}'] = (axis_angle(X, v['elbow']) @ axis_angle(Z, sg * v['elbow_z']), v['fa_s'])
        pose[f'hand.{side}'] = (np.eye(3), v['hand_s'])
        pose[f'thigh.{side}'] = (axis_angle(Z, sg * v['thigh_abduct']), v['thigh_s'])
        pose[f'shin.{side}'] = (np.eye(3), v['shin_s'])
    pose['spine1'] = (np.eye(3), v['spine_s'])
    pose['neck'] = (np.eye(3), v['neck_s'])
    pose['head'] = (np.eye(3), v['head_s'])
    return pose


def normalise_target(T, game):
    """Scale the Tripo mesh to the game mesh's height, feet on the floor, centred on the game torso."""
    T = T.copy()
    gh = game.P[:, 1].max() - game.P[:, 1].min()
    T[:, 1] -= T[:, 1].min(); T *= gh / T[:, 1].max(); T[:, 1] += game.P[:, 1].min()
    T[:, 0] -= (T[:, 0].max() + T[:, 0].min()) / 2
    # depth: align the torso centre (chest band) with the game's
    def torso_z(P):
        sel = (np.abs(P[:, 0]) < 0.12) & (np.abs(P[:, 1] - (P[:, 1].min() + 0.72 * gh)) < 0.05)
        return (P[sel, 2].max() + P[sel, 2].min()) / 2
    T[:, 2] += torso_z(game.P) - torso_z(T)
    return T


def fit_pose(game, T, log=print):
    rng = np.random.default_rng(0)
    gi = rng.choice(len(game.P), min(6000, len(game.P)), replace=False)
    ti = rng.choice(len(T), min(9000, len(T)), replace=False)
    Ts = T[ti]; ttree = cKDTree(Ts)
    Pg, Jg, Wg = game.P[gi], game.J[gi], game.W[gi]
    x0 = np.array([p[1] for p in PARAMS]); span = np.array([p[2] for p in PARAMS])

    def cost(x):
        S = game.skin_mats(pose_from(x))
        D, _ = game.deform(S, Pg, None, Jg, Wg)
        d1, _ = ttree.query(D)
        d2, _ = cKDTree(D).query(Ts)
        reg = np.sum(((x - x0) / span) ** 2) * 1e-4
        return np.mean(d1 ** 2) + np.mean(d2 ** 2) + reg

    c0 = cost(x0)
    t = time.time()
    res = minimize(cost, x0, method='Powell', options={'maxiter': 6000, 'xtol': 1e-4, 'ftol': 1e-7})
    x = np.clip(res.x, x0 - span, x0 + span)
    c1 = cost(x)
    log(f'  pose fit: chamfer rms {math.sqrt(c0) * 100:.2f} cm -> {math.sqrt(c1) * 100:.2f} cm in {time.time() - t:.1f}s ({res.nfev} evals)')
    log('  params: ' + ', '.join(f'{k}={x[i]:+.3f}' for i, (k, _, _) in enumerate(PARAMS)))
    return x, math.sqrt(c0), math.sqrt(c1)


def weld_weights(dense, T):
    """Vertices at the same position (UV-seam duplicates) must share ONE set of weights, or the seam opens into hairline cracks
    as soon as the pose changes (seen in UE as thin see-through lines along every texture seam)."""
    key = np.round(T / 2e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    acc = np.zeros((inv.max() + 1, dense.shape[1])); cnt = np.bincount(inv).astype(float)[:, None]
    np.add.at(acc, inv, dense)
    return (acc / cnt)[inv]


def spatial_smooth(dense, T, TN, radius, iters):
    """Average skin weights over 3D neighbours that face the same way, ACROSS mesh layers (jacket over shirt, vest over sleeve):
    layers a few mm apart otherwise pick different nearest game vertices, deform differently and poke through each other."""
    tree = cKDTree(T)
    pr = tree.query_pairs(radius, output_type='ndarray')
    i, j = pr[:, 0], pr[:, 1]
    ok = np.einsum('ij,ij->i', TN[i], TN[j]) > 0.3
    i, j = i[ok], j[ok]
    d = np.linalg.norm(T[i] - T[j], axis=1)
    w = np.exp(-(d / (radius * 0.6)) ** 2)[:, None]
    for _ in range(iters):
        acc = dense.copy(); ws = np.ones((len(T), 1))
        np.add.at(acc, i, w * dense[j]); np.add.at(acc, j, w * dense[i])
        np.add.at(ws, i, w); np.add.at(ws, j, w)
        dense = acc / ws
    return dense


def transfer_weights(game, S, T, TN, faces, k=12, smooth_iters=3, spatial=0.0, spatial_iters=4, weld=False):
    Pd, Nd = game.deform(S, None, game.N)
    tree = cKDTree(Pd)
    dist, idx = tree.query(T, k=k)
    nj = len(game.names)
    dense = np.zeros((len(T), nj))
    ndot = np.einsum('vkc,vc->vk', Nd[idx], TN)
    ok = ndot > 0.2
    ok[~ok.any(1), 0] = True                                         # no normal-compatible neighbour: use nearest
    w = np.where(ok, 1.0 / (dist + 1e-4) ** 2, 0.0)
    for kk in range(k):
        np.add.at(dense, (np.arange(len(T))[:, None], game.J[idx[:, kk]]), (w[:, kk:kk + 1] * game.W[idx[:, kk]]))
    dense /= dense.sum(1, keepdims=True)
    # smooth over the Tripo mesh (vertex adjacency from faces)
    if smooth_iters:
        e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
        e = np.concatenate([e, e[:, ::-1]])
        deg = np.bincount(e[:, 0], minlength=len(T)).astype(float)[:, None]
        for _ in range(smooth_iters):
            acc = np.zeros_like(dense); np.add.at(acc, e[:, 0], dense[e[:, 1]])
            dense = 0.5 * dense + 0.5 * acc / np.maximum(deg, 1)
    if weld:
        dense = weld_weights(dense, T)
    if spatial > 0:
        dense = spatial_smooth(dense, T, TN, spatial, spatial_iters)
        if weld:
            dense = weld_weights(dense, T)
    top = np.argsort(-dense, axis=1)[:, :4]
    tw = np.take_along_axis(dense, top, 1)
    tw /= tw.sum(1, keepdims=True)
    return top.astype(np.int64), tw


def unpose(S, T, TN, J, W):
    B = np.einsum('vk,vkij->vij', W, S[J])
    Binv = np.linalg.inv(B)
    R = np.einsum('vij,vj->vi', Binv[:, :3, :3], T) + Binv[:, :3, 3]
    N = np.einsum('vji,vj->vi', B[:, :3, :3], TN)               # inverse-transpose of B^-1 is B^T
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    return R, N


# ------------------------------------------------------------------------------------------------------ GLB writing
class Buf:
    def __init__(self): self.data = bytearray(); self.views = []; self.accs = []

    def view(self, raw, target=None):
        while len(self.data) % 4: self.data += b'\0'
        v = {'buffer': 0, 'byteOffset': len(self.data), 'byteLength': len(raw)}
        if target: v['target'] = target
        self.data += raw; self.views.append(v); return len(self.views) - 1

    def acc(self, arr, ctype, typ, target=None, minmax=False, normalized=False):
        raw = np.ascontiguousarray(arr).tobytes()
        a = {'bufferView': self.view(raw, target), 'componentType': ctype, 'count': int(arr.shape[0]), 'type': typ}
        if normalized: a['normalized'] = True
        if minmax:
            a['min'] = [float(v) for v in arr.min(0)]; a['max'] = [float(v) for v in arr.max(0)]
        self.accs.append(a); return len(self.accs) - 1


def write_glb(out, game, R, N, UV, faces, J, W, tex_webp, name, with_anims):
    gj, gb = game.j, game.b
    buf = Buf()
    # geometry
    prim = {'attributes': {
        'POSITION': buf.acc(R.astype(np.float32), 5126, 'VEC3', 34962, minmax=True),
        'NORMAL': buf.acc(N.astype(np.float32), 5126, 'VEC3', 34962),
        'TEXCOORD_0': buf.acc(UV.astype(np.float32), 5126, 'VEC2', 34962),
        'JOINTS_0': buf.acc(J.astype(np.uint8), 5121, 'VEC4', 34962),
        'WEIGHTS_0': buf.acc(W.astype(np.float32), 5126, 'VEC4', 34962)},
        'indices': buf.acc(faces.reshape(-1).astype(np.uint32), 5125, 'SCALAR', 34963), 'material': 0}
    img_view = buf.view(tex_webp)
    # skeleton: copy the game's joint nodes and SpiderRig root verbatim; inverse bind matrices verbatim
    ibm = accessor(gj, gb, gj['skins'][0]['inverseBindMatrices']).astype(np.float32)
    ibm_acc = buf.acc(ibm, 5126, 'MAT4')
    keep = sorted(set(game.joints))
    root = next(i for i, n in enumerate(gj['nodes']) if n.get('name') == 'SpiderRig')
    remap = {}
    nodes = []
    for i in keep + [root]:
        remap[i] = len(nodes); nodes.append(None)
    mesh_node_idx = len(nodes)
    for i in keep + [root]:
        n = {k: v for k, v in gj['nodes'][i].items() if k not in ('children', 'mesh', 'skin')}
        ch = [remap[c] for c in gj['nodes'][i].get('children', []) if c in remap]
        if i == root: ch = ch + [mesh_node_idx]
        if ch: n['children'] = ch
        nodes[remap[i]] = n
    nodes.append({'name': name, 'mesh': 0, 'skin': 0})
    j = {
        'asset': {'version': '2.0', 'generator': 'spider-man-2 tools/skinfit/skinfit.py'},
        'extensionsUsed': ['EXT_texture_webp'], 'extensionsRequired': ['EXT_texture_webp'],
        'scene': 0, 'scenes': [{'name': 'Scene', 'nodes': [remap[root]]}],
        'nodes': nodes,
        'meshes': [{'name': name, 'primitives': [prim]}],
        'skins': [{'name': 'SpiderRig', 'joints': [remap[i] for i in game.joints], 'inverseBindMatrices': ibm_acc}],
        'materials': [{'name': 'SkinSuit', 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0.0, 'roughnessFactor': 0.55}}],
        'textures': [{'sampler': 0, 'extensions': {'EXT_texture_webp': {'source': 0}}}],
        'samplers': [{'magFilter': 9729, 'minFilter': 9987}],
        'images': [{'name': name + '_basecolor', 'mimeType': 'image/webp', 'bufferView': img_view}],
    }
    if with_anims:
        anims = []
        for an in gj['animations']:
            ch, sm = [], []
            for s in an['samplers']:
                ni = buf.acc(accessor(gj, gb, s['input']).astype(np.float32), 5126, 'SCALAR', minmax=True)
                oa = gj['accessors'][s['output']]
                no = buf.acc(accessor(gj, gb, s['output']).astype(np.float32), 5126, oa['type'])
                sm.append({'input': ni, 'output': no, 'interpolation': s.get('interpolation', 'LINEAR')})
            for c in an['channels']:
                if c['target']['node'] not in remap: continue
                ch.append({'sampler': c['sampler'], 'target': {'node': remap[c['target']['node']], 'path': c['target']['path']}})
            anims.append({'name': an['name'], 'channels': ch, 'samplers': sm})
        j['animations'] = anims
    j['bufferViews'] = buf.views; j['accessors'] = buf.accs
    while len(buf.data) % 4: buf.data += b'\0'
    j['buffers'] = [{'byteLength': len(buf.data)}]
    js = json.dumps(j, separators=(',', ':')).encode()
    while len(js) % 4: js += b' '
    total = 12 + 8 + len(js) + 8 + len(buf.data)
    with open(out, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(buf.data), 0x004E4942)); f.write(bytes(buf.data))


# ------------------------------------------------------------------------------------------------------------- main
def load_tripo(path):
    j, b = read_glb(path)
    node = next(n for n in j['nodes'] if 'mesh' in n)
    p = j['meshes'][node['mesh']]['primitives'][0]
    P = accessor(j, b, p['attributes']['POSITION'])
    N = accessor(j, b, p['attributes']['NORMAL'])
    UV = accessor(j, b, p['attributes']['TEXCOORD_0'])
    F = accessor(j, b, p['indices']).reshape(-1, 3).astype(np.int64)
    M = trs(node)
    P = P @ M[:3, :3].T + M[:3, 3]; N = N @ M[:3, :3].T
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    mat = j['materials'][p['material']]
    ti = mat['pbrMetallicRoughness']['baseColorTexture']['index']
    img = j['images'][j['textures'][ti]['source']]
    return P, N, UV, F, image_bytes(j, b, img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tripo'); ap.add_argument('out')
    ap.add_argument('--game', default='public/assets/spiderman.glb')
    ap.add_argument('--name', default='SkinMesh')
    ap.add_argument('--tex', type=int, default=4096)
    ap.add_argument('--with-anims', action='store_true')
    ap.add_argument('--weld', action='store_true', help='share weights between coincident (UV-seam duplicate) vertices: no hairline cracks when posed')
    ap.add_argument('--spatial-smooth', type=float, default=0.0, help='metres: also smooth weights across mesh layers (clothed people); 0 = off (suits)')
    ap.add_argument('--report')
    a = ap.parse_args()
    t0 = time.time()
    game = Game(a.game)
    P, N, UV, F, img = load_tripo(a.tripo)
    print(f'{a.tripo}: {len(P)} verts, {len(F)} tris')
    T = normalise_target(P, game)
    x, c0, c1 = fit_pose(game, T)
    S = game.skin_mats(pose_from(x))
    J, W = transfer_weights(game, S, T, N, F, spatial=a.spatial_smooth, weld=a.weld)
    R, RN = unpose(S, T, N, J, W)
    # round-trip check: re-posing the rest mesh must give back the Tripo mesh
    Tback, _ = game.deform(S, R, None, J, W)
    err = np.abs(Tback - T).max()
    print(f'  un-pose round trip max error {err * 1000:.4f} mm')
    im = Image.open(io.BytesIO(img)).convert('RGB')
    if im.width > a.tex: im = im.resize((a.tex, a.tex), Image.LANCZOS)
    bio = io.BytesIO(); im.save(bio, 'WEBP', quality=90, method=6)
    write_glb(a.out, game, R, RN, UV, F, J, W, bio.getvalue(), a.name, a.with_anims)
    import os
    print(f'  wrote {a.out} ({os.path.getsize(a.out) / 1e6:.1f} MB) in {time.time() - t0:.1f}s')
    if a.report:
        json.dump({'tripo': a.tripo, 'verts': len(P), 'tris': len(F), 'chamfer_rms_cm_before': c0 * 100, 'chamfer_rms_cm_after': c1 * 100,
                   'params': {k: float(x[i]) for i, (k, _, _) in enumerate(PARAMS)}, 'roundtrip_max_mm': float(err * 1000)},
                  open(a.report, 'w'), indent=1)


if __name__ == '__main__':
    main()
