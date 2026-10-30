# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# The parts of the Hulk project's tools/brute/anim_lib.py (2026-10-30) that refine_hero.py needs, copied (not imported) and mapped
# onto the hero rig's SMPL-style bone names: rig state binding, per-frame WORLD bone rotations + root head sampling, forward
# kinematics from world rotations, pose rebuild with overridden bones, analytic 2-bone leg IK, and the foot plant segmentation.
# The algorithms are unchanged; the changes are the bone names (bn()), and one optional floor guard on plant_targets (see there).
# Positions are fit-scene WORLD metres (the armature object's 0.01 scale is inside S['W'] / S['RH']).
#   import from a Blender script:  sys.path.insert(0, os.path.dirname(__file__)); import anim_lib_hero as L
import math

import bpy
from mathutils import Vector

ROOT = 'pelvis'
UP = Vector((0, 0, 1))
S = {}   # rig state

# Brute (Mixamo) role -> hero bone suffix. The hero's "foot/ankle" role is <side>_ankle, the "toe" role (ball joint) is <side>_foot.
ROLE = {'UpLeg': 'hip', 'Leg': 'knee', 'Foot': 'ankle', 'ToeBase': 'foot',
        'Shoulder': 'collar', 'Arm': 'shoulder', 'ForeArm': 'elbow', 'Hand': 'wrist'}
FINGERS = tuple('%s%d' % (f, k) for f in ('thumb', 'index', 'middle', 'ring', 'pinky') for k in (1, 2, 3))
HEAD, NECK = 'head', 'neck'


def bn(side, role):
    """bn('Left', 'Foot') -> 'left_ankle'; side is 'Left' / 'Right' (the report keys), role a Brute role name or a hero suffix"""
    return '%s_%s' % (side.lower(), ROLE.get(role, role))


def bind(arm, act):
    """use an armature already in the scene with `act` assigned"""
    W = arm.matrix_world
    order = sorted(arm.data.bones, key=lambda b: len(b.parent_recursive))
    S.update(sc=bpy.context.scene, arm=arm, act=act, W=W.copy(), Wqi=W.to_quaternion().inverted(), order=order,
             RQ={b.name: (W @ b.matrix_local).to_quaternion() for b in arm.data.bones},
             RH={b.name: W @ b.head_local for b in arm.data.bones},
             tR={b.name: b.matrix_local.to_quaternion() for b in arm.data.bones},
             PAR={b.name: (b.parent.name if b.parent else None) for b in arm.data.bones})
    S['f0'], S['f1'] = (int(round(x)) for x in act.frame_range)


def sample(f):
    sc, arm, W = S['sc'], S['arm'], S['W']
    fi = int(math.floor(f)); sc.frame_set(fi, subframe=f - fi)
    return ({b.name: (W @ arm.pose.bones[b.name].matrix).to_quaternion() for b in S['order']}, (W @ arm.pose.bones[ROOT].head).copy())


def fk(world, rh):
    RQ, RH, PAR = S['RQ'], S['RH'], S['PAR']; pos = {}
    for b in S['order']:
        p = PAR[b.name]
        pos[b.name] = rh.copy() if p is None else pos[p] + (world[p] @ RQ[p].inverted()) @ (RH[b.name] - RH[p])
    return pos


def rebuild(ws, over):
    """world rotations top-down: overridden bones absolute, others keep their parent-relative rotation from ws"""
    out = {}; PAR = S['PAR']
    for b in S['order']:
        n = b.name; p = PAR[n]
        out[n] = over[n] if n in over else (ws[n] if p is None else out[p] @ (ws[p].inverted() @ ws[n]))
    return out


