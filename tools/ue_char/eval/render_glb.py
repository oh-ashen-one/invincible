"""Evaluation clip for a skinned GLB on the hero 58-joint rig (hero, thug, brute, AI suits).

Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.

blender -b -P tools/ue_char/eval/render_glb.py -- NAME GLB [--anims HERO_GLB] [--bc IMAGE] [--scale S]
   [--clips walk,run] [--stats JSON]
Clip: orbit while walking (1-60), 3/4 walk (61-105), side view second clip (106-150). Also writes a face close-up.
"""
import bpy, sys, os, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SCR = _scr('eval', 'frames')
DOCS = os.path.join(ROOT, 'docs/night1/characters/round-01/assets')

ap = argparse.ArgumentParser()
ap.add_argument('name'); ap.add_argument('glb')
ap.add_argument('--anims'); ap.add_argument('--bc'); ap.add_argument('--scale', type=float, default=1.0)
ap.add_argument('--clips', default='walk,run'); ap.add_argument('--stats')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])

sc = studio.reset()
bpy.ops.import_scene.gltf(filepath=a.glb)
keep = set(bpy.context.scene.objects)
arm = next(o for o in keep if o.type == 'ARMATURE')
if a.anims:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=a.anims)
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.context.scene.objects):   # stray non-rig objects
    if o.type == 'MESH' and o.parent is None:
        bpy.data.objects.remove(o, do_unlink=True)
arm.scale = (a.scale,) * 3
if a.bc:
    img = bpy.data.images.load(os.path.abspath(a.bc))
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p and p.inputs['Base Color'].is_linked:
            src = p.inputs['Base Color'].links[0].from_node
            while src.type != 'TEX_IMAGE' and src.inputs and any(i.is_linked for i in src.inputs):
                src = next(i for i in src.inputs if i.is_linked).links[0].from_node
            if src.type == 'TEX_IMAGE':
                src.image = img

meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name != 'floor']
bpy.context.view_layer.update()
zs = [(o.matrix_world @ o.data.vertices[i].co).z for o in meshes for i in range(0, len(o.data.vertices), 7)]
H = (max(zs) - min(zs))
clips = a.clips.split(',')
acts = {c: bpy.data.actions[c] for c in clips}
studio.nla_sequence(arm, [(acts[clips[0]], 1, studio.SEG2), (acts[clips[-1]], studio.SEG2 + 1, studio.N)])
studio.setup(height=max(1.6, H))

stats = {'name': a.name}
for o in meshes:
    me = o.data
    stats.setdefault('meshes', []).append({'obj': o.name, 'verts': len(me.vertices),
        'tris': sum(len(p.vertices) - 2 for p in me.polygons),
        'mats': [m.name for m in me.materials if m]})
imgs = {}
for m in bpy.data.materials:
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                imgs[n.image.name] = list(n.image.size)
stats['images'] = imgs
stats['height_m'] = round(H, 3)
if a.stats:
    json.dump(stats, open(a.stats, 'w'), indent=1)
headz = max(zs) - 0.13 * H
studio.render(SCR, a.name, DOCS, still_frame=95, face=(headz, 1.1 * H / 1.8))
