# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. Copied unchanged from the Hulk project (tools/brute/v2r/v2r_rig.py, 2026-10-30); the SHIPPED_RIG / ALIGNED_BLEND constants are the Brute's and unused here.
# Shared helpers for the Brute video2rig Blender tools (export_clip.py, refine_brute.py, make_test_fit.py). Runs inside Blender.
#
# Two rigs carry the same 52 Mixamo-named bones with identical heads and hierarchy but different REST orientations:
#   SHIPPED  ~/hulk-scratch/brute_corr/brute_rigged_corr.glb (what assemble_motion.py and the game use; glTF-import bone tails)
#   ALIGNED  ~/hulk/Local/video2rig/brute-aligned/model.blend (tails re-pointed at the child head, see brute-aligned/align.py;
#            video2rig fits on it because its hinge / bend-axis / flat-foot logic reads bone tails)
# A pose is moved between them in ARMATURE space: for every bone b with rest matrices R_src[b], R_dst[b] (bone.matrix_local)
# and an armature-space pose matrix P_src[b] (pose_bone.matrix), the same deformation D = P R^-1 needs
#     P_dst[b] = P_src[b] @ R_src[b]^-1 @ R_dst[b]
# and the destination pose basis (what is keyed) is, parent-aware,
#     basis[b] = (R_dst[parent]^-1 R_dst[b])^-1 @ P_dst[parent]^-1 @ P_dst[b]      (root: R_dst[b]^-1 @ P_dst[b])
# Same transform both ways (src/dst swap): shipped -> aligned for the synthetic test fit, aligned -> shipped for export.
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

SHIPPED_RIG = '/Users/midir/hulk-scratch/brute_corr/brute_rigged_corr.glb'
ALIGNED_BLEND = '/Users/midir/hulk/Local/video2rig/brute-aligned/model.blend'


# ------------------------------------------------------------------ actions (Blender 4.x and 5.x slotted actions)
def action_fcurves(act):
    fc = getattr(act, 'fcurves', None)
    if fc is not None:
        return list(fc)
    return [f for L in getattr(act, 'layers', ()) for st in L.strips for cb in getattr(st, 'channelbags', ()) for f in cb.fcurves]


def assign_action(obj, act):
    obj.animation_data_create()
    obj.animation_data.action = act
    if act is not None and hasattr(act, 'slots') and len(act.slots) and hasattr(obj.animation_data, 'action_slot'):
        try:
            obj.animation_data.action_slot = act.slots[0]
        except Exception as ex:  # noqa
            print('v2r_rig: slot assign failed', ex)


def key_range(act):
    """first / last key frame over all F-curves (floats; import_motion keys can sit between integer frames)"""
    xs = [kp.co.x for fc in action_fcurves(act) for kp in fc.keyframe_points]
    return (min(xs), max(xs)) if xs else (0.0, 0.0)


def keyed_bones(act):
    out = {}
    for fc in action_fcurves(act):
        p = fc.data_path
        if p.startswith('pose.bones["'):
            b = p.split('"')[1]
            out.setdefault(b, set()).add(p.rsplit('.', 1)[1])
    return out


# ------------------------------------------------------------------ rig description
def rest(arm):
    return {b.name: b.matrix_local.copy() for b in arm.data.bones}


def parents(arm):
    return {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}


def order(arm):
    return [b.name for b in sorted(arm.data.bones, key=lambda b: len(b.parent_recursive))]


