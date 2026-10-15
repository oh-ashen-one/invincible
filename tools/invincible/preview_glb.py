# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Headless Blender preview of a GLB (front / 3-4 / side / back stills, optional animation frames). GPU: run through tools/gpu/gpu_slot.sh.
# usage: Blender -b --factory-startup -P tools/invincible/preview_glb.py -- <in.glb> <out_prefix> [--res 900] [--action NAME --frames 1,10,20]
import bpy, sys, math, argparse
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('out'); ap.add_argument('--res', type=int, default=900)
ap.add_argument('--action'); ap.add_argument('--frames', default='')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.inp)
sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type == 'MESH']
lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
ctr = (lo + hi) / 2; h = max(hi.z - lo.z, 0.01)
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x = int(a.res * 0.8); sc.render.resolution_y = a.res
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.32, 0.34, 0.38, 1); bg.inputs[1].default_value = 0.8
for rot, e in (((50, 0, 30), 3.5), ((60, 0, -140), 1.6)):
    L = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); L.data.energy = e; L.rotation_euler = [math.radians(v) for v in rot]; sc.collection.objects.link(L)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 60
# the model's front: glTF +Z forward -> Blender -Y; pick the horizontal axis with the smaller extent as depth
dx, dy = hi.x - lo.x, hi.y - lo.y
front = Vector((0, -1, 0)) if dy <= dx else Vector((-1, 0, 0))
dist = h * 2.6
views = {'front': 0, 'q34': 35, 'side': 90, 'back': 180}
def place(ang):
    d = front.copy(); d.rotate(__import__('mathutils').Euler((0, 0, math.radians(ang))))
    cam.location = ctr + d * dist + Vector((0, 0, h * 0.05))
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
if a.action and arm:
    act = bpy.data.actions.get(a.action)
    if act: arm.animation_data_create(); arm.animation_data.action = act
frames = [int(f) for f in a.frames.split(',') if f] or [sc.frame_current]
for fr in frames:
    sc.frame_set(fr)
    for name, ang in views.items():
        if len(frames) > 1 and name not in ('q34',): continue
        place(ang); sc.render.filepath = '%s_%s%s.png' % (a.out, name, ('_f%03d' % fr) if len(frames) > 1 else '')
        bpy.ops.render.render(write_still=True)
print('PREVIEW_OK', len(frames))
