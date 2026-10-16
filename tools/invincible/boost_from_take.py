# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Boost v3 from Meshy take B (owner 2026-10-15: B is closest, but the neck breaks and he must stay HORIZONTAL -- coil up on the flight
# line, then explode further in that same direction). Keeps take B's limb motion relative to the body, replaces the pelvis with the
# flight-line orientation (head forward, belly down, in place), rebuilds neck/head as a steady chin-up flight neck, closes real fists.
# usage: Blender -b --factory-startup -P tools/invincible/boost_from_take.py -- <hero_boost_meshy.glb> <take action> <out.glb>
import bpy, sys, math
from mathutils import Vector, Matrix, Quaternion

SRC, TAKE, OUT = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene; sc.render.fps = 30
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o)
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); AW = arm.matrix_world; pb = arm.pose.bones
src_act = bpy.data.actions[TAKE]
def rest_head(n): return AW @ arm.data.bones[n].head_local
UP = Vector((0, 0, 1))
FWD = rest_head('left_foot') - rest_head('left_ankle'); FWD.z = 0; FWD.normalize()
LEFT = rest_head('left_hip') - rest_head('right_hip'); LEFT.z = 0; LEFT.normalize()
def world(n): return AW @ pb[n].matrix
def limb(n):
    b = arm.data.bones[n]
    if b.children: return ((AW @ pb[b.children[0].name].head) - (AW @ pb[n].head)).normalized()
    return ((AW @ pb[n].head) - (AW @ pb[b.parent.name].head)).normalized()
def setw(n, m): pb[n].matrix = AW.inverted() @ m; bpy.context.view_layer.update()
def aim(n, d):
    m = world(n); q = limb(n).rotation_difference(d.normalized())
    setw(n, Matrix.LocRotScale(m.to_translation(), q @ m.to_quaternion(), m.to_scale()))
def turn(n, ax, deg):
    m = world(n); q = Quaternion(ax.normalized(), math.radians(deg))
    setw(n, Matrix.LocRotScale(m.to_translation(), q @ m.to_quaternion(), m.to_scale()))
FINGERS = ['index', 'middle', 'ring', 'pinky']
def fists():
    for side in ('left', 'right'):
        hp = lambda n: AW @ pb['%s_%s' % (side, n)].head
        hd = (hp('middle1') - hp('wrist')).normalized(); kl = (hp('pinky1') - hp('index1')).normalized()
        nrm = hd.cross(kl).normalized()
        if nrm.dot(hp('thumb1') - hp('wrist')) < 0: nrm = -nrm
        for fn in FINGERS:
            for j, deg in ((1, 82), (2, 98), (3, 78)):
                b = '%s_%s%d' % (side, fn, j)
                if b in pb:
                    ax = limb(b).cross(nrm)
                    if ax.length > 1e-4: turn(b, ax, deg)
        for j, deg in ((1, 20), (2, 35), (3, 30)):
            b = '%s_thumb%d' % (side, j)
            if b in pb:
                ax = limb(b).cross(nrm)
                if ax.length > 1e-4: turn(b, ax, deg)

# 1. sample take B's local poses (rotation only; root travel dropped -- the game moves the actor)
arm.animation_data_create(); arm.animation_data.action = src_act
f0, f1 = int(src_act.frame_range[0]), int(src_act.frame_range[1])
frames = []; coil = []
for f in range(f0, f1 + 1):
    sc.frame_set(f); frames.append({p.name: p.matrix_basis.copy() for p in pb})
    th = (limb('left_hip') + limb('right_hip')).normalized(); sp_up = limb('spine1')
    coil.append(max(0.0, min(1.0, (th.dot(sp_up) + 0.9) / 1.3)))   # 0 legs straight .. 1 knees at the stomach (take's own frame)
arm.animation_data.action = None
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)

