"""Blender headless preview of a skinfit'd person playing hero-rig clips (walk, run, thug clips).

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
blender -b -P tools/ue_char/people/preview_fit.py -- FIT.glb OUT_PREFIX [--clips walk,thugPunch1] [--frames 1,8,15,22] [--scale 1.0] [--girth 1.0]
Actions come from public/assets/spiderman.glb (79 hero clips) and public/assets/thug.glb (13 thug clips); the fitted character has the
hero's exact joint names so any of them binds. Writes OUT_PREFIX_<clip>_<view>.png (front, side, 3/4) for the listed frames as a sheet.
"""
import bpy, sys, os, math, argparse
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
ap = argparse.ArgumentParser()
ap.add_argument('fit'); ap.add_argument('out')
ap.add_argument('--clips', default='walk'); ap.add_argument('--frames', default='1,9,17,25')
ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--girth', type=float, default=1.0)
ap.add_argument('--res', type=int, default=640)
ap.add_argument('--extra', default=None, help='GLB whose actions are also made available (e.g. the walks GLB)')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_EEVEE'
except TypeError: sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x = a.res; sc.render.resolution_y = int(a.res * 1.25)
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.32, 0.33, 0.36, 1); bg.inputs[1].default_value = 1.0
for loc, e, sz in (((-2.5, -3, 3), 350, 3), ((3, -2, 1.5), 150, 3), ((0.5, 3, 3), 250, 2)):
    d = bpy.data.lights.new('l', 'AREA'); d.energy = e; d.size = sz
    o = bpy.data.objects.new('l', d); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 1.0)) - o.location).normalized().to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0)); fl = bpy.context.object
fm = bpy.data.materials.new('f'); fm.use_nodes = True
next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.08, 0.08, 0.09, 1); fl.data.materials.append(fm)

bpy.ops.import_scene.gltf(filepath=a.fit)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
mesh_names = [o.name for o in bpy.context.scene.objects if o.type == 'MESH' and o.name != fl.name]
# borrow the action sets
srcs = [os.path.join(ROOT, 'public/assets/spiderman.glb'), os.path.join(ROOT, 'public/assets/thug.glb')] + ([a.extra] if a.extra else [])
for src in srcs:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=src)
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
arm.scale = (a.scale * a.girth, a.scale * a.girth, a.scale)
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.lens = 45
arm.animation_data_create()
views = {'front': 0, 'q34': -35, 'side': -90}
frames = [int(x) for x in a.frames.split(',')]
sheets = []
for clip in a.clips.split(','):
    act = bpy.data.actions.get(clip)
    if act is None:
        print('MISSING clip', clip); continue
    arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]
    for fr in frames:
        sc.frame_set(fr)
        bpy.context.view_layer.update()
        for vn, az in views.items():
            r = math.radians(az)
            H = 1.8 * a.scale
            dist = 3.4 * a.scale
            cam.location = (math.sin(r) * dist, -math.cos(r) * dist, 0.98 * a.scale)
            cam.rotation_euler = (Vector((0, 0, 0.95 * a.scale)) - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = '%s_%s_f%02d_%s.png' % (a.out, clip, fr, vn)
            bpy.ops.render.render(write_still=True)
print('preview done', a.out)
