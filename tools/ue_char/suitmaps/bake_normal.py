"""Blender (headless) pass B for one AI suit: bake the tangent-space normal map from height.png on the FINAL geometry.

    blender -b --factory-startup -P tools/ue_char/suitmaps/bake_normal.py -- <suit> [--res 4096]

Mesh = fitted skin topology/UVs + geom.npz positions/normals (welded seams, flattened back emblem). The height map
(build_maps.py) drives a Bump node in metres; Cycles bakes the shading normal:
  normal_ogl.png  tangent space, OpenGL (+Y) convention as glTF expects
  onrm_bump.exr   object-space bumped normal (used by write_glb.py to verify the tangent convention numerically)
  tangents2.npy   per-vertex MikkTSpace tangent + bitangent sign of this exact mesh (written into the GLB)

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import os, sys, json
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import mesh_arrays, orig_skin, SCRATCH  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
SUIT = argv[0]
RES = int(argv[argv.index('--res') + 1]) if '--res' in argv else 4096
D = os.path.join(SCRATCH, SUIT)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for dv in prefs.devices: dv.use = True
    sc.cycles.device = 'GPU'
except Exception as e:
    print('GPU setup failed', e)
sc.cycles.samples = 4
sc.render.bake.margin_type = 'EXTEND'
sc.view_settings.view_transform = 'Standard'

j, b, _, _, UV, F = mesh_arrays(orig_skin(SUIT))
g = np.load(os.path.join(D, 'geom.npz'))
P, N = g['P'].astype(np.float64), g['N'].astype(np.float64)
me = bpy.data.meshes.new(SUIT)
me.from_pydata(P.tolist(), [], F.tolist())
uvl = me.uv_layers.new(name='UVMap')
lv = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
uvb = UV[lv].copy(); uvb[:, 1] = 1.0 - uvb[:, 1]
uvl.data.foreach_set('uv', uvb.astype(np.float32).ravel())
me.shade_smooth()
me.normals_split_custom_set_from_vertices(N.astype(np.float32).tolist())
me.update()
ob = bpy.data.objects.new(SUIT, me); sc.collection.objects.link(ob)

me.calc_tangents(uvmap='UVMap')
nl = len(me.loops)
lt = np.zeros(nl * 3, np.float32); me.loops.foreach_get('tangent', lt); lt = lt.reshape(-1, 3)
ls = np.zeros(nl, np.float32); me.loops.foreach_get('bitangent_sign', ls)
T = np.zeros((len(P), 3)); S = np.zeros(len(P))
np.add.at(T, lv, lt); np.add.at(S, lv, ls)
T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
S = np.where(S >= 0, 1.0, -1.0)
np.save(os.path.join(D, 'tangents2.npy'), np.concatenate([T, S[:, None]], 1).astype(np.float32))

hinfo = json.load(open(os.path.join(D, 'maps.json')))['height_m']
himg = bpy.data.images.load(os.path.join(D, 'height.png')); himg.colorspace_settings.name = 'Non-Color'

mat = bpy.data.materials.new('bake'); nt = mat.node_tree if mat.node_tree else None
mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
ht = nt.nodes.new('ShaderNodeTexImage'); ht.image = himg; ht.interpolation = 'Cubic'
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY_ADD'
mul.inputs[1].default_value = hinfo['max'] - hinfo['min']; mul.inputs[2].default_value = hinfo['min']
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = 1.0
nt.links.new(ht.outputs['Color'], mul.inputs[0]); nt.links.new(mul.outputs[0], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal']); nt.links.new(bsdf.outputs[0], out.inputs[0])
tgt = nt.nodes.new('ShaderNodeTexImage'); nt.nodes.active = tgt
ob.data.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob

for name, space, fmt, ext in (('normal_ogl', 'TANGENT', 'PNG', 'png'), ('onrm_bump', 'OBJECT', 'OPEN_EXR', 'exr')):
    im = bpy.data.images.new(name, RES, RES, alpha=False, float_buffer=(fmt == 'OPEN_EXR'))
    im.colorspace_settings.name = 'Non-Color'
    tgt.image = im
    bpy.ops.object.bake(type='NORMAL', normal_space=space, margin=16, use_clear=True)
    im.filepath_raw = os.path.join(D, f'{name}.{ext}'); im.file_format = fmt
    im.save()
    print('baked', im.filepath_raw)
print('DONE', SUIT)
