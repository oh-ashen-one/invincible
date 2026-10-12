"""Shared helpers for the AI-suit PBR map pipeline (tools/ue_char/suitmaps).

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import io, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
import json, struct

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):  # same as tools/skinfit/skinfit.py (copied: Blender's python has no scipy)
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

DL = os.path.expanduser('~/Downloads')
SUITS = {  # skin name -> Tripo source GLB (identical vertex count/order to the fitted skin)
    'claude': os.path.join(DL, 'claude spiderman.glb'),
    'codex': os.path.join(DL, 'spiderman chatgpt.glb'),
    'gemini': os.path.join(DL, 'spiderman gemini.glb'),
    'kimi': os.path.join(DL, 'kimi spiderman.glb'),
    'qwen': os.path.join(DL, 'qwen spioderman.glb'),
}
SCRATCH = _scr('suits')
ART = os.path.join(ROOT, 'art', 'night1', 'characters', 'suits')
SKINS = os.path.join(ROOT, 'public', 'assets', 'skins')


def skin_path(s): return os.path.join(SKINS, s + '.glb')


def mesh_arrays(path):
    j, b = read_glb(path)
    p = j['meshes'][0]['primitives'][0]
    A = p['attributes']
    P = accessor(j, b, A['POSITION']); N = accessor(j, b, A['NORMAL']); UV = accessor(j, b, A['TEXCOORD_0'])
    F = accessor(j, b, p['indices']).reshape(-1, 3).astype(np.int64)
    return j, b, P, N, UV, F


def basecolor_bytes(j, b):
    t = j['textures'][j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]
    src = t.get('extensions', {}).get('EXT_texture_webp', {}).get('source', t.get('source'))
    return image_bytes(j, b, j['images'][src])


ORIG_COMMIT = 'c97c50c'   # commit that shipped the original skinfit GLBs (inputs of this pipeline)


def orig_skin(suit):
    """The original skinfit GLB, extracted from git history into _scratch (idempotent reruns)."""
    import subprocess
    p = os.path.join(SCRATCH, 'orig', suit + '.glb')
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        data = subprocess.run(['git', '-C', ROOT, 'show', f'{ORIG_COMMIT}:public/assets/skins/{suit}.glb'],
                              check=True, capture_output=True).stdout
        open(p, 'wb').write(data)
    return p
