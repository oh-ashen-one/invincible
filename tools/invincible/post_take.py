# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Owner rules (learned on hover / flight / boost, 2026-10-15) applied to any retargeted Meshy take:
#   * arms keep the take's DIRECTIONS but lose its roll (no rotator-cuff / elbow / wrist twist): chain restarts from rest, pure swings
#   * real fists (palm normal chosen by the tightest curl, not guessed)
#   * head straight: no yaw/roll; face solved to a target direction (forward horizon, or the flight line, or kept for landings)
#   * optional: start from the approved horizontal flight pose (--flat-in N frames), trim (--trim a:b), hold the last pose (--hold N)
# usage: Blender -b --factory-startup -P post_take.py -- <in.glb> <take action> <out.glb> <clip name> [--trim a:b] [--flat-in N]
#        [--head forward|up|keep] [--hold N]
import bpy, sys, math, argparse
from mathutils import Vector, Matrix, Quaternion

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('take'); ap.add_argument('out'); ap.add_argument('name')
ap.add_argument('--trim', default=''); ap.add_argument('--flat-in', type=int, default=0); ap.add_argument('--head', default='forward')
ap.add_argument('--hold', type=int, default=0)
ap.add_argument('--fps', type=int, default=24)   # import frame rate: the glTF importer counts keys at the scene fps (24 = how the brake/land/takeoff clips were built; 30 keeps a 30 fps source's exact timing)
ap.add_argument('--end-blend', default='')     # <glb>:<action>:<frames> -- blend the last N frames into that clip's first frame (local poses, same rig)
ap.add_argument('--head-after', type=int, default=-1)
ap.add_argument('--free-arm-back', action='store_true')   # landing: an arm pointing up gets swept back + out (classic three-point landing)   # with --head keep: from this frame on, blend the head to the forward horizon
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps = A.fps; bpy.ops.import_scene.gltf(filepath=A.src)
sc = bpy.context.scene; sc.render.fps = 30
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o)
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); AW = arm.matrix_world; pb = arm.pose.bones
def rest_head(n): return AW @ arm.data.bones[n].head_local
UP = Vector((0, 0, 1))
FWD = rest_head('left_foot') - rest_head('left_ankle'); FWD.z = 0; FWD.normalize()
LEFT = rest_head('left_hip') - rest_head('right_hip'); LEFT.z = 0; LEFT.normalize()
def world(n): return AW @ pb[n].matrix
def limb(n):
    b = arm.data.bones[n]
    if n.endswith('_wrist'): return ((AW @ pb[n.replace('_wrist', '_middle1')].head) - (AW @ pb[n].head)).normalized()
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
REST_Q = {b.name: (AW @ b.matrix_local).to_quaternion() for b in arm.data.bones}
ARM_CHAIN = [s + '_' + n for s in ('left', 'right') for n in ('collar', 'shoulder', 'elbow', 'wrist')]
HAND = [p.name for p in pb if any(p.name.startswith(s + '_') for s in ('left', 'right')) and any(k in p.name for k in FINGERS + ['thumb'])]

def fists():
    for side, sgn in (('left', 1), ('right', -1)):
        w = side + '_wrist'; names = [n for n in HAND if n.startswith(side + '_')]
        base = {n: pb[n].matrix_basis.copy() for n in names}
        swing = world(w).to_quaternion() @ REST_Q[w].inverted()
        def tips():
            palm = AW @ pb[side + '_middle1'].head
            return sum(((AW @ pb['%s_%s3' % (side, fn)].tail) - palm).length for fn in FINGERS if '%s_%s3' % (side, fn) in pb)
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

def solve_head(face, top, neck_w=0.45):
    """orient head (and neck partly): face -> face, top -> top (no yaw/roll beyond that); the chest frame is left as the take has it"""
    top = (top - face * top.dot(face)).normalized()
    B_rest = Matrix((FWD, LEFT, UP)).transposed(); B_tgt = Matrix((face, top.cross(face).normalized(), top)).transposed()
    R = (B_tgt @ B_rest.inverted()).to_quaternion()
    for n, w in (('neck', neck_w), ('head', 1.0)):
        m = world(n); q_now = m.to_quaternion(); q_look = R @ REST_Q[n]
        setw(n, Matrix.LocRotScale(m.to_translation(), q_now.slerp(q_look, w), m.to_scale()))

