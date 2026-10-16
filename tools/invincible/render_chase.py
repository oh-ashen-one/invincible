# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Render a clip from the PLAYER'S view (behind + above, looking down the hero's back along the flight line) and from the side.
# GPU: run through tools/gpu/gpu_slot.sh. usage: Blender -b --factory-startup -P render_chase.py -- <in.glb> <action> <out_prefix> <f,f,...>
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, ACT, OUT, FR = a[0], a[1], a[2], [int(x) for x in a[3].split(',')]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o)
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); AW = arm.matrix_world
arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[ACT]
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y = 520, 360
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.32, 0.34, 0.38, 1)
L = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); L.data.energy = 3.5; L.rotation_euler = (0.7, 0, 0.6); sc.collection.objects.link(L)
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 40
H = (AW @ arm.data.bones['head'].head_local - AW @ arm.data.bones['left_ankle'].head_local).length
for f in FR:
    sc.frame_set(f)
    pel = AW @ arm.pose.bones['pelvis'].head; hd = AW @ arm.pose.bones['head'].head
    ax = hd - pel; ax.z = 0; ax.normalize()                       # flight direction (horizontal)
    side = ax.cross(Vector((0, 0, 1))).normalized()
    ctr = (pel + hd) / 2
    for name, pos in (('chase', ctr - ax * H * 1.6 + Vector((0, 0, H * 1.1))), ('side', ctr + side * H * 2.0 + Vector((0, 0, H * 0.15)))):
        cam.location = pos; cam.rotation_euler = (ctr - pos).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = '%s_%s_f%03d.png' % (OUT, name, f); bpy.ops.render.render(write_still=True)
print('CHASE_OK')
