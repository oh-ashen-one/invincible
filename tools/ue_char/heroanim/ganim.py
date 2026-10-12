"""glTF animation I/O + forward kinematics for the hero GLB (numpy only; runs in python3 or inside Blender).
Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

read(path) -> Doc;  Doc.sample(anim, t) -> local TRS per node;  Doc.world(local) -> 4x4 per node;
Doc.set_clip(name, times, {node: {'rotation': (K,4), 'translation': (K,3), 'scale': (K,3)}}) replaces a clip's
samplers in place (same channel targets, same clip name), Doc.write(path) re-packs the GLB (unused accessors dropped
only for replaced clips; everything else byte-identical in the BIN chunk)."""
import json, struct
import numpy as np


def qmul(a, b):
    ax, ay, az, aw = np.moveaxis(a, -1, 0); bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack([aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw,
                     aw * bw - ax * bx - ay * by - az * bz], -1)


def qinv(q):
    return q * np.array([-1, -1, -1, 1.0])


def qaxis(axis, ang):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis)
    return np.concatenate([axis * np.sin(ang / 2), [np.cos(ang / 2)]])


def qrot(q, v):
    qv = np.concatenate([v, [0.0]])
    return qmul(qmul(q, qv), qinv(q))[:3]


def qslerp(a, b, u):
    d = float(np.dot(a, b))
    if d < 0: b = -b; d = -d
    if d > 0.9995:
        r = a + (b - a) * u; return r / np.linalg.norm(r)
    th = np.arccos(d); s = np.sin(th)
    return (np.sin((1 - u) * th) * a + np.sin(u * th) * b) / s


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs_mat(t, r, s):
    M = np.eye(4); M[:3, :3] = qmat(r) * np.asarray(s)[None, :]; M[:3, 3] = t
    return M


