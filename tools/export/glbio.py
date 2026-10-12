"""Minimal GLB reader / writer (numpy only) for the exporter's glTF files. Attributes come back as float64 arrays."""
import json, struct
import numpy as np

_DT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
_N = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

def read_glb(path):
    """-> dict(attrs={name: (n, k) array}, index=(m,) uint32 array, js=json, prim=first primitive dict)"""
    b = open(path, 'rb').read()
    (jl,) = struct.unpack('<I', b[12:16]); js = json.loads(b[20:20 + jl])
    off = 20 + jl; (bl,) = struct.unpack('<I', b[off:off + 4]); bin_ = b[off + 8:off + 8 + bl]
    def acc(i):
        a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
        n = _N[a['type']]; o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = bv.get('byteStride')
        arr = np.frombuffer(bin_, dtype=_DT[a['componentType']], count=a['count'] * n, offset=o).reshape(-1, n) if not stride or stride == n * np.dtype(_DT[a['componentType']]).itemsize else None
        if arr is None:  # interleaved
            isz = np.dtype(_DT[a['componentType']]).itemsize
            raw = np.frombuffer(bin_, dtype=np.uint8, offset=o)
            arr = np.stack([np.frombuffer(raw[i * stride:i * stride + n * isz].tobytes(), dtype=_DT[a['componentType']]) for i in range(a['count'])])
        if a.get('normalized'):
            arr = arr.astype(np.float64) / np.iinfo(_DT[a['componentType']]).max
        return arr.astype(np.float64) if arr.dtype != np.uint32 else arr
    attrs, idx, prims = {}, [], []
    base = 0
    for mesh in js['meshes']:
        for pr in mesh['primitives']:
            A = {k: acc(v) for k, v in pr['attributes'].items()}
            I = acc(pr['indices']).reshape(-1).astype(np.int64) if 'indices' in pr else np.arange(len(A['POSITION']))
            for k, v in A.items(): attrs.setdefault(k, []).append(v)
            idx.append(I + base); base += len(A['POSITION']); prims.append(pr)
    attrs = {k: np.concatenate(v) for k, v in attrs.items()}
    return {'attrs': attrs, 'index': np.concatenate(idx), 'js': js}

def write_glb(path, attrs, index, name='mesh'):
    """attrs: POSITION (n,3) float, NORMAL, TEXCOORD_0.. (n,2), COLOR_0 (n,4); index (m,) ints -> GLB (one primitive)."""
    chunks, views, accs, ap = [], [], [], {}
    def add(arr, dtype, typ, ctype, target, minmax=False):
        arr = np.ascontiguousarray(arr.astype(dtype)); data = arr.tobytes()
        off = sum(len(c) for c in chunks); pad = (4 - len(data) % 4) % 4
        chunks.append(data + b'\0' * pad)
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data), 'target': target})
        a = {'bufferView': len(views) - 1, 'componentType': ctype, 'count': int(arr.shape[0]), 'type': typ}
        if minmax: a['min'] = arr.min(0).astype(float).tolist(); a['max'] = arr.max(0).astype(float).tolist()
        accs.append(a); return len(accs) - 1
    for k, v in attrs.items():
        typ = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}[v.shape[1]]
        ap[k] = add(v, np.float32, typ, 5126, 34962, minmax=(k == 'POSITION'))
    ii = add(np.asarray(index).reshape(-1, 1), np.uint32, 'SCALAR', 5125, 34963)
    js = {'asset': {'version': '2.0', 'generator': 'sm2 city street kit'}, 'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': name}],
          'meshes': [{'name': name, 'primitives': [{'attributes': ap, 'indices': ii, 'mode': 4}]}],
          'buffers': [{'byteLength': sum(len(c) for c in chunks)}], 'bufferViews': views, 'accessors': accs}
    j = json.dumps(js, separators=(',', ':')).encode(); j += b' ' * ((4 - len(j) % 4) % 4)
    bn = b''.join(chunks)
    open(path, 'wb').write(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(j) + 8 + len(bn)) + struct.pack('<I4s', len(j), b'JSON') + j + struct.pack('<I4s', len(bn), b'BIN\0') + bn)
