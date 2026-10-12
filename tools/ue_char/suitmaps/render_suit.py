"""Blender (headless) still of a suit skin GLB posed by the hero's own clip, front 3/4 + back 3/4, studio light.

    blender -b --factory-startup -P tools/ue_char/suitmaps/render_suit.py -- SKIN.glb OUT.png [--clip idle] [--frame 1]
        [--res 900] [--close]

The skin is imported through Blender's glTF importer (so the render also checks that its material maps load), bound to
the armature imported from public/assets/spiderman.glb (same 58 joints / inverse bind matrices) and posed by a hero clip.
Writes OUT.png with the two views side by side. --close frames the upper back / chest instead of the full body.

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import os, sys, math
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
SKIN, OUT = argv[0], argv[1]
opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
CLIP, FRAME, RES = opt('--clip', 'idle'), int(opt('--frame', '1')), int(opt('--res', '900'))
CLOSE = '--close' in argv
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30


def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


hero = imp(os.path.join(ROOT, 'public', 'assets', 'spiderman.glb'))
arm = next(o for o in hero if o.type == 'ARMATURE')
for o in hero:
    if o.type == 'MESH': o.hide_render = True
skin = imp(SKIN)
sm = max((o for o in skin if o.type == 'MESH'), key=lambda o: len(o.data.vertices))  # importer may add bone-shape meshes
sarm = next(o for o in skin if o.type == 'ARMATURE')
for m in sm.modifiers:
    if m.type == 'ARMATURE': m.object = arm
mw = sm.matrix_world.copy(); sm.parent = arm; sm.matrix_world = mw
for o in skin:
    if o is not sm: bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.users_collection and o is not sm and len(o.data.vertices) < 100: o.hide_render = True
act = bpy.data.actions.get(CLIP) or next(a for a in bpy.data.actions if a.name.startswith(CLIP))
arm.animation_data_create(); arm.animation_data.action = act
if hasattr(arm.animation_data, 'action_slot') and act.slots:
    arm.animation_data.action_slot = act.slots[0]
sc.frame_set(FRAME)
bpy.context.view_layer.update()

# studio: neutral grey world + key/fill/rim area lights, grey floor
w = bpy.data.worlds.new('studio'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.18, 0.18, 0.19, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6


def light(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    d = Vector((0, 0, 1.1)) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o


light('key', (2.5, -3.0, 3.2), 550, 2.0, (1.0, 0.97, 0.92))
light('fill', (-3.0, -2.0, 1.6), 200, 3.0, (0.9, 0.95, 1.0))
light('rim', (0.5, 3.5, 2.8), 700, 1.5)
light('rim2', (-1.0, 3.0, 1.0), 300, 1.5)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
fl = bpy.context.object; fm = bpy.data.materials.new('floor'); fm.use_nodes = True
bs = next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value = (0.25, 0.25, 0.26, 1); bs.inputs['Roughness'].default_value = 0.8
fl.data.materials.append(fm)

try: sc.render.engine = 'BLENDER_EEVEE'
except TypeError: sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 64
try: sc.eevee.use_raytracing = True
except Exception: pass
sc.view_settings.view_transform = 'AgX'
sc.render.resolution_x, sc.render.resolution_y = RES, int(RES * (1.0 if CLOSE else 1.3))
sc.render.image_settings.file_format = 'PNG'

cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.lens = 85 if CLOSE else 55
tgt = Vector((0, 0, 1.3 if CLOSE else 0.95))
dist = 1.6 if CLOSE else 3.3
# the glTF hero faces +Z, which is -Y in Blender: front 3/4 from -Y, back 3/4 from +Y
for tag, ang in (('front', -90 + 30), ('back', 90 + 30)):
    a = math.radians(ang)
    cam.location = tgt + Vector((math.cos(a) * dist, math.sin(a) * dist, 0.25 if not CLOSE else 0.1))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = OUT.replace('.png', f'_{tag}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', sc.render.filepath)