class Doc:
    def __init__(self, path):
        raw = open(path, 'rb').read()
        n = struct.unpack_from('<I', raw, 12)[0]
        self.j = json.loads(raw[20:20 + n])
        off = 20 + n; bl = struct.unpack_from('<I', raw, off)[0]
        self.bin = bytearray(raw[off + 8: off + 8 + bl])
        self.nodes = self.j['nodes']
        self.names = [nd.get('name', '') for nd in self.nodes]
        self.idx = {nm: i for i, nm in enumerate(self.names)}
        self.parent = {c: i for i, nd in enumerate(self.nodes) for c in nd.get('children', [])}
        self.joints = self.j['skins'][0]['joints']
        order = []
        seen = set()
        def visit(i):
            if i in seen: return
            if i in self.parent: visit(self.parent[i])
            seen.add(i); order.append(i)
        for i in range(len(self.nodes)): visit(i)
        self.order = order

    def acc(self, i):
        a = self.j['accessors'][i]; v = self.j['bufferViews'][a['bufferView']]
        nc = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        assert a['componentType'] == 5126
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = v.get('byteStride', nc * 4)
        out = np.empty((a['count'], nc), np.float64)
        for k in range(a['count']):
            out[k] = struct.unpack_from('<' + 'f' * nc, self.bin, off + k * stride)
        return out

    def anim(self, name):
        return next(a for a in self.j['animations'] if a['name'] == name)

    def duration(self, name):
        a = self.anim(name)
        return max(float(self.acc(s['input'])[-1, 0]) for s in a['samplers'])

    def tracks(self, name):
        """{node: {path: (times, values, interp)}}"""
        a = self.anim(name); out = {}
        for c in a['channels']:
            s = a['samplers'][c['sampler']]
            out.setdefault(c['target']['node'], {})[c['target']['path']] = (self.acc(s['input'])[:, 0], self.acc(s['output']), s.get('interpolation', 'LINEAR'))
        return out

    def rest_local(self):
        L = {}
        for i, nd in enumerate(self.nodes):
            L[i] = (np.array(nd.get('translation', [0, 0, 0]), float), np.array(nd.get('rotation', [0, 0, 0, 1]), float),
                    np.array(nd.get('scale', [1, 1, 1]), float))
        return L

    @staticmethod
    def interp(times, vals, interp, t, path):
        if t <= times[0]: return vals[0].copy()
        if t >= times[-1]: return vals[-1].copy()
        k = int(np.searchsorted(times, t, side='right') - 1)
        if interp == 'STEP': return vals[k].copy()
        u = (t - times[k]) / max(1e-9, times[k + 1] - times[k])
        if path == 'rotation': return qslerp(vals[k], vals[k + 1], u)
        return vals[k] * (1 - u) + vals[k + 1] * u

    def sample(self, tracks, t):
        L = self.rest_local()
        for n, ch in tracks.items():
            t_, r_, s_ = L[n]
            if 'translation' in ch: t_ = self.interp(*ch['translation'], t, 'translation')
            if 'rotation' in ch: r_ = self.interp(*ch['rotation'], t, 'rotation')
            if 'scale' in ch: s_ = self.interp(*ch['scale'], t, 'scale')
            L[n] = (t_, r_ / np.linalg.norm(r_), s_)
        return L

    def world(self, L):
        W = {}
        for i in self.order:
            M = trs_mat(*L[i])
            W[i] = W[self.parent[i]] @ M if i in self.parent else M
        return W

    def pos(self, W, name):
        return W[self.idx[name]][:3, 3].copy()

    # ---------- write
    def _append(self, arr, typ):
        while len(self.bin) % 4: self.bin.append(0)
        raw = np.ascontiguousarray(arr, dtype=np.float32).tobytes()
        self.j['bufferViews'].append({'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(raw)})
        self.bin.extend(raw)
        a = {'bufferView': len(self.j['bufferViews']) - 1, 'componentType': 5126, 'count': int(arr.shape[0]), 'type': typ}
        if typ == 'SCALAR':
            a['min'] = [float(arr.min())]; a['max'] = [float(arr.max())]
        self.j['accessors'].append(a)
        return len(self.j['accessors']) - 1

    def set_clip(self, name, times, data):
        """data: {node: {path: (K, n) array}} sampled at `times`; every existing channel target keeps its slot."""
        a = self.anim(name)
        ti = self._append(np.asarray(times, np.float32).reshape(-1, 1), 'SCALAR')
        new_s = []; new_c = []
        for c in a['channels']:
            n, p = c['target']['node'], c['target']['path']
            vals = data[n][p]
            oi = self._append(np.asarray(vals, np.float32), {'translation': 'VEC3', 'rotation': 'VEC4', 'scale': 'VEC3'}[p])
            new_s.append({'input': ti, 'output': oi, 'interpolation': 'LINEAR'})
            new_c.append({'sampler': len(new_s) - 1, 'target': {'node': n, 'path': p}})
        a['samplers'] = new_s; a['channels'] = new_c

    def write(self, path):
        self._compact()
        while len(self.bin) % 4: self.bin.append(0)
        self.j['buffers'][0]['byteLength'] = len(self.bin)
        js = json.dumps(self.j, separators=(',', ':')).encode()
        js += b' ' * ((4 - len(js) % 4) % 4)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin)))
            f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack('<II', len(self.bin), 0x004E4942)); f.write(bytes(self.bin))

    def _compact(self):
        """Drop accessors/bufferViews no longer referenced (the replaced clips' old keys) and re-pack the BIN chunk."""
        j = self.j
        used_acc = set()
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ('input', 'output', 'indices', 'inverseBindMatrices') and isinstance(v, int): used_acc.add(v)
                    elif k == 'attributes' or k == 'targets':
                        vs = v.values() if isinstance(v, dict) else [x for t in v for x in t.values()]
                        for x in vs: used_acc.add(x)
                    else: walk(v)
            elif isinstance(o, list):
                for x in o: walk(x)
        for key in ('meshes', 'skins', 'animations'): walk(j.get(key, []))
        amap = {}; accs = []
        for i, a in enumerate(j['accessors']):
            if i in used_acc: amap[i] = len(accs); accs.append(a)
        used_bv = {a['bufferView'] for a in accs if 'bufferView' in a}
        for im in j.get('images', []):
            if 'bufferView' in im: used_bv.add(im['bufferView'])
        bmap = {}; bvs = []; nb = bytearray()
        for i, v in enumerate(j['bufferViews']):
            if i not in used_bv: continue
            while len(nb) % 4: nb.append(0)
            o = v.get('byteOffset', 0); nv = dict(v); nv['byteOffset'] = len(nb)
            nb.extend(self.bin[o:o + v['byteLength']]); bmap[i] = len(bvs); bvs.append(nv)
        for a in accs:
            if 'bufferView' in a: a['bufferView'] = bmap[a['bufferView']]
        for im in j.get('images', []):
            if 'bufferView' in im: im['bufferView'] = bmap[im['bufferView']]
        def remap(o):
            if isinstance(o, dict):
                for k, v in list(o.items()):
                    if k in ('input', 'output', 'indices', 'inverseBindMatrices') and isinstance(v, int): o[k] = amap[v]
                    elif k == 'attributes': o[k] = {kk: amap[vv] for kk, vv in v.items()}
                    elif k == 'targets': o[k] = [{kk: amap[vv] for kk, vv in t.items()} for t in v]
                    else: remap(v)
            elif isinstance(o, list):
                for x in o: remap(x)
        for key in ('meshes', 'skins', 'animations'): remap(j.get(key, []))
        j['accessors'] = accs; j['bufferViews'] = bvs; self.bin = nb