# 2. rebuild: flight-line pelvis + take B limbs + steady flight neck + fists
q_flat = UP.rotation_difference(FWD)
cmax = max(coil) or 1.0
PEAK = coil.index(max(coil))                                        # deepest point of the tuck
def ease(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)
REST = {n: (AW @ arm.data.bones[n].matrix_local).to_quaternion() for n in ('spine1', 'spine2', 'spine3', 'neck', 'head')}
U, F, L = FWD, -UP, LEFT                                            # body frame on the flight line: head forward, belly down
out = bpy.data.actions.new('HERO_boost_v3'); arm.animation_data.action = out
for p in pb: p.rotation_mode = 'QUATERNION'
for i, basis in enumerate(frames):
    for p in pb: p.matrix_basis = basis[p.name] if p.name != 'pelvis' else Matrix.Identity(4)
    bpy.context.view_layer.update()
    m = world('pelvis'); setw('pelvis', Matrix.LocRotScale(m.to_translation(), q_flat @ m.to_quaternion(), m.to_scale()))
    # owner round 3: not rigid -- the approved flight idle's sway runs underneath (hips weave/bank, spine follows a beat late, head
    # drifts), the chest compresses a little into the coil and extends on the burst; still pencil-straight overall
    c = ease(coil[i] / cmax); t = i / 30.0; TAU = 2 * math.pi
    side_s = math.sin(TAU * t / 2.0); side_l = math.sin(TAU * t / 2.0 - 0.9)
    turn('pelvis', F, 3.5 * side_s); turn('pelvis', U, 5.0 * math.sin(TAU * t / 2.0 + 0.5))     # weave + bank (hips / butt move)
    turn('pelvis', L, 1.2 * math.sin(TAU * t / 1.3))                                           # small breathing rock
    FLEX = U.cross(F)                                                                          # rotating U toward F = curling toward the belly
    for n, k in (('spine1', 0.25), ('spine2', 0.40), ('spine3', 0.35)):
        m = world(n); setw(n, Matrix.LocRotScale(m.to_translation(), q_flat @ REST[n], m.to_scale()))
        bpy.context.view_layer.update()
        turn(n, FLEX, 14.0 * k * c - 4.0 * k * (1 - c))                                       # compress into the coil, extend on the burst
        turn(n, F, -2.0 * side_l * k / 0.35); turn(n, U, -2.5 * k / 0.35 * math.sin(TAU * t / 2.0 + 0.1))   # S-curve lag + counter-roll
    for n, pitch in (('neck', -10.0), ('head', -8.0)):                                         # head straight ahead, chin up, small drift
        m = world(n); q = Quaternion(L, math.radians(pitch + 1.5 * math.sin(TAU * t / 1.7))) @ q_flat @ REST[n]
        setw(n, Matrix.LocRotScale(m.to_translation(), q, m.to_scale()))
    turn('head', F, -2.5 * side_s); turn('head', U, 1.2 * math.sin(TAU * t / 2.3))
    # arms: coil = elbows bent and drawn back toward the hips, fists chambered at the ribs, knuckles forward (half punch);
    #       burst = swing forward into the parallel Superman line. Collars stay near natural (no big shoulder roll).
    for side, sgn in (('left', 1), ('right', -1)):
        up_c = (-U * 0.80 + F * 0.42 + L * sgn * 0.30).normalized()      # upper arm back toward the hip, a little out and belly-side
        fo_c = (U * 0.88 + F * 0.38 - L * sgn * 0.12).normalized()       # forearm forward: fist by the ribs, knuckles leading
        fwd = (U * 0.985 + L * sgn * 0.035 - F * 0.08).normalized()      # parallel Superman line
        dr = 0.02 * math.sin(TAU * t / 1.5 + (0 if sgn > 0 else 1.3))
        aim(side + '_collar', (L * sgn * 0.95 + U * (0.12 * (1 - c)) + F * 0.05 * c).normalized())
        aim(side + '_shoulder', (up_c * c + fwd * (1 - c) + L * sgn * dr).normalized())
        aim(side + '_elbow', (fo_c * c + fwd * (1 - c)).normalized())
        aim(side + '_wrist', (fo_c * c + fwd * (1 - c) - F * 0.05 * c).normalized())
    # owner: pencil-straight on the release -- after the deepest tuck the legs open straight back into the line (no kick-up)
    if i >= PEAK:
        k = ease((1 - c) * 1.15)
        for side, sgn in (('left', 1), ('right', -1)):
            th_take, sh_take, an_take = limb(side + '_hip'), limb(side + '_knee'), limb(side + '_ankle')
            th_s = (-U - L * sgn * 0.03).normalized(); sh_s = (-U - F * 0.04).normalized(); an_s = (-U * 0.96 + F * 0.27).normalized()
            aim(side + '_hip', (th_take * (1 - k) + th_s * k).normalized())
            aim(side + '_knee', (sh_take * (1 - k) + sh_s * k).normalized())
            aim(side + '_ankle', (an_take * (1 - k) + an_s * k).normalized())
    fists()
    for p in pb:
        p.keyframe_insert('rotation_quaternion', frame=i)
        if p.name == 'pelvis': p.keyframe_insert('location', frame=i)
tr = arm.animation_data.nla_tracks.new(); tr.name = out.name; tr.strips.new(out.name, 0, out); arm.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('BOOST3_OK', len(frames), OUT)
