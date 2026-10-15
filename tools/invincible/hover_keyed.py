# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Hand-keyed hover idle for the hero (owner reference: show-style hover -- body vertical, hips under the chest, legs hanging together with
# one knee bent back, toes pointed, arms slightly off the body, fists clenched, head level) + a crotch-volume fix on the v2 sculpt.
# Poses are built by AIMING bones at world directions (rig-axis independent), keyed as a seamless 4 s loop at 30 fps.
# usage: Blender -b --factory-startup -P tools/invincible/hover_keyed.py -- <rigged.glb> <out.glb> [--no-meshfix] [--still out.png]
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
MESHFIX = '--no-meshfix' not in argv
FPS, N = 30, 120                                   # 4 s loop

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 0, N
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o)
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
body = next(o for o in sc.objects if o.type == 'MESH')
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
AW = arm.matrix_world
def rest_head(n): return AW @ arm.data.bones[n].head_local
UP = Vector((0, 0, 1))
FWD = (rest_head('left_foot') - rest_head('left_ankle')); FWD.z = 0; FWD.normalize()     # toes point forward
LEFT = (rest_head('left_hip') - rest_head('right_hip')); LEFT.z = 0; LEFT.normalize()   # character's left
H = rest_head('head').z - min(rest_head('left_ankle').z, rest_head('right_ankle').z)
print('FRAME fwd', tuple(round(x, 2) for x in FWD), 'left', tuple(round(x, 2) for x in LEFT), 'height', round(H, 3))