# sample the take
act = bpy.data.actions[A.take]; arm.animation_data_create(); arm.animation_data.action = act
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
if A.trim: a_, b_ = [int(x) for x in A.trim.split(':')]; f0, f1 = f0 + a_, min(f1, f0 + b_)
frames = []
for f in range(f0, f1 + 1):
    sc.frame_set(f); frames.append({p.name: p.matrix_basis.copy() for p in pb})
arm.animation_data.action = None
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
if A.hold: frames += [frames[-1]] * A.hold
END = None
if A.end_blend:                                        # sample the target clip's first frame on its own armature (same rig, same rest)
    glb, act_name, nb = A.end_blend.split(':'); nb = int(nb)
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]; arm2 = next(o for o in new if o.type == 'ARMATURE')
    arm2.animation_data_create(); arm2.animation_data.action = bpy.data.actions[act_name]; sc.frame_set(0)
    END = ({p.name: p.matrix_basis.copy() for p in arm2.pose.bones}, nb)
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        if a.name == act_name: bpy.data.actions.remove(a)
q_flat = UP.rotation_difference(FWD)
def ease(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

out = bpy.data.actions.new(A.name); arm.animation_data.action = out
for p in pb: p.rotation_mode = 'QUATERNION'
for i, basis in enumerate(frames):
    for p in pb: p.matrix_basis = basis[p.name]
    if END and i >= len(frames) - END[1]:              # hand off into the target clip's first pose
        k = ease((i - (len(frames) - END[1])) / max(1, END[1] - 1))
        for p in pb:
            a_, b_ = basis[p.name], END[0].get(p.name, basis[p.name])
            q = a_.to_quaternion().slerp(b_.to_quaternion(), k); t = a_.to_translation().lerp(b_.to_translation(), k)
            p.matrix_basis = Matrix.LocRotScale(t, q, Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    if A.flat_in and i < A.flat_in:                   # start from the horizontal flight line, swing into the take
        k = ease(i / A.flat_in); m = world('pelvis'); q_take = m.to_quaternion(); q_fl = q_flat @ REST_Q['pelvis']
        setw('pelvis', Matrix.LocRotScale(m.to_translation(), q_fl.slerp(q_take, k), m.to_scale()))
    # untwist: remember each arm bone's direction, restart the chain from rest, re-aim (pure swings)
    dirs = {n: limb(n) for n in ARM_CHAIN}
    for n in ARM_CHAIN + HAND: pb[n].matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    if A.free_arm_back:
        for sd, sgn in (('left', 1), ('right', -1)):
            for n in (sd + '_shoulder', sd + '_elbow', sd + '_wrist'):
                u = dirs[n].dot(UP)
                if u > 0.35:
                    k = ease((u - 0.35) / 0.4)
                    tgt = (-FWD * 0.72 + LEFT * sgn * 0.50 + UP * 0.48).normalized()
                    dirs[n] = (dirs[n] * (1 - k) + tgt * k).normalized()
    for n in ARM_CHAIN: aim(n, dirs[n])
    fists()
    if A.head == 'keep' and A.head_after >= 0 and i >= A.head_after:
        k = ease((i - A.head_after) / 12.0); m_n, m_h = world('neck').to_quaternion(), world('head').to_quaternion()
        solve_head(FWD, UP)
        for n, q0 in (('neck', m_n), ('head', m_h)):
            m = world(n); setw(n, Matrix.LocRotScale(m.to_translation(), q0.slerp(m.to_quaternion(), k), m.to_scale()))
    if A.head != 'keep':
        chest_up = limb('spine3')
        if A.head == 'up':                            # rising takeoff: chin up toward the sky, still straight (no yaw/roll)
            solve_head((FWD * 0.75 + UP * 0.66).normalized(), (UP * 0.6 - FWD * 0.8).normalized())
        else:                                         # forward horizon; top of head follows the chest (lean) without roll
            solve_head(FWD, chest_up if chest_up.dot(UP) > 0.2 else UP)
    for p in pb:
        p.keyframe_insert('rotation_quaternion', frame=i)
        if p.name == 'pelvis': p.keyframe_insert('location', frame=i)
tr = arm.animation_data.nla_tracks.new(); tr.name = out.name; tr.strips.new(out.name, 0, out); arm.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=A.out, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('POST_OK', A.name, len(frames), A.out)
