# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Minimal glTF binary editing: read a GLB, append accessors (new buffer views at the end of the BIN chunk), rewrite primitives, write it back."""
import json, struct
import numpy as np

CT = {np.dtype(np.float32): 5126, np.dtype(np.uint8): 5121, np.dtype(np.uint16): 5123, np.dtype(np.uint32): 5125}
TYPE = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}


class Glb:
    def __init__(self, path):
        d = open(path, 'rb').read()
        assert d[:4] == b'glTF'
        jl = struct.unpack('<I', d[12:16])[0]
        self.j = json.loads(d[20:20 + jl])
        bl = struct.unpack('<I', d[20 + jl:24 + jl])[0]
        self.bin = bytearray(d[28 + jl:28 + jl + bl])
        self.rest = d[28 + jl + bl:]          # (no further chunks expected)

    def add(self, arr, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        while len(self.bin) % 4: self.bin.append(0)
        off = len(self.bin)
        self.bin += arr.tobytes()
        bv = {'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes}
        if target: bv['target'] = target
        self.j['bufferViews'].append(bv)
        n = arr.shape[1] if arr.ndim > 1 else 1
        a = {'bufferView': len(self.j['bufferViews']) - 1, 'componentType': CT[arr.dtype], 'count': int(arr.shape[0]), 'type': TYPE[n]}
        if minmax:
            a['min'] = [float(x) for x in arr.reshape(len(arr), -1).min(0)]; a['max'] = [float(x) for x in arr.reshape(len(arr), -1).max(0)]
        self.j['accessors'].append(a)
        return len(self.j['accessors']) - 1

    def save(self, path):
        while len(self.bin) % 4: self.bin.append(0)
        self.j['buffers'][0]['byteLength'] = len(self.bin)
        js = json.dumps(self.j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
        out = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(self.bin)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(self.bin)) + b'BIN\x00' + bytes(self.bin)
        open(path, 'wb').write(out)
