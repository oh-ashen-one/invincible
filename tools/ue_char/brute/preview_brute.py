"""Still preview of the thug rig with a given base colour map (Blender 5.2, headless Eevee, grey studio).

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.

blender -b -P tools/ue_char/brute/preview_brute.py -- OUT_PREFIX BASECOLOR.png [--scale 1.24] [--pose walk|rest] [--frame 12] [--tag x]
Writes OUT_PREFIX_{front,q34,side,back,head}.png (960x1080). The walk pose comes from the hero glb clip 'walk' (the game plays it on this rig).
"""
import bpy, sys, os, math, argparse
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/ue_char/eval'))
import studio

ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('bc')
ap.add_argument('--scale', type=float, default=1.0)
ap.add_argument('--xy', type=float, default=1.0, help='extra girth multiplier on X/Y (brute build)')
ap.add_argument('--pose', default='walk'); ap.add_argument('--frame', type=int, default=6)
ap.add_argument('--glb', default=os.path.join(ROOT, 'public/assets/thug.glb'))
ap.add_argument('--views', default='front,q34,side,back,head')
ap.add_argument('--res', type=int, default=960, help='render width; height = width*9/8')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])

sc = studio.reset()
bpy.ops.import_scene.gltf(filepath=a.glb)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
if a.pose == 'walk':
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'public/assets/spiderman.glb'))
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
    act = bpy.data.actions['walk']
    arm.animation_data_create(); arm.animation_data.action = act
    sc.frame_set(a.frame)
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH' and o.parent is None and o.name != 'floor':
        bpy.data.objects.remove(o, do_unlink=True)
arm.scale = (a.scale * a.xy, a.scale * a.xy, a.scale)
img = bpy.data.images.load(os.path.abspath(a.bc))
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if p and p.inputs['Base Color'].is_linked:
        src = p.inputs['Base Color'].links[0].from_node
        while src.type != 'TEX_IMAGE' and any(i.is_linked for i in src.inputs):
            src = next(i for i in src.inputs if i.is_linked).links[0].from_node
        if src.type == 'TEX_IMAGE':
            src.image = img
bpy.context.view_layer.update()
H = 1.8 * a.scale
studio.setup(height=H, res=(a.res, a.res * 9 // 8))
cam = sc.camera
for fc in list(cam.animation_data.action.fcurves) if hasattr(cam.animation_data.action, 'fcurves') else []:
    pass
cam.animation_data_clear()
for c in list(cam.constraints):
    cam.constraints.remove(c)
sc.render.image_settings.file_format = 'PNG'
views = {'front': (0, 0.53 * H, 2.0 * H, 50), 'q34': (-35, 0.53 * H, 2.0 * H, 50), 'side': (-90, 0.53 * H, 2.0 * H, 50), 'back': (180, 0.53 * H, 2.0 * H, 50),
         'head': (-15, 0.955 * H, 0.55 * H, 85), 'head_f': (0, 0.955 * H, 0.55 * H, 85), 'head_s': (-90, 0.955 * H, 0.55 * H, 85),
         'head_b': (180, 0.955 * H, 0.55 * H, 85), 'upper': (-30, 0.75 * H, 1.1 * H, 60)}
for name in a.views.split(','):
    ang, tz, dist, lens = views[name]
    cam.data.lens = lens
    r = math.radians(ang)
    cam.location = (math.sin(r) * dist, -math.cos(r) * dist, tz + 0.05)
    d = Vector((0, 0, tz)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = '%s_%s.png' % (a.out, name)
    bpy.ops.render.render(write_still=True)
print('preview done', a.out)
