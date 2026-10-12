# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). P6 city life.
# Head masks of the 20 crowd citizens in atlas (UV) space: the triangles of the top 14 % of the mesh height, rasterised into a 1024x1024 PNG next to the FBX
# (NAME_headmask.json = the UV polygons; tools/life/citizen_variants.py rasterises them). tools/life/citizen_variants.py uses them to change hair / beard / skin tone of the head only, so the same face does not appear twice.
#   blender -b --factory-startup -P tools/life/citizen_headmask.py -- <fbx dir>
import bpy, sys, os, glob, json
import numpy as np
d = sys.argv[sys.argv.index('--') + 1]
S = 1024
for f in sorted(glob.glob(os.path.join(d, '*.fbx'))):
    name = os.path.splitext(os.path.basename(f))[0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes: print('NO MESH', name); continue
    m = max(meshes, key=lambda o: len(o.data.vertices))
    me = m.data
    co = np.array([tuple(m.matrix_world @ v.co) for v in me.vertices])
    ext = co.max(0) - co.min(0); up = int(np.argmax(ext))
    h = co[:, up]; lo, hi = h.min(), h.max(); cut = lo + 0.86 * (hi - lo)
    uv = me.uv_layers.active.data
    polys = []
    n = 0
    for p in me.polygons:
        if all(h[v] > cut for v in p.vertices):
            polys.append([(uv[l].uv[0], 1.0 - uv[l].uv[1]) for l in p.loop_indices]); n += 1
    json.dump(polys, open(os.path.join(d, name + '_headmask.json'), 'w'))
    print('%s: up axis %d height %.2f m, head polygons %d' % (name, up, hi - lo, n))