# ---------------------------------------------------------------- 1. crotch volume fix (rest-pose mesh, skin weights untouched)
if MESHFIX:
    mw = body.matrix_world; mwi = mw.inverted()
    pel = rest_head('pelvis'); lh, rh = rest_head('left_hip'), rest_head('right_hip')
    crotch = (lh + rh) / 2 - UP * (0.10 * H)                     # groin centre, a little under the hip joints
    R = 0.085 * H
    bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
    sel, wts = [], {}
    # the body's front surface depth at groin height (median of the front-most points across the hips) = where the bulge should sit
    for v in bm.verts:
        p = mw @ v.co; d = p - crotch
        lat = abs(d.dot(LEFT)); vert = d.dot(UP); fwd = d.dot(FWD)
        if fwd > -0.01 * H and lat < 0.075 * H and -0.11 * H < vert < 0.07 * H:
            w = max(0.0, 1.0 - math.sqrt((lat / (0.075 * H)) ** 2 + (vert / (0.09 * H)) ** 2))
            if w > 0: sel.append(v); wts[v] = w * w * (3 - 2 * w)
    # the flat line: front depth of the lower belly just above, and of the inner thighs either side
    ref = [(mw @ v.co - crotch).dot(FWD) for v in bm.verts
           if abs((mw @ v.co - crotch).dot(LEFT)) < 0.06 * H and 0.09 * H < (mw @ v.co - crotch).dot(UP) < 0.13 * H and (mw @ v.co - crotch).dot(FWD) > 0]
    flat = sorted(ref)[int(len(ref) * 0.9)] if ref else 0.06 * H
    moved = 0
    for v in sel:
        p = mw @ v.co; f = (p - crotch).dot(FWD)
        over = f - (flat - 0.004 * H)
        if over > 0:
            p = p - FWD * (over * 0.85 * wts[v]); v.co = mwi @ p; moved += 1
    for _ in range(6):                                            # relax the moved patch so it reads as cloth over the body, not a dent
        bmesh.ops.smooth_vert(bm, verts=sel, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(body.data); bm.free(); body.data.update()
    print('MESHFIX crotch verts', len(sel), 'moved', moved, 'flat', round(flat, 4))

# ---------------------------------------------------------------- 2. posing helpers
pb = arm.pose.bones
for p in pb: p.rotation_mode = 'QUATERNION'
def world(n): return AW @ pb[n].matrix
def limb(n):
    """the bone's real limb direction in world space: its head -> its first child's head (the glTF import does NOT point bone +Y
    along the limb on this rig, e.g. left_knee +Y points forward); leaves continue their parent's direction"""
    b = arm.data.bones[n]
    if b.children:
        return ((AW @ pb[b.children[0].name].head) - (AW @ pb[n].head)).normalized()
    return ((AW @ pb[n].head) - (AW @ pb[b.parent.name].head)).normalized()
def aim(n, d, twist_ref=None):
    """rotate bone n (in world space, minimal arc) so its limb (head -> child head) points along world direction d"""
    m = world(n); y = limb(n)
    q = y.rotation_difference(d.normalized())
    new = Matrix.LocRotScale(m.to_translation(), q @ m.to_quaternion(), m.to_scale())
    pb[n].matrix = AW.inverted() @ new; bpy.context.view_layer.update()
def turn(n, axis_world, deg):
    m = world(n); q = Quaternion(axis_world.normalized(), math.radians(deg))
    pb[n].matrix = AW.inverted() @ Matrix.LocRotScale(m.to_translation(), q @ m.to_quaternion(), m.to_scale()); bpy.context.view_layer.update()
def bone_dir(n): return limb(n)
FINGERS = ['index', 'middle', 'ring', 'pinky']

def pose(t):
    """t in [0,1): one loop. Reference hover: vertical body, legs together, right knee bent back, toes down, fists, arms a bit out."""
    s1, c1 = math.sin(2 * math.pi * t), math.cos(2 * math.pi * t)
    s2 = math.sin(4 * math.pi * t + 0.7)
    for p in pb: p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    # body: hips UNDER the chest (pelvis tilted forward a touch, never thrust forward), slow bob, breathing in the chest
    pb['pelvis'].location = pb['pelvis'].location + (AW.inverted().to_3x3() @ (UP * (0.012 * H * s1)))
    bpy.context.view_layer.update()
    turn('pelvis', LEFT, 4 + 1.0 * s1)                 # tip the hips forward (tucks the groin back under the torso)
    turn('spine1', LEFT, -2.0); turn('spine2', LEFT, -1.5 + 1.2 * c1)   # chest proud, breathing
    turn('spine3', LEFT, -1.0 + 0.8 * c1)
    turn('head', LEFT, 3.0 + 0.6 * s2); turn('head', UP, 2.0 * math.sin(2 * math.pi * t + 1.3))   # level gaze, tiny scan
    # arms: hang slightly away from the body, elbows soft, fists by the thighs
    for side, sgn in (('left', 1), ('right', -1)):
        ph = 2 * math.pi * t + (0 if sgn > 0 else 0.9)
        up_dir = (-UP * 0.93 + LEFT * sgn * (0.30 + 0.02 * math.sin(ph)) - FWD * 0.02).normalized()
        aim(side + '_shoulder', up_dir)
        fore = (-UP * 0.96 + LEFT * sgn * 0.20 + FWD * (0.10 + 0.015 * math.sin(ph))).normalized()
        aim(side + '_elbow', fore)
        aim(side + '_wrist', (-UP * 0.97 + LEFT * sgn * 0.12 + FWD * 0.10).normalized())
        # fist: curl each finger joint ~80 deg around the axis across the palm; thumb wraps over
        palm_n = -LEFT * sgn                               # hanging hands: palms face the thighs
        for fn in FINGERS:
            for j, deg in ((1, 70), (2, 90), (3, 70)):
                n = '%s_%s%d' % (side, fn, j)
                if n in pb:
                    d = bone_dir(n); ax = d.cross(palm_n)   # rotating d about d x n moves it toward the palm
                    if ax.length > 1e-4: turn(n, ax, deg)
        for j, deg in ((1, 25), (2, 35), (3, 30)):
            n = '%s_thumb%d' % (side, j)
            if n in pb: turn(n, FWD, deg * sgn)
    # legs: together and hanging; LEFT leg near-straight, RIGHT knee bent with the foot trailing back; toes pointed down
    pb['left_hip'] and aim('left_hip', (-UP + FWD * (0.06 + 0.01 * s1) - LEFT * 0.04).normalized())
    aim('left_knee', (-UP + FWD * 0.02 - LEFT * 0.02).normalized())
    aim('left_ankle', (-UP * 0.88 + FWD * 0.47).normalized())          # foot pointed: toes mostly down (reference hover)
    aim('right_hip', (-UP + FWD * (0.10 - 0.01 * s1) + LEFT * 0.05).normalized())
    aim('right_knee', (-UP * 0.80 - FWD * (0.60 + 0.03 * s2)).normalized())   # shin trails back
    aim('right_ankle', (-UP * 0.80 - FWD * 0.20).normalized())         # trailing foot: pointed down-back along the shin
    for n in ('left_foot', 'right_foot'): turn(n, LEFT, 8)

act = bpy.data.actions.new('HERO_hover_keyed'); arm.animation_data_create(); arm.animation_data.action = act
for f in range(0, N + 1):
    pose((f % N) / N)
    for p in pb:
        p.keyframe_insert('rotation_quaternion', frame=f)
        if p.name == 'pelvis': p.keyframe_insert('location', frame=f)
tr = arm.animation_data.nla_tracks.new(); tr.name = act.name; tr.strips.new(act.name, 0, act); arm.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('HOVER_OK', OUT)