def check_match(arm_a, arm_b, tol=1e-4):
    """same bone names, same parents, same heads (armature space, metres of armature space). Returns (ok, lines)."""
    A, B = {b.name: b for b in arm_a.data.bones}, {b.name: b for b in arm_b.data.bones}
    lines, ok = [], True
    if set(A) != set(B):
        ok = False
        lines.append('bone names differ: only in %s %s; only in %s %s' % (arm_a.name, sorted(set(A) - set(B))[:10], arm_b.name, sorted(set(B) - set(A))[:10]))
    common = sorted(set(A) & set(B))
    par = [n for n in common if (A[n].parent.name if A[n].parent else None) != (B[n].parent.name if B[n].parent else None)]
    if par:
        ok = False
        lines.append('parents differ for %s' % par[:10])
    dh = max(((A[n].head_local - B[n].head_local).length, n) for n in common)
    if dh[0] > tol:
        ok = False
    lines.append('bones %d, max head delta %.3g (bone %s), tol %.0e' % (len(common), dh[0], dh[1], tol))
    return ok, lines


# ------------------------------------------------------------------ the transform
def sample_pose(arm):
    """armature-space pose matrices of every bone at the current (already set) frame"""
    return {pb.name: pb.matrix.copy() for pb in arm.pose.bones}


def convert_pose(P_src, R_src, R_dst):
    return {n: P_src[n] @ R_src[n].inverted() @ R_dst[n] for n in R_dst}


def basis_from_pose(P, R, PAR):
    out = {}
    for n, p in PAR.items():
        if p is None:
            out[n] = R[n].inverted() @ P[n]
        else:
            out[n] = (R[p].inverted() @ R[n]).inverted() @ P[p].inverted() @ P[n]
    return out


def retarget_basis(P_src, R_src, R_dst, PAR_dst):
    """armature-space source pose -> destination pose-basis matrices (one frame)"""
    return basis_from_pose(convert_pose(P_src, R_src, R_dst), R_dst, PAR_dst)


# ------------------------------------------------------------------ writing keys fast
def write_basis_frames(arm, act, frames, bases, loc_bones=None, loc_tol=1e-5):
    """key one pose-basis matrix per bone per frame (rotation_quaternion for every bone; location only for bones whose
    translation leaves loc_tol, or the bones in loc_bones). Linear keys, quaternion hemisphere kept continuous.
    frames: list of frame numbers; bases: list of {bone: Matrix}. Returns the bones that got location keys."""
    names = list(bases[0])
    quats = {n: [] for n in names}
    locs = {n: [] for n in names}
    for B in bases:
        for n in names:
            l, q, s = B[n].decompose()
            quats[n].append(q)
            locs[n].append(l)
    for n in names:  # hemisphere continuity
        for i in range(1, len(quats[n])):
            if quats[n][i].dot(quats[n][i - 1]) < 0:
                quats[n][i] = -quats[n][i]
    if loc_bones is None:
        loc_bones = [n for n in names if max(v.length for v in locs[n]) > loc_tol or arm.data.bones[n].parent is None]
    assign_action(arm, act)
    for n in names:  # create the F-curves with one key, then overwrite in bulk
        pb = arm.pose.bones[n]
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = quats[n][0]
        pb.keyframe_insert('rotation_quaternion', frame=frames[0])
        if n in loc_bones:
            pb.location = locs[n][0]
            pb.keyframe_insert('location', frame=frames[0])
    fcmap = {(fc.data_path, fc.array_index): fc for fc in action_fcurves(act)}
    F = np.asarray(frames, dtype=np.float64)
    for n in names:
        chans = [('rotation_quaternion', 4, quats[n])] + ([('location', 3, locs[n])] if n in loc_bones else [])
        for prop, k, vals in chans:
            for i in range(k):
                fc = fcmap[('pose.bones["%s"].%s' % (n, prop), i)]
                fc.keyframe_points.clear()
                fc.keyframe_points.add(len(F))
                co = np.empty(2 * len(F))
                co[0::2] = F
                co[1::2] = [v[i] for v in vals]
                fc.keyframe_points.foreach_set('co', co)
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
                fc.update()
    return loc_bones


# ------------------------------------------------------------------ evaluation helpers
def set_frame(f):
    sc = bpy.context.scene
    fi = int(np.floor(f + 1e-9))
    sc.frame_set(fi, subframe=float(f - fi))


def mesh_world(mesh_obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh_obj.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    M = np.array(mesh_obj.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]
