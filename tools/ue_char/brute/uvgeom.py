"""Dump the thug mesh's UV triangles with rest-pose 3D positions (run inside Blender, headless).

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.

blender -b -P tools/ue_char/brute/uvgeom.py -- [GLB] [OUT.npz]

Writes per triangle: island id, 3x uv, 3x rest-pose position (Blender axes: +Z up, -Y is the character's front,
T-pose so arms run along X), dominant skin bone id. Also the bone name list. Used by paint_brute.py to paint the
brute onto the ORIGINAL thug UV layout (the old brute_basecolor.webp belonged to a different layout).
"""
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
GLB = argv[0] if argv else os.path.join(ROOT, 'public/assets/thug.glb')
OUT = argv[1] if len(argv) > 1 else _scr('r2', 'uvgeom.npz')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
o = next(x for x in bpy.data.objects if x.type == 'MESH' and len(x.vertex_groups) > 10)
me = o.data
bones = [g.name for g in o.vertex_groups]
uv = me.uv_layers[0].data
mw = o.matrix_world
co = np.array([tuple(mw @ v.co) for v in me.vertices], dtype=np.float32)
vdom = np.zeros(len(me.vertices), np.int16)
for v in me.vertices:
    best, bw = 0, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, g.group
    vdom[v.index] = best

parent = {}
def find(a):
    while parent.setdefault(a, a) != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
keys = []
for p in me.polygons:
    ks = [(me.loops[l].vertex_index, round(uv[l].uv[0] * 4096), round(uv[l].uv[1] * 4096)) for l in p.loop_indices]
    keys.append(ks)
    for k in ks[1:]:
        ra, rb = find(ks[0]), find(k)
        if ra != rb:
            parent[ra] = rb
isl = defaultdict(list)
for i, ks in enumerate(keys):
    isl[find(ks[0])].append(i)
order = sorted(isl.items(), key=lambda kv: -len(kv[1]))
rows = []
for rid, (_, ps) in enumerate(order):
    for pi in ps:
        p = me.polygons[pi]
        ls = list(p.loop_indices)
        tris = [(ls[0], ls[1], ls[2])] + ([(ls[0], ls[2], ls[3])] if len(ls) == 4 else [])
        for t in tris:
            vi = [me.loops[l].vertex_index for l in t]
            uvs = [uv[l].uv[:] for l in t]
            rows.append([rid] + [c for u in uvs for c in u] + [c for i in vi for c in co[i]] + [int(vdom[vi[0]])])
np.savez(OUT, tris=np.array(rows, np.float32), bones=np.array(bones))
print('uvgeom: %d tris, %d islands -> %s' % (len(rows), len(order), OUT))
