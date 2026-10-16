# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Hand-keyed Shift sonic-boom boost for the hero (helpers from hover_keyed.py / fly_keyed.py) (owner reference: show-style hover -- body vertical, hips under the chest, legs hanging together with
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


# Owner (2026-10-15): Shift = charge up, then a sonic boom straight ahead at double speed. Coil = elbows drawn down to the knees,
# knees pulled up to the stomach (a tight ball), head down, trembling with stored power; release = explosive stretch that overshoots
# into a long streamlined line, fists together leading; hold = tighter, faster-buffeting version of the flight line.
# Reference takeaways (search 2026-10-15): anticipation must be as big as the action; spring coil + tremble; fast release with
# overshoot (squash -> stretch). Clips: HERO_boost_full (review: hover -> coil -> launch -> hold), HERO_boost_coil, HERO_boost_launch,
# HERO_boost_hold (seamless loop). Timing matches the flight code: 0.42 s charge hang, then the boom.
TAU = 2 * math.pi
def lerp(a, b, k): return a + (b - a) * k
def ease(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

def body(theta_deg):
    """pitch the whole body from the pelvis: 0 = upright, 90 = lying on the flight line (head forward, belly down); returns U, F, L"""
    for p in pb: p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    ax = UP.cross(FWD).normalized(); q = Quaternion(ax, math.radians(theta_deg))
    m = world('pelvis')
    pb['pelvis'].matrix = AW.inverted() @ Matrix.LocRotScale(m.to_translation(), q @ m.to_quaternion(), m.to_scale())
    bpy.context.view_layer.update()
    return (q @ UP).normalized(), (q @ FWD).normalized(), LEFT

def fists(U, F, L, palm_n=None):
    """robust fist: the palm normal comes from the hand itself (hand dir x knuckle line, signed toward the thumb side), so every finger
    joint curls INTO the palm whatever the arm pose (the earlier fixed palm direction opened the hands into claws)"""
    for side in ('left', 'right'):
        hp = lambda n: AW @ pb['%s_%s' % (side, n)].head
        hd = (hp('middle1') - hp('wrist')).normalized(); kl = (hp('pinky1') - hp('index1')).normalized()
        n = hd.cross(kl).normalized()
        if n.dot(hp('thumb1') - hp('wrist')) < 0: n = -n
        for fn in FINGERS:
            for j, deg in ((1, 82), (2, 98), (3, 78)):
                b = '%s_%s%d' % (side, fn, j)
                if b in pb:
                    d = bone_dir(b); ax = d.cross(n)
                    if ax.length > 1e-4: turn(b, ax, deg)
        for j, deg in ((1, 20), (2, 35), (3, 30)):
            b = '%s_thumb%d' % (side, j)
            if b in pb:
                d = bone_dir(b); ax = d.cross(n)
                if ax.length > 1e-4: turn(b, ax, deg)

def pose(theta, c, s, buffet, t):
    """theta body pitch; c = coil 0..1 (ball); s = stretch 0..1 (streamline, >1 overshoot); buffet = wind amplitude; t = seconds"""
    U, F, L = body(theta)
    tr = 0.6 * c * math.sin(t * TAU * 11) + 0.4 * c * math.sin(t * TAU * 17 + 1.0)      # charging tremble (power building)
    bw = buffet * math.sin(t * TAU * 3.0); bw2 = buffet * math.sin(t * TAU * 4.5 + 1.3)
    # spine: curls forward into the ball when coiled, long and straight (a touch arched) when stretched
    for n, k in (('spine1', 0.30), ('spine2', 0.45), ('spine3', 0.40)):
        aim(n, (U * lerp(1.0, 0.70, c) + F * lerp(-0.05 * s, 0.70 * k / 0.45, c) + L * 0.01 * tr).normalized())
    aim('neck', (U * lerp(0.94, 0.55, c) + F * lerp(-0.34 * min(s, 1.0) - 0.0, 0.83, c)).normalized())   # head down into the coil, chin up when flying
    for side, sgn in (('left', 1), ('right', -1)):
        # coil: upper arm down-forward so the ELBOW meets the knee; forearm up so the fist sits under the chin
        up_c = (-U * 0.80 + F * 0.55 + L * sgn * 0.10); fo_c = (U * 0.85 + F * 0.40 - L * sgn * 0.25)   # elbows ON the knees, fists at the chin
        # stretch: both fists forward together on the line (tighter than cruise: fists almost touching)
        up_s = (U * 0.98 - F * 0.06 + L * sgn * (0.10 + 0.01 * bw)); fo_s = (U * 0.99 - F * 0.03 - L * sgn * (0.02 + 0.01 * bw2))
        up_h = (-U * 0.93 + L * sgn * 0.30); fo_h = (-U * 0.96 + L * sgn * 0.20 + F * 0.10)        # hover arms (start pose)
        ss = min(1.0, s); up_s = up_h * (1 - ss) + up_s * ss; fo_s = fo_h * (1 - ss) + fo_s * ss
        k = ease(c)
        aim(side + '_collar', (L * sgn * 0.75 + U * lerp(0.66 * ss, -0.1, k) + F * 0.25 * k).normalized())
        aim(side + '_shoulder', (up_s * (1 - k) + up_c * k + L * sgn * 0.01 * tr).normalized())
        aim(side + '_elbow', (fo_s * (1 - k) + fo_c * k).normalized())
        aim(side + '_wrist', (fo_s * (1 - k) + fo_c * k).normalized())
    fists(U, F, L)
    # legs: knees pulled up to the stomach (thigh forward-up, heels tucked under) vs long and tight with pointed toes
    for side, sgn, ph in (('left', 1, 0.0), ('right', -1, 1.9)):
        f = buffet * math.sin(t * TAU * 3.5 + ph)
        th_c = (F * 0.62 + U * 0.75 + L * sgn * 0.10); th_s = (-U + F * (0.02 + 0.02 * f) - L * sgn * 0.02)
        sh_c = (-U * 0.55 - F * 0.82 + L * sgn * 0.04); sh_s = (-U - F * (0.06 + 0.02 * f))
        k = ease(c)   # coil: knees pulled up to the stomach, heels tucked under the seat
        aim(side + '_hip', (th_s * (1 - k) + th_c * k + L * sgn * 0.01 * tr).normalized())
        aim(side + '_knee', (sh_s * (1 - k) + sh_c * k).normalized())
        aim(side + '_ankle', ((-U * 0.96 + F * 0.27) * (1 - k) + (-U * 0.70 - F * 0.20) * k).normalized())

def key_clip(name, frames):
    act = bpy.data.actions.new(name); arm.animation_data_create(); arm.animation_data.action = act
    for i, args in enumerate(frames):
        pose(*args)
        for p in pb:
            p.keyframe_insert('rotation_quaternion', frame=i)
            if p.name == 'pelvis': p.keyframe_insert('location', frame=i)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 0, act); arm.animation_data.action = None
    print('CLIP', name, len(frames))

