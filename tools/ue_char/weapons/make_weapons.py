"""Simple enemy hand weapons modelled in Blender headless: baseball bat, steel pipe with an elbow fitting, generic pistol.
Fan homage project; not official Marvel/Sony/Insomniac; no affiliation. Generic shapes only (no copied design, no brand, no lettering).
  blender -b -P tools/ue_char/weapons/make_weapons.py -- OUT_DIR
Writes OUT_DIR/{bat,pipe,pistol}.glb. Frame (metres): grip centre at the origin, handle axis = +Y (the bat / pipe extend to -Y,
i.e. out of the pinky side of the fist), pistol barrel along +Z. Materials by name: wood, steel, polymer, grip, tape
(tools/ue_char/weapons/add_weapon.py maps them to solid tiles in the character atlas)."""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m


def lathe(name, profile, segs=24, material='wood'):
    """profile: list of (radius, y) from bottom to top; closed with caps. Axis = +Y."""
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    rings = []
    for r, y in profile:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * k / segs), y, r * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.materials.append(mat(material))
    for p in me.polygons: p.use_smooth = True
    return ob


def box(name, size, loc, material, bevel=0.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object; ob.name = name; ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = ob.modifiers.new('bv', 'BEVEL'); md.width = bevel; md.segments = 2
        bpy.ops.object.modifier_apply(modifier=md.name)
    ob.data.materials.append(mat(material))
    return ob


def export(name):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + '.glb'), export_format='GLB', use_selection=True,
                              export_apply=True, export_yup=True)
    print('WEAPON', name, sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type == 'MESH'))


# ---- baseball bat, 84 cm: knob at the bottom of the fist, barrel below (-Y). Grip at y = 0.
reset()
prof = [(0.018, 0.075), (0.021, 0.07), (0.013, 0.062), (0.0125, 0.0), (0.013, -0.12), (0.016, -0.26), (0.024, -0.40), (0.030, -0.52),
        (0.0325, -0.62), (0.0335, -0.72), (0.032, -0.755), (0.026, -0.765)]
bat = lathe('bat', [(r, -y) for r, y in prof][::-1], material='wood')   # flip: knob up at +Y... then rotate so the knob sits at +Y
bat.data.transform(Matrix.Rotation(math.pi, 4, 'X'))
lathe('bat_tape', [(0.0138, -0.075), (0.0138, 0.07)], material='tape')
export('bat')

# ---- steel pipe, 70 cm, with a threaded elbow fitting at the far end
reset()
lathe('pipe', [(0.0165, -0.60), (0.0165, 0.10)], segs=20, material='steel')
lathe('pipe_collar', [(0.0205, -0.64), (0.0205, -0.585)], segs=20, material='steel')
el = lathe('pipe_elbow', [(0.0205, 0.0), (0.0205, 0.07)], segs=20, material='steel')
el.data.transform(Matrix.Translation((0, -0.64, 0)) @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Translation((0, -0.02, 0)))
lathe('pipe_wrap', [(0.019, -0.06), (0.019, 0.06)], segs=20, material='grip')
export('pipe')

# ---- generic pistol (polymer frame, steel slide), barrel along +Z, grip along Y through the origin
reset()
g = box('grip', (0.030, 0.105, 0.046), (0, -0.005, 0), 'polymer', 0.004)
g.data.transform(Matrix.Rotation(math.radians(-16), 4, 'X'))          # grip rake
box('frame', (0.028, 0.030, 0.150), (0, 0.062, 0.045), 'polymer', 0.003)
box('slide', (0.026, 0.030, 0.175), (0, 0.090, 0.052), 'steel', 0.003)
box('guard', (0.012, 0.006, 0.050), (0, 0.030, 0.050), 'polymer', 0.002)
box('trigger', (0.006, 0.020, 0.008), (0, 0.040, 0.038), 'steel', 0.001)
box('sight', (0.006, 0.006, 0.008), (0, 0.108, 0.132), 'steel', 0.0)
export('pistol')
