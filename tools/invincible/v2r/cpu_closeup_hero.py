# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# CPU-only Cycles close-up render of ONE hero clip from a fixed camera table (same camera for old and new, so a pair differs only in
# the motion). Workbench is not used (flat look hides nothing but also shows no weight); Cycles CPU keeps the GPU untouched.
#   Blender -b --factory-startup -P cpu_closeup_hero.py -- --glb <file.glb> --action <name> --out <dir> [--cams tq,front,side]
#        [--samples 16] [--size 480x540] [--fps 24] [--every 1] [--lens 50] [--label old]
# Output: <out>/<label>_<cam>/0000.png ... and a JSON with the frame count. The camera yaw is measured from the hero's facing
# (left_foot - left_ankle at frame 0, horizontal); target = pelvis height at frame 0; distance so a 1.9 m body fills ~75 % of the height.
import argparse, json, math, os, sys
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('--glb', required=True); ap.add_argument('--action', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--cams', default='tq,front'); ap.add_argument('--samples', type=int, default=16); ap.add_argument('--size', default='480x540')
ap.add_argument('--fps', type=int, default=24); ap.add_argument('--every', type=int, default=1); ap.add_argument('--lens', type=float, default=50.0)
ap.add_argument('--label', default='clip'); ap.add_argument('--scale', type=float, default=0.0, help='armature scale (0 = auto: 0.01 if the body is over 20 units tall)')
ap.add_argument('--threads', type=int, default=8)
a = ap.parse_args(argv)
W, H = [int(x) for x in a.size.split('x')]
YAW = {'front': 0.0, 'tq': 40.0, 'side': 90.0, 'back': 180.0}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
sc = bpy.context.scene; sc.render.fps = a.fps
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o, do_unlink=True)
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); body = next(o for o in sc.objects if o.type == 'MESH')
act = bpy.data.actions.get(a.action)
if act is None: raise SystemExit('no action %s in %s; have %s' % (a.action, a.glb, [x.name for x in bpy.data.actions]))
if arm.animation_data is None: arm.animation_data_create()
for tr in arm.animation_data.nla_tracks: tr.mute = True
arm.animation_data.action = act
try: arm.animation_data.action_slot = act.slots[0]
except Exception: pass
f0, f1 = act.frame_range
sc.frame_set(int(f0)); bpy.context.view_layer.update()
def wb():
    deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps)
    zs = [(ev.matrix_world @ v.co).z for v in ev.data.vertices]; return min(zs), max(zs)
lo, hi = wb()
scale = a.scale or (0.01 if hi - lo > 20 else 1.0)
arm.scale = (scale, scale, scale); bpy.context.view_layer.update(); lo, hi = wb()
AW = arm.matrix_world; h = lambda n: AW @ arm.pose.bones[n].head
fwd = h('left_foot') - h('left_ankle'); fwd.z = 0; fwd.normalize()
pel = h('pelvis'); body_h = hi - lo
# studio: grey world, soft sun + fill, floor under the lowest point of frame 0 (the hover hangs over it)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.42, 0.41, 0.40, 1); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.0; sun.data.angle = math.radians(20); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.atan2(fwd.y, fwd.x) + math.radians(150))
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = 1.2; fill.data.angle = math.radians(60); sc.collection.objects.link(fill)
fill.rotation_euler = (math.radians(35), 0, math.atan2(fwd.y, fwd.x) - math.radians(140))
r = 40.0; fz = min(lo, 0.0)
fm = bpy.data.meshes.new('floor'); fm.from_pydata([(-r, -r, fz), (r, -r, fz), (r, r, fz), (-r, r, fz)], [], [(0, 1, 2, 3)])
mat = bpy.data.materials.new('floor'); mat.use_nodes = True
pb = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); pb.inputs['Base Color'].default_value = (0.36, 0.35, 0.34, 1); pb.inputs['Roughness'].default_value = 0.9
fm.materials.append(mat); sc.collection.objects.link(bpy.data.objects.new('floor', fm))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = a.samples; sc.cycles.use_denoising = True
try: bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'NONE'
except Exception as ex: print('prefs', ex)
sc.render.threads_mode = 'FIXED'; sc.render.threads = a.threads
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
target = Vector((pel.x, pel.y, pel.z + 0.05 * body_h))
dist = body_h * 0.5 / math.tan(0.5 * 2 * math.atan(12.0 / a.lens)) / 0.75 * (H / W if W < H else 1.0)   # 24 mm sensor height, body ~75 % of the frame height
cams = {}
for name in a.cams.split(','):
    yaw = math.radians(YAW[name]); d = Vector((fwd.x * math.cos(yaw) - fwd.y * math.sin(yaw), fwd.x * math.sin(yaw) + fwd.y * math.cos(yaw), 0))
    cd = bpy.data.cameras.new(name); cd.lens = a.lens; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 24.0; cd.clip_end = 1000
    co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co)
    loc = target + d * dist + Vector((0, 0, 0.12 * body_h)); co.location = loc
    co.rotation_euler = (target - loc).to_track_quat('-Z', 'Y').to_euler(); cams[name] = co
frames = list(range(int(f0), int(f1) + 1, a.every))
info = dict(glb=a.glb, action=a.action, frames=len(frames), fps=a.fps, first=int(f0), last=int(f1), body_h=body_h, facing=list(fwd), scale=scale, cams=a.cams)
for name, co in cams.items():
    d = os.path.join(a.out, '%s_%s' % (a.label, name)); os.makedirs(d, exist_ok=True); sc.camera = co
    for i, f in enumerate(frames):
        sc.frame_set(f); sc.render.filepath = os.path.join(d, '%04d.png' % i); bpy.ops.render.render(write_still=True)
json.dump(info, open(os.path.join(a.out, '%s_info.json' % a.label), 'w'), indent=1)
print('CLOSEUP', json.dumps(info))