def phase(f):
    """the full boost at 30 fps: 0-5 ease into the coil, 5-13 charged hang (0.42 s from the press), 13-19 launch (overshoot), then hold"""
    t = f / FPS
    if f <= 5:  k = ease(f / 5.0);           return (lerp(0, 10, k), k, 0.0, 0.0, t)
    if f <= 13:                               return (10.0, 1.0, 0.0, 0.0, t)
    if f <= 19:
        k = (f - 13) / 6.0; e = 1 - (1 - k) ** 3                      # explosive ease-out
        over = 1.0 + 0.12 * math.sin(math.pi * k)                      # overshoot stretch
        return (lerp(10, 90, e), 1 - ease(k * 1.6), over, 0.0, t)
    k = min(1.0, (f - 19) / 8.0); return (90.0, 0.0, 1.0 + 0.12 * (1 - k), 1.0, t)

key_clip('HERO_boost_full', [phase(f) for f in range(0, 91)])          # 3 s review clip (hover -> coil -> launch -> hold)
key_clip('HERO_boost_coil', [phase(f) for f in range(0, 14)])
key_clip('HERO_boost_launch', [phase(f) for f in range(13, 20)])
key_clip('HERO_boost_hold', [(90.0, 0.0, 1.0, 1.0, (f % 60) / FPS * 1.0) for f in range(0, 61)])   # 2 s seamless: 3 / 4.5 / 3.5 Hz = 6 / 9 / 7 whole cycles
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('BOOST_OK', OUT)
