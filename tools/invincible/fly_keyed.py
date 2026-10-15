# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Hand-keyed superman-line flight loop for the hero (built from hover_keyed.py's helpers) (owner reference: show-style hover -- body vertical, hips under the chest, legs hanging together with
# one knee bent back, toes pointed, arms slightly off the body, fists clenched, head level) + a crotch-volume fix on the v2 sculpt.
# Poses are built by AIMING bones at world directions (rig-axis independent), keyed as a seamless 4 s loop at 30 fps.
# usage: Blender -b --factory-startup -P tools/invincible/hover_keyed.py -- <rigged.glb> <out.glb> [--no-meshfix] [--still out.png]
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
MESHFIX = '--no-meshfix' not in argv
VERTICAL = '--vertical' in argv          # upright variant = launch straight up from the ground
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
    """t in [0,1): one loop. Superman-line flight (owner refs: Invincible covers), authored UPRIGHT -- the game pitches body-up onto
    the fly line, so 'overhead' = leading. Both fists reach up past the head ~shoulder-width apart, elbows barely soft, chest lifted,
    chin up (looking along the flight), legs together and long, toes pointed, one knee a touch softer. Loop = wind buffeting: hips
    drive, the motion travels up the spine into the arms (overlap), limbs on different rhythms so the loop never reads."""
    TAU = 2 * math.pi
    for p in pb: p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    # owner: flying straight ahead = lying on the flight line (head + fists forward, belly down). The upright variant (--vertical)
    # is the launch-straight-up clip. Rotate the whole body from the pelvis, then pose in the body frame U/F/L.
    if VERTICAL: U, F, L = UP, FWD, LEFT
    else:
        U, F, L = FWD, -UP, LEFT
        m = world('pelvis'); q = UP.rotation_difference(FWD)
        pb['pelvis'].matrix = AW.inverted() @ Matrix.LocRotScale(m.to_translation(), q @ m.to_quaternion(), m.to_scale())
        bpy.context.view_layer.update()
    w1 = math.sin(TAU * 2 * t); w2 = math.sin(TAU * 3 * t + 0.8); w3 = math.sin(TAU * 5 * t + 2.1)   # wind layers (2 s, 1.33 s, 0.8 s)
    hip = math.sin(TAU * t)                                                                       # slow undulation driver (4 s)
    turn('pelvis', L, -3.0 + 2.0 * hip); turn('pelvis', F, 1.5 * w1)                          # hips drive
    turn('spine1', L, -2.0 + 1.5 * math.sin(TAU * t - 0.5)); turn('spine2', L, -3.0 + 1.5 * math.sin(TAU * t - 1.0))   # chest lifted, overlap up the spine
    turn('spine3', L, -2.0 + 1.2 * math.sin(TAU * t - 1.5)); turn('spine2', F, -1.0 * w1)
    aim('neck', (U * 0.94 - F * 0.34).normalized())                                            # chin up ~20 deg: eyes ahead once the body lies on the fly line
    for side, sgn in (('left', 1), ('right', -1)):
        ph = TAU * t - 2.0 + (0.0 if sgn > 0 else 1.7)                                            # arms lag the spine; sides offset
        lead = 0.06 if sgn < 0 else 0.0                                                            # right fist leads a touch (cover pose)
        aim(side + '_collar', (L * sgn * 0.75 + U * 0.66).normalized())                       # shoulders raised with the reach
        aim(side + '_shoulder', (U * 0.97 - F * (0.12 - lead - 0.03 * math.sin(ph)) + L * sgn * (0.17 + 0.02 * w2)).normalized())   # reach forward + a touch above the line
        aim(side + '_elbow', (U * 0.97 - F * (0.06 - 0.04 * math.sin(ph - 0.6)) + L * sgn * (0.05 + 0.015 * w3)).normalized())   # forearm on the line, soft elbow
        aim(side + '_wrist', (U * 0.98 - F * (0.04 - 0.03 * math.sin(ph - 1.1)) + L * sgn * 0.03).normalized())
        palm_n = F                                                                               # fists lead with the knuckles, palms to the front
        for fn in FINGERS:
            for j, deg in ((1, 80), (2, 95), (3, 75)):
                n = '%s_%s%d' % (side, fn, j)
                if n in pb:
                    d = bone_dir(n); ax = d.cross(palm_n)
                    if ax.length > 1e-4: turn(n, ax, deg)
        for j, deg in ((1, 25), (2, 40), (3, 35)):
            n = '%s_thumb%d' % (side, j)
            if n in pb:
                d = bone_dir(n); ax = d.cross(palm_n)
                if ax.length > 1e-4: turn(n, ax, deg)
    # legs: together, long, toes pointed; the wind flutters them on their own rhythms
    for side, sgn, soft in (('left', 1, 0.10), ('right', -1, 0.18)):
        f = math.sin(TAU * 3 * t + (0.0 if sgn > 0 else 1.9))
        aim(side + '_hip', (-U + F * (0.03 + 0.025 * f) - L * sgn * 0.035).normalized())
        aim(side + '_knee', (-U - F * (soft + 0.04 * f)).normalized())
        aim(side + '_ankle', (-U * 0.96 - F * 0.05 + F * (0.27 + 0.03 * w3)).normalized())   # pointed toes

act = bpy.data.actions.new('HERO_launch_up' if VERTICAL else 'HERO_fly_keyed'); arm.animation_data_create(); arm.animation_data.action = act
for f in range(0, N + 1):
    pose((f % N) / N)
    for p in pb:
        p.keyframe_insert('rotation_quaternion', frame=f)
        if p.name == 'pelvis': p.keyframe_insert('location', frame=f)
tr = arm.animation_data.nla_tracks.new(); tr.name = act.name; tr.strips.new(act.name, 0, act); arm.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('FLY_OK', OUT)