def smooth(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi


def ik2(A, K, T, l1=None, l2=None, pole=None):
    """2-bone IK: shoulder/hip A, current mid joint K (pole side), target T -> new mid joint, reached end"""
    l1 = l1 or (K - A).length; l2 = l2 or (T - K).length
    dv = T - A; d = min(dv.length, (l1 + l2) * 0.9995); u = dv.normalized()
    pl = (pole if pole is not None else (K - A)); pl = pl - pl.dot(u) * u
    pl = pl.normalized() if pl.length > 1e-6 else UP.cross(u).normalized()
    ca = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    return A + l1 * (ca * u + math.sqrt(max(0.0, 1 - ca * ca)) * pl), A + u * d


def leg_ik(world, rh, side, foot_target, foot_rot=None, pole=None):
    """re-solve hip/knee so the ankle (bn(side,'Foot') head) reaches foot_target; the ankle bone keeps world rotation foot_rot (or its own)"""
    pos = fk(world, rh); RH = S['RH']
    up_, lo_, ft_, toe_ = bn(side, 'UpLeg'), bn(side, 'Leg'), bn(side, 'Foot'), bn(side, 'ToeBase')
    A, K, T = pos[up_], pos[lo_], pos[ft_]
    l1 = (RH[lo_] - RH[up_]).length; l2 = (RH[ft_] - RH[lo_]).length
    K2, T2 = ik2(A, K, foot_target, l1, l2, pole if pole is not None else (K - A) - (K - A).dot((T - A).normalized()) * (T - A).normalized())
    over = {}
    up = (K - A).rotation_difference(K2 - A) @ world[up_]
    w2 = rebuild(world, {up_: up}); p2 = fk(w2, rh)
    lo = (p2[ft_] - p2[lo_]).rotation_difference(T2 - K2) @ w2[lo_]
    over[up_] = up; over[lo_] = lo
    over[ft_] = foot_rot if foot_rot is not None else world[ft_]
    # keep the toes' world rotation too
    for c in (toe_,):
        if c in world: over[c] = world[c] if foot_rot is None else foot_rot @ (world[ft_].inverted() @ world[c])
    return over


def leg_len(side='Left'):
    RH = S['RH']; return (RH[bn(side, 'Leg')] - RH[bn(side, 'UpLeg')]).length + (RH[bn(side, 'Foot')] - RH[bn(side, 'Leg')]).length


def plant_targets(frames, side, h_k=0.07, v_k=0.025, min_len=3, blend=3, keep=None, floor=None, floor_tol=0.0, report=None):
    """foot lock targets: frames where the foot is near its lowest height and barely moving are grouped into plants; each plant's
    ankle is pinned (xy) to the plant's average, blending in/out over `blend` frames. Returns per-frame ankle targets (or None).
    Hero addition (off with floor_tol <= 0, the Brute behaviour): a sample can only be on the ground when its toe or ankle joint
    is within floor_tol of `floor` too (the "lowest height" test is relative to the clip, so a take whose feet never touch the floor,
    e.g. a flight clip refined without --no-plant, would otherwise plant in the air). `report` (dict) receives the guard's counts."""
    l = leg_len(side); n = len(frames)
    P = [fk(w, rh) for w, rh in frames]
    ank = [p[bn(side, 'Foot')] for p in P]; toe = [p[bn(side, 'ToeBase')] for p in P]
    zt = min(t.z for t in toe); za = min(a.z for a in ank)
    # on the ground = toe or ankle near its lowest height (a planted foot that slides in the take is still planted: it gets pinned);
    # short lifts (<= 4 frames, foot stays below 2x the threshold) are a shuffle / slide in the take and are merged into one plant
    low = [toe[i].z < zt + h_k * l or ank[i].z < za + h_k * l for i in range(n)]
    lowish = [toe[i].z < zt + 2 * h_k * l or ank[i].z < za + 2 * h_k * l for i in range(n)]
    if floor is not None and floor_tol > 0:
        near = [min(toe[i].z, ank[i].z) - floor < floor_tol for i in range(n)]
        if report is not None:
            report.update(floor=floor, floor_tol=floor_tol, low_samples=int(sum(low)),
                          removed_off_floor=int(sum(1 for i in range(n) if low[i] and not near[i])))
        low = [low[i] and near[i] for i in range(n)]
        lowish = [lowish[i] and near[i] for i in range(n)]
    planted = list(low); i = 0
    while i < n:
        if not planted[i]:
            j = i
            while j + 1 < n and not planted[j + 1]: j += 1
            if 0 < i and j < n - 1 and j - i + 1 <= 4 and all(lowish[i:j + 1]):
                for k in range(i, j + 1): planted[k] = True
            i = j + 1
        else: i += 1
    if keep:   # forced plant frame ranges [(a, b)]
        for a_, b_ in keep:
            for i in range(max(0, a_), min(n, b_ + 1)): planted[i] = True
    segs = []; i = 0
    while i < n:
        if planted[i]:
            j = i
            while j + 1 < n and planted[j + 1]: j += 1
            if j - i + 1 >= min_len: segs.append((i, j))
            i = j + 1
        else: i += 1
    tgt = [None] * n; wts = [0.0] * n
    for a_, b_ in segs:
        c = sum((ank[i] for i in range(a_, b_ + 1)), Vector()) / (b_ - a_ + 1)
        for i in range(max(0, a_ - blend), min(n, b_ + blend + 1)):
            w = 1.0 if a_ <= i <= b_ else smooth(1 - (a_ - i) / (blend + 1)) if i < a_ else smooth(1 - (i - b_) / (blend + 1))
            if w > wts[i]:
                wts[i] = w; tgt[i] = Vector((ank[i].x + (c.x - ank[i].x) * w, ank[i].y + (c.y - ank[i].y) * w, ank[i].z))
    return tgt, segs
