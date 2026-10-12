"""Neutral still renders of raw Tripo people (Blender 5.2 headless, Eevee): full body front/side + head + hands close-ups.

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
blender -b -P tools/ue_char/people/inspect_raw.py -- OUT_DIR GLB [GLB ...]
Raw Tripo meshes are normalised to a unit box; here they are scaled to 1.8 m tall for the renders.
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]; GLBS = argv[1:]
os.makedirs(OUT, exist_ok=True)

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    try: sc.render.engine = 'BLENDER_EEVEE'
    except TypeError: sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.2, 0.2, 0.22, 1); bg.inputs[1].default_value = 1.0
    def area(loc, e, size):
        d = bpy.data.lights.new('l', 'AREA'); d.energy = e; d.size = size
        o = bpy.data.objects.new('l', d); sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0, 1.0)) - o.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    area((-2.5, -3, 3), 700, 3); area((3, -2, 1.5), 300, 3); area((0.5, 3, 3), 400, 2)
    cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
    return sc, cam

def shoot(sc, cam, path, target, dist, lens, az_deg):
    cam.data.lens = lens
    a = math.radians(az_deg)
    cam.location = (target[0] + math.sin(a) * dist, target[1] - math.cos(a) * dist, target[2])
    cam.rotation_euler = (Vector(target) - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

for g in GLBS:
    name = os.path.splitext(os.path.basename(g))[0].replace('+', '_').replace(' ', '')
    sc, cam = setup_scene()
    bpy.ops.import_scene.gltf(filepath=g)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    # find tallest axis (glTF Y up -> Blender Z up after import)
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    zmin = min(p.z for p in pts); zmax = max(p.z for p in pts); h = zmax - zmin
    s = 1.8 / h
    for o in objs:
        o.scale = (s, s, s)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    zmin = min(p.z for p in pts)
    for o in objs: o.location.z -= zmin
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]
    print('RAW', name, 'x', round(min(xs), 2), round(max(xs), 2), 'y', round(min(ys), 2), round(max(ys), 2))
    cx = (min(xs) + max(xs)) / 2; cy = (min(ys) + max(ys)) / 2
    shoot(sc, cam, f'{OUT}/{name}_front.png', (cx, cy, 0.95), 4.2, 50, 0)
    shoot(sc, cam, f'{OUT}/{name}_side.png', (cx, cy, 0.95), 4.2, 50, 90)
    shoot(sc, cam, f'{OUT}/{name}_head.png', (cx, cy, 1.62), 1.1, 85, 0)
    # hands: find extreme x vertices around hand height (arms out) -> use the two extremes in the widest axis
    axis = 0 if (max(xs) - min(xs)) > (max(ys) - min(ys)) else 1
    vals = xs if axis == 0 else ys
    hi = max(pts, key=lambda p: p[axis]); lo = min(pts, key=lambda p: p[axis])
    for tag, p in (('handA', hi), ('handB', lo)):
        shoot(sc, cam, f'{OUT}/{name}_{tag}.png', (p.x, p.y, p.z), 0.9, 85, 0 if axis == 0 else 90)
