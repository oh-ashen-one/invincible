"""Blender (headless) pass A for one AI suit: bake the geometry maps the texture analysis needs.

    blender -b --factory-startup -P tools/ue_char/suitmaps/bake_base.py -- <suit> [--res 4096]

Builds the fitted skin's bind-pose mesh straight from public/assets/skins/<suit>.glb (vertex order, UVs and
normals exactly as shipped), then bakes into _scratch/characters/suits/<suit>/:
  mask.png      UV coverage (no margin)          ao.png       Cycles ambient occlusion (bind pose)
  pos.exr       object-space position (glTF metres, Y up)
  onrm.exr      object-space shading normal
  tangents.npy  per-vertex MikkTSpace tangent (xyz) + bitangent sign, glTF space

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import os, sys
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import mesh_arrays, orig_skin, SCRATCH  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
SUIT = argv[0]
RES = int(argv[argv.index('--res') + 1]) if '--res' in argv else 4096
OUT = os.path.join(SCRATCH, SUIT); os.makedirs(OUT, exist_ok=True)


def setup_cycles(samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type = 'METAL'; prefs.get_devices()
        for d in prefs.devices: d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:  # CPU fallback
        print('GPU setup failed', e)
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False


def build_mesh(suit):
    j, b, P, N, UV, F = mesh_arrays(orig_skin(suit))
    me = bpy.data.meshes.new(suit)
    me.from_pydata(P.tolist(), [], F.tolist())
    uvl = me.uv_layers.new(name='UVMap')
    loop_v = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', loop_v)
    uvb = UV[loop_v].copy(); uvb[:, 1] = 1.0 - uvb[:, 1]
    uvl.data.foreach_set('uv', uvb.astype(np.float32).ravel())
    me.shade_smooth()
    me.normals_split_custom_set_from_vertices(N.astype(np.float32).tolist())
    me.update()
    ob = bpy.data.objects.new(suit, me); bpy.context.scene.collection.objects.link(ob)
    return ob, P, N


def new_image(name, float_buf=False):
    im = bpy.data.images.new(name, RES, RES, alpha=False, float_buffer=float_buf)
    im.generated_color = (0, 0, 0, 1)
    im.colorspace_settings.name = 'Non-Color'   # data maps: no view transform / sRGB curve on save
    return im


def material_with(ob, emit_socket_fn=None):
    mat = bpy.data.materials.new('bake'); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.name = 'target'
    if emit_socket_fn:
        em = nt.nodes.new('ShaderNodeEmission')
        emit_socket_fn(nt, em)
        nt.links.new(em.outputs[0], out.inputs[0])
    else:
        bs = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(bs.outputs[0], out.inputs[0])
    ob.data.materials.clear(); ob.data.materials.append(mat)
    nt.nodes.active = tex
    return mat, tex


def bake(ob, kind, img, path, margin=16, emit_fn=None, space=None, fmt='PNG'):
    mat, tex = material_with(ob, emit_fn)
    tex.image = img
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    kw = dict(type=kind, margin=margin, use_clear=True)
    if space: kw['normal_space'] = space
    bpy.ops.object.bake(**kw)
    img.filepath_raw = path; img.file_format = fmt
    img.save()
    print('baked', path)


bpy.ops.wm.read_factory_settings(use_empty=True)
setup_cycles(1)
ob, P, N = build_mesh(SUIT)
sc = bpy.context.scene
sc.render.bake.margin_type = 'EXTEND'
sc.view_settings.view_transform = 'Standard'

# tangents (MikkTSpace on the custom normals + UVs; averaged per vertex, they are identical at a shared vertex)
me = ob.data
me.calc_tangents(uvmap='UVMap')
nl = len(me.loops)
lt = np.zeros(nl * 3, np.float32); me.loops.foreach_get('tangent', lt); lt = lt.reshape(-1, 3)
ls = np.zeros(nl, np.float32); me.loops.foreach_get('bitangent_sign', ls)
lv = np.zeros(nl, np.int64); me.loops.foreach_get('vertex_index', lv)
T = np.zeros((len(P), 3)); S = np.zeros(len(P))
np.add.at(T, lv, lt); np.add.at(S, lv, ls)
T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
S = np.where(S >= 0, 1.0, -1.0)
# spread of loop tangents at a vertex (should be ~0)
dev = 1 - (lt * T[lv]).sum(1)
print('tangent loop deviation max', float(dev.max()), 'frac>0.01', float((dev > 0.01).mean()))
np.save(os.path.join(OUT, 'tangents.npy'), np.concatenate([T, S[:, None]], 1).astype(np.float32))


def emit_const(nt, em): em.inputs['Color'].default_value = (1, 1, 1, 1)


def emit_pos(nt, em):
    g = nt.nodes.new('ShaderNodeNewGeometry'); nt.links.new(g.outputs['Position'], em.inputs['Color'])


def emit_nrm(nt, em):
    g = nt.nodes.new('ShaderNodeNewGeometry'); nt.links.new(g.outputs['Normal'], em.inputs['Color'])


bake(ob, 'EMIT', new_image('mask'), os.path.join(OUT, 'mask.png'), margin=0, emit_fn=emit_const)
bake(ob, 'EMIT', new_image('pos', True), os.path.join(OUT, 'pos.exr'), margin=8, emit_fn=emit_pos, fmt='OPEN_EXR')
bake(ob, 'EMIT', new_image('onrm', True), os.path.join(OUT, 'onrm.exr'), margin=8, emit_fn=emit_nrm, fmt='OPEN_EXR')
setup_cycles(256)
sc.world = bpy.data.worlds.new('w'); sc.world.light_settings.distance = 0.3
bake(ob, 'AO', new_image('ao'), os.path.join(OUT, 'ao.png'), margin=16)
print('DONE', SUIT)
