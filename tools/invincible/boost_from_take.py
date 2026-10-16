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
    if n.endswith('_wrist'):   # the wrist's first child is the THUMB: the hand's real direction is wrist -> middle knuckle
        return ((AW @ pb[n.replace('_wrist', '_middle1')].head) - (AW @ pb[n].head)).normalized()
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
REST_W = {}
def fists():
    """fist that is verified, not guessed: try the six rest-frame directions (carried through the wrist's current swing) as the palm
    normal, curl the fingers into each, keep the one whose fingertips end closest to the palm (the tightest fist)"""
    for side, sgn in (('left', 1), ('right', -1)):
        w = side + '_wrist'
        if w not in REST_W: REST_W[w] = (AW @ arm.data.bones[w].matrix_local).to_quaternion()
        names = ['%s_%s%d' % (side, fn, j) for fn in FINGERS for j in (1, 2, 3)] + ['%s_thumb%d' % (side, j) for j in (1, 2, 3)]
        names = [n for n in names if n in pb]
        base = {n: pb[n].matrix_basis.copy() for n in names}
        swing = world(w).to_quaternion() @ REST_W[w].inverted()
        def tips():
            tot = 0.0; palm = (AW @ pb[side + '_middle1'].head)
            for fn in FINGERS:
                n3 = '%s_%s3' % (side, fn)
                if n3 in pb: tot += ((AW @ pb[n3].tail) - palm).length
            return tot
        def curl(nrm):
            for n in names: pb[n].matrix_basis = base[n]
            bpy.context.view_layer.update()
            for fn in FINGERS:
                for j, deg in ((1, 80), (2, 95), (3, 75)):
                    b = '%s_%s%d' % (side, fn, j)
                    if b in pb:
                        ax = limb(b).cross(nrm)
                        if ax.length > 1e-4: turn(b, ax, deg)
            for j, deg in ((1, 15), (2, 30), (3, 25)):
                b = '%s_thumb%d' % (side, j)
                if b in pb:
                    ax = limb(b).cross(nrm)
                    if ax.length > 1e-4: turn(b, ax, deg)
        best = None
        for cand in (-LEFT * sgn, LEFT * sgn, FWD, -FWD, UP, -UP):
            nrm = (swing @ cand).normalized(); curl(nrm); d = tips()
            if best is None or d < best[0]: best = (d, nrm)
        curl(best[1])

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
    # owner round 4: no hip weave/bank (read as hip shaking) -- the body's motion comes from the coil itself
    FLEX = U.cross(F)                                                                          # rotating U toward F = curling toward the belly
    for n, k in (('spine1', 0.25), ('spine2', 0.40), ('spine3', 0.35)):
        m = world(n); setw(n, Matrix.LocRotScale(m.to_translation(), q_flat @ REST[n], m.to_scale()))
        bpy.context.view_layer.update()
        turn(n, FLEX, 38.0 * k * c - 7.0 * k * (1 - c))                                       # back curls INTO the coil, arches open on the burst
    # head/neck SOLVED (owner: face straight up the flight line): face -> U (flight direction), top of head -> world up (-F);
    # the neck takes ~45 % of the bend from the straight body, the head the rest
    B_rest = Matrix((FWD, LEFT, UP)).transposed(); B_tgt = Matrix((U, L, (-F))).transposed()
    R = (B_tgt @ B_rest.inverted()).to_quaternion()
    for n, w in (('neck', 0.45), ('head', 1.0)):
        q_body = q_flat @ REST[n]; q_look = R @ REST[n]
        m = world(n); setw(n, Matrix.LocRotScale(m.to_translation(), q_body.slerp(q_look, w), m.to_scale()))
    # arms: coil = elbows bent and drawn back toward the hips, fists chambered at the ribs, knuckles forward (half punch);
    #       burst = swing forward into the parallel Superman line. Collars stay near natural (no big shoulder roll).
    # owner round 5: no rotator-cuff / elbow / wrist roll on the extension -- the take's arm twist is discarded: the whole arm chain
    # restarts from the rig's rest orientation each frame, so the aims below add pure swings (no roll about the limb)
    for p in pb:
        if any(p.name.startswith(sd + '_') and not p.name.endswith(('_hip', '_knee', '_ankle', '_foot')) for sd in ('left', 'right')):
            p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for side, sgn in (('left', 1), ('right', -1)):
        up_c = (-U * 0.80 + F * 0.42 + L * sgn * 0.30).normalized()      # upper arm back toward the hip, a little out and belly-side
        fo_c = (U * 0.88 + F * 0.38 - L * sgn * 0.12).normalized()       # forearm forward: fist by the ribs, knuckles leading
        fwd = (U * 0.985 + L * sgn * 0.035 - F * 0.08).normalized()      # parallel Superman line
        dr = 0.0
        aim(side + '_collar', (L * sgn * 0.80 + U * (0.15 * (1 - c) - 0.10 * c) + F * 0.45 * c).normalized())   # shoulders hunch forward/down into the coil, reach on the burst
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
