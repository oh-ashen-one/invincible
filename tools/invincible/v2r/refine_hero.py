# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# Scripted Blender pass on a raw video2rig fit of the HERO (project rig .blend from the video2rig fork's import_motion.py: armature
# scaled 0.01, SMPL-style bone names, one Action keyed at the scene fps): a fit is a base, never a deliverable. Port of the Hulk
# project's tools/brute/v2r/refine_brute.py (2026-10-30, 1012 lines) with its anim_lib parts copied into anim_lib_hero.py.
# Same algorithms, defaults, CLI and outputs; the changes for the hero:
#   bone names   Hips -> pelvis; LeftUpLeg/LeftLeg/LeftFoot/LeftToeBase -> left_hip/left_knee/left_ankle/left_foot (the "toe" role is
#                left_foot, the ankle/foot role left_ankle); LeftShoulder/LeftArm/LeftForeArm/LeftHand -> left_collar/left_shoulder/
#                left_elbow/left_wrist; Neck/Head -> neck/head (anim_lib_hero.bn). The 15 finger bones per hand join the arm bones in the
#                untouched-arms proof (they are never edited either). JSON / log keys stay 'Left' / 'Right'.
#   units        every position is fit-scene WORLD metres (the 0.01 object scale is folded in by FK / mesh_world); mm = world m x 1000.
#                Fix vs the Brute: feet.treadmill.speed_m_s_world no longer multiplies the (already world) speed by the object scale.
#   floor        world z = 0 (--floor). New --plant-floor-tol M (default 0.25; 0 = the Brute behaviour): a sample can only be planted when
#                its ball (left_foot head) or ankle joint is within M of the floor; the Brute's test is relative to the clip's own
#                lowest foot height, which plants an airborne foot (flight clips belong on --no-plant anyway).
#   channels     the project rig's GLB-born fits also key scale (and location on every bone): location is refined like the root's;
#                constant identity scale F-curves are dropped (the game export keys rotation + root location only), any other
#                non-rotation/location pose channel is kept but cut to the refined key range (reported in channels_other).
#   output       the saved .blend holds ONE Action (the refined one, active on the armature); any other Action is removed.
#   dropped      nothing: refine_brute.py itself has no corrective-morph or posture code (no Brute-only step to drop or map).
#
#   Blender -b --factory-startup -P tools/invincible/v2r/refine_hero.py -- <fit.blend> [options]
#     --loop                 close the loop: end on the best-matching frame within --loop-win s of the end, offset-blend the last N
#                            frames so the end pose equals frame 0 (velocities stay continuous); N auto 12-24 (--xfade N to force)
#     --return-to-stance     one-shot: blend the end back onto frame 0 (the start-picture stance) over --return-frames (24-36, def 30)
#     --keep-travel          with --return-to-stance: leave the pelvis' horizontal position alone (moves that travel)
#     --trim THR             trim the still tail: trailing samples whose 9-sample mean rotation step < THR x median (default 0.4;
#                            --trim 0 turns it off); never below half the clip
#     --no-plant             skip the foot plant (IK bake while a foot is grounded) and the toe clamp
#     --window A B           keep only fit samples A..B (inclusive, 0-based on the fit's key grid) before anything else, re-keyed to
#                            start on the fit's first key: a loop cut from the steady stride (a walk that starts from and ends in the
#                            stance has no steady cycle at its ends); trim / loop then work inside the window
#     --treadmill            in-place locomotion (Walk / Run, the game moves the capsule): planted feet are pinned in a ground frame
#                            that slides backward at ONE constant velocity (the median planted-toe velocity of the take), so they slide
#                            evenly at the walk speed instead of being nailed under hips that never travel; foot_drift_mm is then
#                            measured in that sliding frame (the treadmill speed is reported in the JSON as feet.treadmill)
#     --floor Z              floor height in the fit scene (default 0.0: the project puts the floor at world z = 0)
#     --plant-floor-tol M    (hero) planting only where the ball or ankle joint is within M of --floor (default 0.25; 0 = off)
#     --max-lift M           the toe clamp lifts a foot by IK at most M metres (default 0.05); a deeper penetration means the whole
#                            body sits low (a floor / root mismatch, not a toe problem): it is capped and reported, never folded away
#     --spike-k K --spike-min-deg D   single-frame spike test: deviation from the neighbours' midpoint > K x the bone's median
#                            (default 4.0) and >= D deg (default 3), direction reverses, AND the in/out steps are > --spike-iso x
#                            (default 3) the steps around them (isolated jitter; a fast extreme such as a punch snap is never touched)
#     --burst-k K --burst-min-deg D --burst-iso I --burst-max M --burst-ease-deg E   (2026-10-29, after the Throw fit)
#                            multi-sample burst test: a run of 1..M (default 4) consecutive steps, each > K x the bone's median step
#                            (default 8) and > D deg (default 30), whose smallest step is > I x (default 3) the largest of the 2 steps
#                            on either side. That is a solver reset landing in another twist branch (Throw LeftArm: 3/67/100/68/3 deg
#                            at frames 25-29, the upper arm's direction moving ~20 deg while its twist turns ~125 deg; the single-frame
#                            test cannot see it because the bone never comes back). The net change is KEPT but re-timed: the jump is
#                            removed, then re-added as a smoothstep offset over a window sized so its peak step is <= E deg (default 12,
#                            at least the burst + 2 samples, at most 0.5 s), centred on the burst; motion before/after is unchanged.
#                            Only twist-dominated bursts: the bone's length axis must move <= --burst-max-swing-deg (default 45)
#                            across the burst (Throw frame 27: ~20 deg; Throw's hurl at frames 98-101 moves the arms ~95 deg, real
#                            motion, reported in bursts.skipped_as_swing and left alone).
#                            --no-burst turns it off. Arms count these frames like spike frames in the untouched-arms proof.
#     --compress-holds       (2026-10-29, after the Blender blind A/B: one-shots read as dead pauses) with --return-to-stance only:
#                            find near-static spans (smoothed mean bone angular speed < clamp(--hold-frac (0.3) x the clip's p95 speed,
#                            --hold-min-dps, --hold-max-dps) for >= --hold-min-s) outside the contact windows (each hand's raw peak
#                            +- --contact-s), and re-time each one to at most --hold-keep samples (default 6) with a cosine-eased rate
#                            (the playback rate is unchanged at the hold's edges, fastest mid-hold). Holds with both hands above the
#                            Head keep --hold-keep-up samples instead (default = --hold-keep; Lift's overhead hold). If the clip is still
#                            longer than --max-seconds, all non-hold time is sped up uniformly (at most --max-speedup x). Hit times move
#                            and are re-measured (retime.hit in the JSON). Runs after spikes/bursts, before the return blend.
#                            The contact spans themselves play at real speed (eased into over 3 samples), so a strike keeps its own
#                            timing and weight while the wind-up/recovery speed up.
#     --return-target T      (hero) with --return-to-stance: frame0 (default, the Brute: blend the end onto frame 0) or stance (blend
#                            the end onto the --stance-rig start_pose: every bone's basis rotation + the location-keyed bones'
#                            translation; --keep-travel still keeps the pelvis x/y). For one-shots that do NOT start in the stance,
#                            e.g. A_LandHero (starts in a head-first dive, ends standing): frame0 would turn the standing end back into
#                            the dive. The seam is then measured last frame -> stance; --stance-snap snaps the end lift to 0.
#     --stance-yaw-align     (hero) with --return-target stance: first turn the stance's pelvis about world Z onto the clip end's
#                            facing (rig-stand/rig.json faces ~30 deg off -Y; A_LandHero ends facing -Y), so the return does not
#                            swing the whole body in the last frames. Turned angle in JSON return.stance_yaw_aligned_deg.
#     --stance-snap N        with --return-to-stance: the return blend already makes the last pose equal frame 0 before the plant;
#                            the toe clamp's smoothed lift could still differ at the two ends (Land: 16 mm end gap). This blends the
#                            lift of the last N samples onto frame 0's lift (never below what the toes need), so the last frame equals
#                            frame 0 and the toes stay above the floor (end-minus-start lift before/after in feet.stance_snap).
#                            Tried first and dropped: blending the leg rotations after the clamp (PunchL: drift 1 -> 8 mm, toe -1.3 mm).
#     --lock-yaw             (2026-10-30, after the Seedance straight punch: the whole body turns ~90 deg to profile and back) remove
#                            the root's (pelvis, creature.json root_bone) world yaw relative to frame 0 from every fit sample, before
#                            anything else, so the body keeps frame 0's facing all clip while every other bone keeps its parent-relative
#                            (body-relative) motion. Yaw = heading of the root's facing axis (creature.json facing, default -Y) and its
#                            lateral axis about world Z, weighted by their horizontal lengths (robust to a forward lean); pitch/roll are
#                            kept. The root's travel is kept body-relative: each step of the root location is turned by the yaw removed
#                            at that step (a lunge toward the turned body's front stays a lunge toward the locked front; keeping the
#                            world travel instead made the hips run sideways away from the planted foot: PunchR sd_v4 left toe drift
#                            36 mm, 13 IK misses). The plant then re-pins the feet. Removed range in JSON yaw_lock and on
#                            the REFINE_GATE line as `yaw_locked <deg span>` (max - min of the removed yaw).
#     --action NAME --clip NAME --out PATH.blend   (defaults: active action; clip = action name; <fit>_refined.blend beside input)
#     --stance-rig rig.json  the project rig.json whose start_pose is the start-picture stance (overlap check); default the
#                            HOVER pose Local/video2rig/hero/rig/rig.json, the standing stance is rig-stand/rig.json
#     --root-dz U            (2026-10-31) shift every root location key by U ARMATURE units up (armature space) before anything else:
#                            a fit from a project whose model sits at another height over its floor (hero-dive) onto the game floor.
# Writes <out>.blend and <out>.json; prints
#   REFINE_GATE <clip> seam x.xx foot_drift_mm X toe_min_mm X peakhand_L f peakhand_R f [yaw_locked D]   (D only with --lock-yaw)
#   seam  = rotation step across the loop wrap / median step (loop: last DISTINCT frame -> frame 0, the end frame equals frame 0 as in
#           assemble_motion; one-shot: last frame -> frame 0, i.e. how far the end is from the start stance)
#   foot_drift_mm = worst horizontal slide vs that plant's mean, after the plant: toe joint over every planted sample, ankle over the
#           heel-down samples (with the heel up the ankle legitimately swings around the ball)
#   toe_min_mm = lowest toe-region vertex over the clip, after the clamp (floor = 0)
#   peakhand_L/R = sample index of peak hand speed after refinement (seconds and 30 fps frame in the JSON)
# Arms/hands are only ever touched on detected single-frame spikes and inside the loop/return blend window; the JSON proves it.
# The input .blend is never written. Works on the fit's own key grid (no resampling: export_hero_clip.py does the one 30 fps resample).
import argparse
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v2r_rig as R  # noqa: E402
import anim_lib_hero as L  # noqa: E402  (copy of the Hulk anim_lib parts, hero bone names: FK, 2-bone leg IK, plant segmentation)

SIDES = ('Left', 'Right')
LEG = ('UpLeg', 'Leg', 'Foot', 'ToeBase')
ARM = ('Shoulder', 'Arm', 'ForeArm', 'Hand')
STANCE_RIG = '/Users/midir/spider-man-2-invincible/Local/video2rig/hero/rig/rig.json'   # the HOVER pose; standing: rig-stand/rig.json


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser(prog='refine_hero.py')
    ap.add_argument('blend')
    ap.add_argument('--loop', action='store_true')
    ap.add_argument('--return-to-stance', action='store_true')
    ap.add_argument('--keep-travel', action='store_true')
    ap.add_argument('--trim', type=float, default=0.4)
    ap.add_argument('--no-plant', action='store_true')
    ap.add_argument('--treadmill', action='store_true')
    ap.add_argument('--window', type=int, nargs=2, default=None, metavar=('A', 'B'))
    ap.add_argument('--floor', type=float, default=0.0)
    ap.add_argument('--plant-floor-tol', type=float, default=0.25)
    ap.add_argument('--max-lift', type=float, default=0.05)
    ap.add_argument('--loop-win', type=float, default=2.0)
    ap.add_argument('--xfade', type=int, default=0)
    ap.add_argument('--return-frames', type=int, default=30)
    ap.add_argument('--spike-k', type=float, default=4.0)
    ap.add_argument('--spike-min-deg', type=float, default=3.0)
    ap.add_argument('--spike-iso', type=float, default=3.0)
    ap.add_argument('--burst-k', type=float, default=8.0)
    ap.add_argument('--burst-min-deg', type=float, default=30.0)
    ap.add_argument('--burst-iso', type=float, default=3.0)
    ap.add_argument('--burst-max', type=int, default=4)
    ap.add_argument('--burst-ease-deg', type=float, default=12.0)
    ap.add_argument('--burst-max-swing-deg', type=float, default=45.0)
    ap.add_argument('--no-burst', action='store_true')
    ap.add_argument('--compress-holds', action='store_true')
    ap.add_argument('--hold-frac', type=float, default=0.3)
    ap.add_argument('--hold-min-dps', type=float, default=4.0)
    ap.add_argument('--hold-max-dps', type=float, default=8.0)
    ap.add_argument('--hold-min-s', type=float, default=0.25)
    ap.add_argument('--hold-keep', type=int, default=6)
    ap.add_argument('--hold-keep-up', type=int, default=0)
    ap.add_argument('--contact-s', type=float, default=0.1)
    ap.add_argument('--max-seconds', type=float, default=0.0)
    ap.add_argument('--max-speedup', type=float, default=1.6)
    ap.add_argument('--stance-snap', type=int, default=0)
    ap.add_argument('--return-target', choices=('frame0', 'stance'), default='frame0')
    ap.add_argument('--stance-yaw-align', action='store_true')
    ap.add_argument('--lock-yaw', action='store_true')
    ap.add_argument('--action', default='')
    ap.add_argument('--clip', default='')
    ap.add_argument('--out', default='')
    ap.add_argument('--stance-rig', default=STANCE_RIG)
    ap.add_argument('--root-dz', type=float, default=0.0)
    a = ap.parse_args(argv)
    if a.loop and a.return_to_stance:
        ap.error('--loop and --return-to-stance exclude each other')
    if (a.compress_holds or a.stance_snap) and not a.return_to_stance:
        ap.error('--compress-holds / --stance-snap need --return-to-stance')
    if a.return_target == 'stance' and not a.return_to_stance:
        ap.error('--return-target stance needs --return-to-stance')
    if a.stance_yaw_align and a.return_target != 'stance':
        ap.error('--stance-yaw-align needs --return-target stance')
    return a


# ------------------------------------------------------------------ small math
def qang(a, b):
    return 2.0 * math.acos(min(1.0, abs(float(np.dot(a, b)))))


def fix_hemi(q):
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    for i in range(1, len(q)):
        if np.dot(q[i], q[i - 1]) < 0:
            q[i] = -q[i]
    return q


def nlerp(a, b, w):
    b = b if np.dot(a, b) >= 0 else -b
    o = (1 - w) * a + w * b
    return o / np.linalg.norm(o)


def sstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def gauss1d(v, sig=1.5, hw=4):
    g = np.exp(-.5 * (np.arange(-hw, hw + 1) / sig) ** 2); g /= g.sum()
    return np.convolve(np.pad(v, hw, mode='edge'), g, mode='valid')


def r3(x):
    return None if x is None else round(float(x), 3)


AXES = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}


def facing_axis(blend):
    """creature.json `facing` ('-Y', '+X', ...) beside the fit .blend or up to three levels up (the video2rig project dir, e.g.
    Local/video2rig/hero/work/<take>/fit.blend); default -Y (the hero's)"""
    d0 = os.path.dirname(blend)
    for d in (d0, os.path.dirname(d0), os.path.dirname(os.path.dirname(d0)), os.path.dirname(os.path.dirname(os.path.dirname(d0)))):
        f = os.path.join(d, 'creature.json')
        if os.path.exists(f):
            s = str(json.load(open(f)).get('facing', '-Y')).strip().upper()
            v = Vector(AXES[s[-1]]) * (-1 if s.startswith('-') else 1)
            return v, s, f
    return Vector((0, -1, 0)), '-Y', None


def root_yaw(qs, Bq, F):
    """unwrapped world yaw (rad) of the root per sample, relative to the rest pose. qs: root basis quaternions (n, 4); Bq: the rest
    root's world rotation (world rotation = Bq @ basis); F: facing axis in world. Heading of the facing axis and of the lateral axis
    (Z x F), each weighted by its horizontal length, so a lean along either axis does not swing the estimate."""
    Lt = Vector((0, 0, 1)).cross(F)
    bi = Bq.inverted()
    y = []
    for q in qs:
        D = Bq @ Quaternion(q) @ bi
        sx = cx = 0.0
        for ax in (F, Lt):
            v = D @ ax
            wv = math.hypot(v.x, v.y)
            if wv < 1e-9:
                continue
            d = math.atan2(v.y, v.x) - math.atan2(ax.y, ax.x)
            sx += wv * math.sin(d); cx += wv * math.cos(d)
        y.append(math.atan2(sx, cx))
    return np.unwrap(np.array(y))


# ------------------------------------------------------------------ channels on the key grid
def read_channels(act, grid):
    ch = {}
    for fc in R.action_fcurves(act):
        p = fc.data_path
        if not p.startswith('pose.bones["'):
            continue
        b = p.split('"')[1]; prop = p.rsplit('.', 1)[1]
        kind = {'rotation_quaternion': 'q', 'location': 'l'}.get(prop)
        if kind is None:
            continue
        d = ch.setdefault(b, {})
        if kind not in d:
            d[kind] = np.zeros((len(grid), 4 if kind == 'q' else 3))
        d[kind][:, fc.array_index] = [fc.evaluate(x) for x in grid]
    for d in ch.values():
        if 'q' in d:
            d['q'] = fix_hemi(d['q'])
    return ch


def write_channels(arm, act, ch, grid):
    """replace every key of every channel in ch with one linear key per grid point; creates missing F-curves"""
    have = {(fc.data_path, fc.array_index): fc for fc in R.action_fcurves(act)}
    for b, d in ch.items():
        pb = arm.pose.bones[b]; pb.rotation_mode = 'QUATERNION'
        for kind, prop in (('q', 'rotation_quaternion'), ('l', 'location')):
            if kind in d and ('pose.bones["%s"].%s' % (b, prop), 0) not in have:
                pb.keyframe_insert(prop, frame=grid[0])
    have = {(fc.data_path, fc.array_index): fc for fc in R.action_fcurves(act)}
    G = np.asarray(grid, dtype=np.float64)
    for b, d in ch.items():
        for kind, prop, n in (('q', 'rotation_quaternion', 4), ('l', 'location', 3)):
            if kind not in d:
                continue
            for i in range(n):
                fc = have[('pose.bones["%s"].%s' % (b, prop), i)]
                fc.keyframe_points.clear(); fc.keyframe_points.add(len(G))
                co = np.empty(2 * len(G)); co[0::2] = G; co[1::2] = d[kind][:len(G), i]
                fc.keyframe_points.foreach_set('co', co)
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
                fc.update()


def steps(ch, n, bones):
    """per-step summed rotation (rad) over bones, length n-1"""
    s = np.zeros(max(0, n - 1))
    for b in bones:
        q = ch[b]['q']
        s += np.array([qang(q[i], q[i + 1]) for i in range(n - 1)])
    return s


def pose_dist(ch, i, j, bones):
    return float(sum(qang(ch[b]['q'][i], ch[b]['q'][j]) for b in bones))


def pose_dist_to(ch, i, tq, bones):
    """pose distance of sample i to a target pose {bone: quaternion} (hero: --return-target stance)"""
    return float(sum(qang(ch[b]['q'][i], tq[b]) for b in bones))


def resample(ch, t):
    """channels at fractional source sample times t (quaternions nlerp, locations linear)"""
    t = np.asarray(t, dtype=np.float64)
    out = {}
    for b, d in ch.items():
        n = len(next(iter(d.values())))
        i0 = np.clip(np.floor(t).astype(int), 0, n - 1); i1 = np.minimum(i0 + 1, n - 1); w = t - i0
        o = {}
        for k, v in d.items():
            if k == 'q':
                o[k] = fix_hemi(np.array([nlerp(v[i0[j]], v[i1[j]], w[j]) for j in range(len(t))]))
            else:
                o[k] = v[i0] * (1 - w)[:, None] + v[i1] * w[:, None]
        out[b] = o
    return out


def hold_warp(n, holds, f, contact=(), ramp=3.0, sub=16):
    """source time t (fractional samples) for each output sample. n: source samples. holds: list of (a, b, K) source sample spans
    re-timed to K output steps. Elsewhere the rate (output steps per source step) is 1/f, except inside the contact spans
    (list of (c0, c1)), which play at rate 1 (real speed), eased into over `ramp` samples on either side. Inside a hold the rate is
    base / (1 + A (1 - cos 2 pi u) / 2), u in 0..1 across it, A solved so the hold takes K output steps (rate continuous at the
    edges). Returns t_k (the last output sample lands exactly on the last source sample) and the solved A per hold."""
    ts = np.linspace(0.0, n - 1, (n - 1) * sub + 1)
    w = np.zeros(len(ts))
    for c0, c1 in contact:
        d = np.maximum(0.0, np.maximum(c0 - ts, ts - c1)) / ramp
        x = np.clip(1 - d, 0, 1)
        w = np.maximum(w, x * x * (3 - 2 * x))
    r = 1.0 / f + (1 - 1.0 / f) * w
    amps = []
    for a_, b_, K in holds:
        m = (ts >= a_) & (ts <= b_)
        u = (ts[m] - a_) / max(1e-9, (b_ - a_))
        base = r[m].copy()

        def tot(A):
            rr = base / (1 + A * (1 - np.cos(2 * np.pi * u)) / 2)
            return float(np.sum(0.5 * (rr[1:] + rr[:-1])) / sub), rr
        lo, hi = 0.0, 1.0
        while tot(hi)[0] > K and hi < 1e6:
            hi *= 2
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if tot(mid)[0] > K:
                lo = mid
            else:
                hi = mid
        r[m] = tot(hi)[1]
        amps.append(hi)
    tau = np.concatenate([[0.0], np.cumsum(0.5 * (r[1:] + r[:-1]) / sub)])
    nout = int(round(tau[-1]))
    tau *= nout / tau[-1]
    tk = np.interp(np.arange(nout + 1), tau, ts)
    tk[-1] = n - 1
    return tk, amps


def apply_plant(frames, tg, frot):
    """anim_lib.apply_feet with a per-frame foot world rotation (None = keep the take's)"""
    out = []
    for i, (w, rh) in enumerate(frames):
        over = {}
        for s in SIDES:
            t = tg[s][i]
            if t is None:
                continue
            fr_ = frot[s][i] if frot and frot[s][i] is not None else w[L.bn(s, 'Foot')]
            over.update(L.leg_ik(L.rebuild(w, over), rh, s, t, foot_rot=fr_))
        out.append((L.rebuild(w, over) if over else w, rh))
    return out


def smooth_lift(need, cyclic):
    """max-filter (+-2) then Gaussian, never below the need; cyclic = over the distinct samples of a closed loop (last = first)"""
    n = len(need)
    if cyclic and n > 3:
        m = n - 1
        v = need[:m]
        mx = np.array([max(v[(i + o) % m] for o in range(-2, 3)) for i in range(m)])
        g = np.exp(-.5 * (np.arange(-4, 5) / 1.5) ** 2); g /= g.sum()
        sm = np.array([sum(g[k] * mx[(i + k - 4) % m] for k in range(9)) for i in range(m)])
        out = np.maximum(sm, v)
        return np.append(out, out[0])
    mx = np.array([need[max(0, i - 2):i + 3].max() for i in range(n)])
    return np.maximum(gauss1d(mx, 1.5, 4), need)


def clean_other_channels(act, keep_range):
    """pose-bone F-curves that are neither rotation_quaternion nor location (the GLB-born fits key scale): drop the ones that hold
    their identity value (scale 1, euler 0) at every key; with keep_range=(first, last) cut the rest to that key range. Returns counts."""
    ident = {'scale': 1.0, 'rotation_euler': 0.0, 'rotation_axis_angle': None}
    dropped, kept, cut = 0, [], 0
    for fc in list(R.action_fcurves(act)):
        p = fc.data_path
        if not p.startswith('pose.bones["') or p.rsplit('.', 1)[1] in ('rotation_quaternion', 'location'):
            continue
        prop = p.rsplit('.', 1)[1]
        dv = ident.get(prop)
        vals = [kp.co.y for kp in fc.keyframe_points]
        if dv is not None and vals and max(abs(v - dv) for v in vals) < 1e-4:
            remove_fcurve(act, fc); dropped += 1
            continue
        kept.append(p + '[%d]' % fc.array_index)
        if keep_range is not None:
            lo, hi = keep_range
            for kp in [kp for kp in fc.keyframe_points if kp.co.x < lo - 1e-4 or kp.co.x > hi + 1e-4][::-1]:
                fc.keyframe_points.remove(kp); cut += 1
            fc.update()
    if kept:
        print('REFINE WARNING %d non-identity non-rotation/location channels kept (cut to the refined range): %s' % (len(kept), kept[:6]))
    return dict(dropped_identity=dropped, kept=kept[:20], kept_count=len(kept), keys_cut=cut)


def remove_fcurve(act, fc):
    if getattr(act, 'fcurves', None) is not None:
        act.fcurves.remove(fc)
        return
    for L_ in act.layers:
        for st in L_.strips:
            for cb in st.channelbags:
                if fc in list(cb.fcurves):
                    cb.fcurves.remove(fc)
                    return


# ------------------------------------------------------------------ main
def main():
    a = parse()
    src = os.path.abspath(a.blend)
    out_blend = os.path.abspath(a.out) if a.out else os.path.splitext(src)[0] + '_refined.blend'
    out_json = os.path.splitext(out_blend)[0] + '.json'
    assert out_blend != src, 'refusing to overwrite the input'
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False)
    sc = bpy.context.scene
    arms = [o for o in sc.objects if o.type == 'ARMATURE']
    arm = next((o for o in arms if o.animation_data and o.animation_data.action), arms[0])
    act = bpy.data.actions[a.action] if a.action else arm.animation_data.action
    R.assign_action(arm, act)
    mesh = max((o for o in sc.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers)),
               key=lambda o: len(o.data.vertices))   # hero: the body (largest skinned mesh)
    clip = a.clip or act.name
    other = clean_other_channels(act, None)
    fps = sc.render.fps / sc.render.fps_base
    xs = sorted({round(kp.co.x, 5) for fc in R.action_fcurves(act) for kp in fc.keyframe_points})
    dx = np.diff(xs)
    if len(xs) > 2 and dx.std() < 1e-3 * dx.mean():
        grid0 = list(xs); spacing = float(dx.mean())
    else:  # irregular keys: integer frames
        grid0 = list(np.arange(math.ceil(xs[0]), math.floor(xs[-1]) + 1, 1.0)); spacing = 1.0
    sr = fps / spacing                       # samples per second
    N0 = len(grid0)
    REP = dict(source=src, clip=clip, action=act.name, scene_fps=fps, grid=dict(first=grid0[0], spacing_frames=spacing, samples=N0,
               sample_rate=sr, seconds=(N0 - 1) / sr), options=vars(a))
    print('REFINE %s: %d samples, %.3f s, sample rate %.3f /s (keys every %.4f frames at %g fps)' % (clip, N0, (N0 - 1) / sr, sr, spacing, fps))
    ch0 = read_channels(act, grid0)
    if a.window:
        wa, wb = max(0, a.window[0]), min(N0 - 1, a.window[1])
        assert wb - wa >= 10, '--window keeps fewer than 11 samples'
        ch0 = {b: {k: v[wa:wb + 1].copy() for k, v in d.items()} for b, d in ch0.items()}
        grid0 = grid0[:wb - wa + 1]
        N0 = len(grid0)
        write_channels(arm, act, ch0, grid0)
        REP['window'] = dict(samples=[wa, wb], seconds=[r3(wa / sr), r3(wb / sr)], kept=N0)
        REP['grid']['samples'] = N0; REP['grid']['seconds'] = (N0 - 1) / sr
        print('REFINE window', json.dumps(REP['window']))
    # ---------- root height shift (--root-dz, ARMATURE units, +z up): a fit made in a project whose model sits at another height
    #           over its floor (hero-dive: the dive picture is 1.2 m over the floor line, the game's LandHero start 0.55 m) lands on that
    #           project's floor in armature space; this moves every root location key by dz in armature space so the landing meets the
    #           game's floor. Done first, so refine's floor/plant logic runs on the shifted motion (pass --floor dz*scale in metres when the
    #           model's own floor is world 0). The root has no parent: armature delta = rest3x3 @ basis delta.
    if a.root_dz:
        rb = L.ROOT
        assert arm.data.bones[rb].parent is None, '--root-dz: root %s has a parent' % rb
        assert rb in ch0 and 'l' in ch0[rb], '--root-dz: no %s location keys in the fit' % rb
        d = arm.data.bones[rb].matrix_local.to_3x3().inverted() @ Vector((0.0, 0.0, a.root_dz))
        ch0[rb]['l'] = np.asarray(ch0[rb]['l'], float) + np.array(list(d))
        write_channels(arm, act, ch0, grid0)
        REP['root_dz'] = dict(armature_units=a.root_dz, metres=r3(a.root_dz * arm.matrix_world.to_scale().z))
        print('REFINE root_dz', json.dumps(REP['root_dz']))
    # ---------- 0. yaw lock (one-shots whose take turns the whole body, e.g. Seedance punches): the root's world yaw relative to frame 0
    #           is removed from every sample (basis q' = Bq^-1 Rz(-dyaw) Bq q); children are parent-relative, so the limbs keep their
    #           body-relative motion. Done on the fit channels before everything else: the raw hand peaks, holds and contact windows are
    #           then measured on the yaw-locked motion (the turn is not motion the game clip keeps). Frame 0 is unchanged.
    if a.lock_yaw:
        rb = L.ROOT
        assert rb in ch0 and 'q' in ch0[rb], '--lock-yaw: no %s rotation keys in the fit' % rb
        Fa, fs, fsrc = facing_axis(src)
        Bq = arm.matrix_world.to_quaternion() @ arm.data.bones[rb].matrix_local.to_quaternion()
        Fw = arm.matrix_world.to_quaternion() @ Fa
        yw = root_yaw(ch0[rb]['q'], Bq, Fw)
        dy = yw - yw[0]
        Bi = Bq.inverted()
        ch0[rb]['q'] = fix_hemi(np.array([list(Bi @ Quaternion((0, 0, 1), -float(dy[i])) @ Bq @ Quaternion(ch0[rb]['q'][i]))
                                         for i in range(N0)]))
        trav = None
        sc_w = arm.matrix_world.to_scale().x
        if 'l' in ch0[rb]:   # travel steps turned by the removed yaw (midpoint angle), in world; location keys are in the rest bone's axes
            Mw = arm.matrix_world.to_quaternion().to_matrix() @ arm.data.bones[rb].matrix_local.to_3x3()
            Mi = Mw.inverted()
            lw = [Mw @ Vector(x) for x in ch0[rb]['l']]
            nw = [lw[0].copy()]
            for i in range(1, N0):
                nw.append(nw[-1] + Matrix.Rotation(-0.5 * float(dy[i] + dy[i - 1]), 3, 'Z') @ (lw[i] - lw[i - 1]))
            ch0[rb]['l'] = np.array([list(Mi @ v) for v in nw])
            hz = lambda v: math.hypot(v.x, v.y)   # noqa: E731
            trav = dict(end_xy_before_mm=r3(hz(lw[-1] - lw[0]) * sc_w * 1000), end_xy_after_mm=r3(hz(nw[-1] - nw[0]) * sc_w * 1000),
                        max_xy_change_mm=r3(max(hz(nw[i] - lw[i]) for i in range(N0)) * sc_w * 1000), z_kept=True)
        write_channels(arm, act, {rb: ch0[rb]}, grid0)
        yr = root_yaw(ch0[rb]['q'], Bq, Fw)
        imax = int(np.argmax(np.abs(dy)))
        REP['yaw_lock'] = dict(bone=rb, facing=fs, facing_source=fsrc, removed_deg_min=r3(math.degrees(dy.min())),
                               removed_deg_max=r3(math.degrees(dy.max())), removed_deg_span=r3(math.degrees(dy.max() - dy.min())),
                               peak_sample=imax, peak_seconds=r3(imax / sr), frame0_yaw_deg=r3(math.degrees(yw[0])),
                               residual_deg_max=r3(math.degrees(np.abs(yr - yr[0]).max())),
                               removed_deg_every_5=[r3(math.degrees(x)) for x in dy[::5]], travel=trav,
                               note='pitch and roll kept; root travel turned into the locked body frame; feet re-pinned by the plant')
        print('REFINE yaw_lock', json.dumps({k: v for k, v in REP['yaw_lock'].items() if k != 'removed_deg_every_5'}))
    rotb = sorted(b for b in ch0 if 'q' in ch0[b])
    armb = [L.bn(s, x) for s in SIDES for x in ARM + L.FINGERS if L.bn(s, x) in ch0]   # hero: the 15 finger bones per hand count as arm
    legb = [L.bn(s, x) for s in SIDES for x in LEG]
    root = L.ROOT
    W = arm.matrix_world.copy()
    sc_w = W.to_scale().x

    names = {g.index: g.name for g in mesh.vertex_groups}
    dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '' for v in mesh.data.vertices])
    toe_idx = {s: np.where(dom == L.bn(s, 'ToeBase'))[0] for s in SIDES}
    foot_idx = {s: np.where((dom == L.bn(s, 'Foot')) | (dom == L.bn(s, 'ToeBase')))[0] for s in SIDES}
    for s in SIDES:
        assert len(toe_idx[s]) and len(foot_idx[s]), 'mesh %s: no vertices dominated by %s / %s' % (mesh.name, L.bn(s, 'ToeBase'), L.bn(s, 'Foot'))
    # hero check: FK from sampled world rotations reproduces the evaluated joint heads (the 0.01 object scale, non-root location keys)
    L.bind(arm, act); R.set_frame(grid0[0])
    w_, rh_ = L.sample(grid0[0]); P_ = L.fk(w_, rh_)
    fk_err = max((P_[b.name] - W @ arm.pose.bones[b.name].head).length for b in arm.data.bones) * 1000
    REP['fk_check_mm_frame0'] = r3(fk_err)
    print('REFINE fk check frame 0: max joint error %.3f mm (FK vs evaluated pose)' % fk_err)

    def eval_frames(grid):
        L.bind(arm, act)
        return [L.sample(x) for x in grid]

    def hand_peaks(frames):
        out = {}
        for s in SIDES:
            P = np.array([list(L.fk(w, rh)[L.bn(s, 'Hand')]) for w, rh in frames])
            v = np.zeros(len(P))
            v[1:-1] = np.linalg.norm(P[2:] - P[:-2], axis=1) / 2 * sr
            i = int(v.argmax())
            out[s] = dict(sample=i, seconds=round(i / sr, 3), frame30=round(i / sr * 30, 1), speed_m_s=round(float(v[i]), 3))
        return out

    def foot_heights(grid):
        """per sample: min z of toe-region and whole-foot vertices per side (fit-scene metres)"""
        res = {s: dict(toe=np.zeros(len(grid)), foot=np.zeros(len(grid))) for s in SIDES}
        for i, x in enumerate(grid):
            R.set_frame(x)
            V = R.mesh_world(mesh)
            for s in SIDES:
                res[s]['toe'][i] = V[toe_idx[s], 2].min()
                res[s]['foot'][i] = V[foot_idx[s], 2].min()
        return res

    # ---------- before: stance overlap, hand peaks, toe heights (raw fit)
    st = json.load(open(a.stance_rig))['start_pose'] if os.path.exists(a.stance_rig) else None
    overlap = None
    if st:
        R.set_frame(grid0[0]); V0 = R.mesh_world(mesh)
        q0 = {pb.name: pb.matrix_basis.to_quaternion() for pb in arm.pose.bones}
        h0 = arm.pose.bones[root].matrix_basis.to_translation()
        arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.matrix_basis = Matrix(st[pb.name])
        bpy.context.view_layer.update()
        Vs = R.mesh_world(mesh)
        angs = {n: math.degrees(q0[n].rotation_difference(Matrix(st[n]).to_quaternion()).angle) for n in st}
        dv = np.linalg.norm(V0 - Vs, axis=1) * 1000
        wn = max(angs, key=lambda n: angs[n] if angs[n] <= 180 else 360 - angs[n])
        overlap = dict(mesh_mm_mean=r3(dv.mean()), mesh_mm_p95=r3(np.percentile(dv, 95)), mesh_mm_max=r3(dv.max()),
                       bone_deg_max=r3(min(angs[wn], 360 - angs[wn])), bone_deg_max_name=wn,
                       hips_loc_mm=r3((h0 - Matrix(st[root]).to_translation()).length * sc_w * 1000))
        R.assign_action(arm, act)
    REP['frame0_vs_start_stance'] = overlap
    print('REFINE frame 0 vs start-picture stance', json.dumps(overlap))
    fr_raw = eval_frames(grid0)
    peaks_raw = hand_peaks(fr_raw)
    fh_raw = foot_heights(grid0)
    toe_raw = min(float(fh_raw[s]['toe'].min()) for s in SIDES)
    med0 = float(np.median(steps(ch0, N0, rotb)))
    REP['raw'] = dict(median_step_rad=r3(med0), pose_dist_last_vs_first_rad=r3(pose_dist(ch0, N0 - 1, 0, rotb)),
                      seam_ratio_last_to_first=r3(pose_dist(ch0, N0 - 1, 0, rotb) / med0), peak_hand=peaks_raw,
                      toe_min_mm=r3((toe_raw - a.floor) * 1000))

    # ---------- 1. trim the still tail
    spd = steps(ch0, N0, rotb)
    run = np.convolve(np.pad(spd, 4, mode='edge'), np.ones(9) / 9, mode='valid')
    N = N0
    trim_rep = dict(threshold=a.trim)
    if a.trim > 0:
        live = [i for i in range(len(run)) if run[i] >= a.trim * med0]
        still_start = (live[-1] + 1) if live else N0 - 1
        Nt = min(N0, still_start + 1)
        floor_n = max(int(0.5 * N0), int(round(1.0 * sr)))
        trim_rep.update(still_tail_start=int(still_start), limited=Nt < floor_n)
        N = max(Nt, min(N0, floor_n))
    trim_rep.update(kept=[0, N - 1], trimmed_samples=N0 - N, trimmed_seconds=r3((N0 - N) / sr))
    REP['trim'] = trim_rep
    ch = {b: {k: v[:N].copy() for k, v in d.items()} for b, d in ch0.items()}
    print('REFINE trim', json.dumps(trim_rep))

    # ---------- 2. single-frame spikes (per bone: out-and-back deviation from the neighbours' midpoint)
    spikes = {}
    G = np.exp(-.5 * (np.arange(-2, 3) / 1.0) ** 2); G /= G.sum()
    for b in rotb:
        q = ch[b]['q']
        touched = set()
        for _ in range(3):
            dev = np.zeros(N); rev = np.zeros(N, bool)
            for i in range(1, N - 1):
                mid = nlerp(q[i - 1], q[i + 1], 0.5)
                dev[i] = qang(q[i], mid)
                d1 = (Quaternion(q[i - 1]).inverted() @ Quaternion(q[i])).to_exponential_map()
                d2 = (Quaternion(q[i]).inverted() @ Quaternion(q[i + 1])).to_exponential_map()
                rev[i] = d1.length > 1e-9 and d2.length > 1e-9 and d1.normalized().dot(d2.normalized()) < 0
            med = float(np.median(dev[1:-1])) if N > 2 else 0.0
            thr = max(a.spike_k * med, math.radians(a.spike_min_deg))
            stp = [qang(q[i], q[i + 1]) for i in range(N - 1)]

            def isolated(i):   # the in/out steps dwarf the steps around them: a jitter frame, not a fast extreme (punch snap)
                around = max(stp[i - 2] if i >= 2 else 0.0, stp[i + 1] if i + 1 < N - 1 else 0.0)
                return min(stp[i - 1], stp[i]) > a.spike_iso * around
            sp = [i for i in range(1, N - 1) if dev[i] > thr and rev[i] and isolated(i)]
            if not sp:
                break
            for i in sp:
                q[i] = nlerp(q[i - 1], q[i + 1], 0.5); touched.add(i)
            qs = q.copy()
            for i in sp:
                for j in range(max(1, i - 1), min(N - 1, i + 2)):
                    acc = sum(g * qs[min(N - 1, max(0, j + o))] * (1 if np.dot(qs[min(N - 1, max(0, j + o))], qs[j]) >= 0 else -1)
                              for o, g in zip(range(-2, 3), G))
                    q[j] = acc / np.linalg.norm(acc); touched.add(j)
        ch[b]['q'] = fix_hemi(q)
        if touched:
            spikes[b] = sorted(int(i) for i in touched)
    REP['spikes'] = dict(bones=len(spikes), frames_touched=spikes, arm_bones_touched=[b for b in spikes if b in armb])
    print('REFINE spikes', json.dumps({b: len(v) for b, v in spikes.items()}))
    spike_frames_arm = {b: set(spikes.get(b, [])) for b in armb}

    # ---------- 2b. bursts: 1..M samples of huge steps between quiet steps (a solver reset switching twist branch); keep the net change,
    #           re-time it as a smoothstep offset (remove the jump: z = q after the burst @ X, X = q[e]^-1 q[s]; re-add X^-1 eased)
    bursts, skipped = {}, []
    if not a.no_burst:
        thr_min = math.radians(a.burst_min_deg)
        ease = math.radians(a.burst_ease_deg)
        nmax = max(a.burst_max + 2, int(round(0.5 * sr)))
        for b in rotb:
            q = ch[b]['q']
            found = []
            i = 1
            stp = np.array([qang(q[k], q[k + 1]) for k in range(N - 1)])
            thr = max(a.burst_k * float(np.median(stp)), thr_min)   # the take's own median, fixed before any edit
            while i < N - 2:
                if stp[i] <= thr:
                    i += 1
                    continue
                j = i
                while j + 1 < N - 1 and stp[j + 1] > thr:
                    j += 1
                s_, e_ = i, j + 1                                    # keys before / after the burst
                around = max(list(stp[max(0, i - 2):i]) + list(stp[j + 1:j + 3]) + [0.0])
                if j - i + 1 > a.burst_max or e_ >= N - 1 or stp[i:j + 1].min() <= a.burst_iso * around:
                    i = j + 1
                    continue
                # twist-dominated only: the bone's length axis (local Y) barely moves across the burst. A real fast swing between
                # holds (Throw's hurl: arms overhead -> forward, ~95 deg in 3 samples) is motion and is never re-timed.
                yb, ya = Quaternion(q[s_]) @ Vector((0, 1, 0)), Quaternion(q[e_]) @ Vector((0, 1, 0))
                swing = math.degrees(yb.angle(ya, 0.0))
                if swing > a.burst_max_swing_deg:
                    skipped.append(dict(bone=b, keys=[int(s_), int(e_)], swing_deg=r3(swing), path_deg=r3(math.degrees(float(stp[i:j + 1].sum())))))
                    i = j + 1
                    continue
                X = Quaternion(q[e_]).inverted() @ Quaternion(q[s_])
                Xi = X.inverted()
                net = Xi.angle if Xi.angle <= math.pi else 2 * math.pi - Xi.angle
                n = int(min(nmax, max(j - i + 1 + 2, math.ceil(1.5 * net / ease))))
                n = min(n, N - 1)
                c = 0.5 * (s_ + e_)
                w0 = int(max(0, min(s_, math.floor(c - n / 2.0))))
                w1 = int(min(N - 1, max(e_, w0 + n)))
                z = [Quaternion(q[k]) for k in range(N)]
                for k in range(s_ + 1, e_):
                    z[k] = Quaternion(q[s_])
                for k in range(e_, N):
                    z[k] = Quaternion(q[k]) @ X
                for k in range(w0, N):
                    wgt = sstep((k - w0) / max(1, (w1 - w0)))
                    q[k] = np.array(z[k] @ Quaternion().slerp(Xi, wgt))
                q[:] = fix_hemi(q)
                stp2 = [qang(q[k], q[k + 1]) for k in range(w0, w1)]
                found.append(dict(swing_deg=r3(swing), steps_deg=[r3(math.degrees(x)) for x in stp[i:j + 1]], keys=[int(s_), int(e_)], around_deg=r3(math.degrees(around)),
                                  net_deg=r3(math.degrees(net)), path_deg=r3(math.degrees(float(stp[i:j + 1].sum()))), window=[w0, w1],
                                  peak_step_after_deg=r3(math.degrees(max(stp2)))))
                i = w1 + 1
                stp = np.array([qang(q[k], q[k + 1]) for k in range(N - 1)])
            ch[b]['q'] = fix_hemi(q)
            if found:
                bursts[b] = found
                if b in spike_frames_arm:
                    for f_ in found:
                        spike_frames_arm[b].update(range(f_['window'][0], f_['window'][1] + 1))
    REP['bursts'] = dict(bones=len(bursts), found=bursts, skipped_as_swing=skipped,
                         options=dict(k=a.burst_k, min_deg=a.burst_min_deg, iso=a.burst_iso, max=a.burst_max, max_swing_deg=a.burst_max_swing_deg,
                                      ease_deg=a.burst_ease_deg, off=a.no_burst))
    print('REFINE bursts', json.dumps({b: [(f_['keys'], f_['net_deg'], f_['path_deg'], f_['window'], f_['peak_step_after_deg']) for f_ in v]
                                       for b, v in bursts.items()}), 'skipped (real swing)', json.dumps([(x['bone'], x['keys'], x['swing_deg']) for x in skipped]))

    # ---------- 2c. hold compression (one-shots): re-time near-static spans to <= --hold-keep samples, cap the length
    tmap = None   # output sample -> fractional source sample, when re-timed
    if a.compress_holds:
        stp_ = steps(ch, N, rotb) / len(rotb) * sr                      # mean rad/s per bone, per step
        vs = np.zeros(N); vs[1:] += stp_; vs[:-1] += stp_; vs[1:-1] *= 0.5
        vs = np.degrees(np.convolve(np.pad(vs, 2, mode='edge'), np.ones(5) / 5, mode='valid'))
        thr = float(min(a.hold_max_dps, max(a.hold_min_dps, a.hold_frac * np.percentile(vs, 95))))
        cw = int(round(a.contact_s * sr))
        contact, cspans = set(), []
        for s_ in SIDES:
            pk = peaks_raw[s_]['sample']
            if pk < N:
                contact.update(range(max(0, pk - cw), min(N, pk + cw + 1)))
                cspans.append((max(0, pk - cw), min(N - 1, pk + cw)))
        static = [(vs[i] < thr and i not in contact) for i in range(N)]
        minlen = int(math.ceil(a.hold_min_s * sr))
        keep_up = a.hold_keep_up or a.hold_keep
        hz = {s_: np.array([L.fk(w, rh)[L.bn(s_, 'Hand')].z for w, rh in fr_raw[:N]]) for s_ in SIDES}
        head_z = np.array([L.fk(w, rh)[L.HEAD].z for w, rh in fr_raw[:N]])
        spans, i = [], 0
        while i < N:
            if not static[i]:
                i += 1
                continue
            j = i
            while j + 1 < N and static[j + 1]:
                j += 1
            if j - i + 1 >= minlen:
                up = bool(np.all(hz['Left'][i:j + 1] > head_z[i:j + 1]) and np.all(hz['Right'][i:j + 1] > head_z[i:j + 1]))
                spans.append(dict(samples=[i, j], seconds=[r3(i / sr), r3(j / sr)], length_s=r3((j - i) / sr), hands_up=up,
                                  keep=keep_up if up else a.hold_keep))
            i = j + 1
        holds = [(sp['samples'][0], sp['samples'][1], sp['keep']) for sp in spans if sp['samples'][1] - sp['samples'][0] > sp['keep']]
        # speed-up of the non-hold, non-contact time: the smallest f in 1..--max-speedup that meets --max-seconds (contact spans stay
        # at real speed); a hold already shorter than K at that rate is left alone
        def warp(f_):
            hs = [(a_, b_, K) for a_, b_, K in holds if K < (b_ - a_) / f_]
            return hold_warp(N, hs, f_, cspans) + (hs,)
        f = 1.0
        tmap, amps, hs = warp(f)
        if a.max_seconds > 0 and (len(tmap) - 1) / sr > a.max_seconds:
            lo_, hi_ = 1.0, a.max_speedup
            if (len(warp(hi_)[0]) - 1) / sr > a.max_seconds:
                f = hi_
            else:
                for _ in range(30):
                    mid = 0.5 * (lo_ + hi_)
                    if (len(warp(mid)[0]) - 1) / sr > a.max_seconds:
                        lo_ = mid
                    else:
                        hi_ = mid
                f = hi_
            tmap, amps, hs = warp(f)
        holds = hs
        N_before = N
        ch = resample(ch, tmap)
        N = len(tmap)
        inv = lambda t: float(np.interp(t, tmap, np.arange(N)))   # noqa: E731  source sample -> output sample
        for b in spike_frames_arm:
            spike_frames_arm[b] = {k for k in range(N) if any(abs(tmap[k] - s) <= 1.0 for s in spike_frames_arm[b])}
        REP['retime'] = dict(threshold_dps=r3(thr), p95_dps=r3(np.percentile(vs, 95)), contact_samples=sorted(contact), contact_spans=cspans,
                             contact_note='contact spans play at real speed (rate 1), eased over 3 samples', spans=spans,
                             compressed=[dict(samples=[a_, b_], keep=K, ease_amp=r3(A)) for (a_, b_, K), A in zip(holds, amps)],
                             speedup=r3(f), samples_before=N_before, samples_after=N, seconds_before=r3((N_before - 1) / sr),
                             seconds_after=r3((N - 1) / sr),
                             hit_raw={s_: dict(sample=peaks_raw[s_]['sample'], seconds=peaks_raw[s_]['seconds']) for s_ in SIDES},
                             hit_mapped={s_: dict(sample=r3(inv(peaks_raw[s_]['sample'])), seconds=r3(inv(peaks_raw[s_]['sample']) / sr)) for s_ in SIDES})
        print('REFINE retime', json.dumps({k: v for k, v in REP['retime'].items() if k != 'contact_samples'}))

    # ---------- 3a. loop: best end frame + offset blend
    blend_win = set()
    if a.loop:
        win = int(round(a.loop_win * sr))
        lo = max(int(N * 0.5), N - 1 - win)

        def cost(Lx):
            c = 0.0
            for b in rotb:
                q = ch[b]['q']
                c += qang(q[Lx], q[0]) ** 2
                v_end = Quaternion(q[Lx - 1]).inverted() @ Quaternion(q[Lx]); v_beg = Quaternion(q[0]).inverted() @ Quaternion(q[1])
                c += 0.5 * v_end.rotation_difference(v_beg).angle ** 2
            if root in ch and 'l' in ch[root]:
                l_ = ch[root]['l']; c += float(np.sum((l_[Lx] - l_[0]) ** 2)) * 25
            return c
        costs = {Lx: cost(Lx) for Lx in range(lo, N)}
        Lend = min(costs, key=costs.get)
        offs = {b: (Quaternion(ch[b]['q'][Lend]).inverted() @ Quaternion(ch[b]['q'][0])) for b in rotb}
        for b in offs:
            if offs[b].w < 0:
                offs[b] = -offs[b]
        tot = sum(o.angle for o in offs.values())
        if a.xfade:
            nX = a.xfade; why = 'forced'
        else:  # smallest N in 12..24 whose blend adds at most half a median step per frame (smoothstep peak slope 1.5/N)
            nX = next((n for n in range(12, 25) if tot * 1.5 / n <= 0.5 * med0), 24); why = 'auto: added step <= 0.5 x median' if tot * 1.5 / nX <= 0.5 * med0 else 'auto: capped at 24'
        nX = min(nX, Lend)
        seam_before = pose_dist(ch, N - 1, 0, rotb) / med0
        for b in rotb:
            q = ch[b]['q']
            for j in range(Lend - nX, Lend + 1):
                s = sstep((j - (Lend - nX)) / nX)
                q[j] = np.array(q[j]) if s == 0 else np.array(Quaternion(q[j]) @ Quaternion().slerp(offs[b], s))
            ch[b]['q'] = fix_hemi(q)
        for b, d in ch.items():
            if 'l' in d:
                l0, lL = d['l'][0].copy(), d['l'][Lend].copy()
                for j in range(Lend - nX, Lend + 1):
                    d['l'][j] = d['l'][j] + sstep((j - (Lend - nX)) / nX) * (l0 - lL)
        N = Lend + 1
        for b in ch:
            for k in ch[b]:
                ch[b][k] = ch[b][k][:N]
        blend_win = set(range(Lend - nX, Lend + 1))
        REP['loop'] = dict(window_samples=win, end_sample=Lend, end_seconds=r3(Lend / sr), cost=r3(costs[Lend]), cost_at_last=r3(costs[max(costs)]),
                           xfade=nX, xfade_rule=why, offset_total_rad=r3(tot), seam_ratio_before=r3(seam_before))
        print('REFINE loop', json.dumps(REP['loop']))

    # ---------- 3b. one-shot: return to the frame-0 stance
    if a.return_to_stance:
        Wn = max(2, min(a.return_frames, N // 2))
        # combat timing: the blend never starts before the later hand-speed peak + 0.2 s (contact and follow-through survive)
        if tmap is not None:
            hp = int(round(max(np.interp(peaks_raw[s_]['sample'], tmap, np.arange(N)) for s_ in SIDES if peaks_raw[s_]['sample'] <= tmap[-1])))
        else:
            hp = max(peaks_raw[s_]['sample'] for s_ in SIDES if peaks_raw[s_]['sample'] < N)
        start_min = hp + int(round(0.2 * sr))
        limited = N - Wn < start_min
        if limited:
            Wn = max(2, N - start_min)
        # the blend target: frame 0 (the Brute: its one-shots start in the stance), or with --return-target stance (hero) the
        # --stance-rig start_pose (pose-basis rotations of every bone, location of every location-keyed bone)
        tq = {b: np.array(ch[b]['q'][0]) for b in rotb}
        tl = {b: np.array(d['l'][0]) for b, d in ch.items() if 'l' in d}
        if a.return_target == 'stance':
            assert st, '--return-target stance: no start_pose in --stance-rig %s' % a.stance_rig
            miss = [b for b in rotb if b not in st]
            assert not miss, '--return-target stance: stance rig lacks bones %s' % miss[:8]
            tq = {b: np.array(list(Matrix(st[b]).to_quaternion())) for b in rotb}
            tl = {b: np.array(list(Matrix(st[b]).to_translation())) for b in tl}
        Bq_ = arm.matrix_world.to_quaternion() @ arm.data.bones[root].matrix_local.to_quaternion()
        Fw_ = arm.matrix_world.to_quaternion() @ facing_axis(src)[0]
        yw_ = root_yaw(np.array([ch[root]['q'][N - 1], tq[root]]), Bq_, Fw_)
        yaw_aligned = None
        if a.stance_yaw_align:   # turn the stance's root about world Z onto the clip end's facing (its body-relative pose is kept)
            dyw = float(yw_[0] - yw_[1])
            tq[root] = np.array(list(Bq_.inverted() @ Quaternion((0, 0, 1), dyw) @ Bq_ @ Quaternion(tq[root])))
            yaw_aligned = r3(math.degrees(dyw))
        before = pose_dist_to(ch, N - 1, tq, rotb)
        for b in rotb:
            q = ch[b]['q']
            for j in range(N - Wn, N):
                q[j] = nlerp(q[j], tq[b], sstep((j - (N - Wn) + 1) / Wn))
            ch[b]['q'] = fix_hemi(q)
        Rr = arm.data.bones[root].matrix_local.to_3x3()      # root location keys are in the rest bone's axes; travel = armature x/y
        for b, d in ch.items():
            if 'l' not in d:
                continue
            for j in range(N - Wn, N):
                s = sstep((j - (N - Wn) + 1) / Wn)
                if a.keep_travel and b == root:
                    lj, l0 = Rr @ Vector(d['l'][j]), Rr @ Vector(tl[b])
                    t = Vector((lj.x, lj.y, (1 - s) * lj.z + s * l0.z))
                    d['l'][j] = list(Rr.inverted() @ t)
                else:
                    d['l'][j] = (1 - s) * d['l'][j] + s * tl[b]
        blend_win = set(range(N - Wn, N))
        REP['return'] = dict(frames=Wn, seconds=r3(Wn / sr), limited_by_hand_peak=limited, hand_peak_sample=hp, target=a.return_target,
                             end_vs_start_rad_before=r3(before), end_vs_start_rad_after=r3(pose_dist_to(ch, N - 1, tq, rotb)),
                             end_vs_frame0_rad_after=r3(pose_dist(ch, N - 1, 0, rotb)),
                             root_yaw_end_to_target_deg=r3(math.degrees(yw_[1] - yw_[0])), stance_yaw_aligned_deg=yaw_aligned,
                             note='end_vs_start_* are measured against the blend target (frame 0, or the stance rig with --return-target stance)')
        print('REFINE return', json.dumps(REP['return']))

    grid = grid0[:N]
    write_channels(arm, act, ch, grid)
    ch_pre = {b: {k: v.copy() for k, v in d.items()} for b, d in ch.items()}   # for the untouched-arms proof

    # ---------- 4. feet: plant while grounded (anim_lib segmentation + analytic 2-bone IK), cyclic-aware for loops
    frames = eval_frames(grid)
    feet_rep = {}
    groups = {}
    if not a.no_plant:
        for s in SIDES:
            grd = {}
            _, segs = L.plant_targets(frames, s, floor=a.floor, floor_tol=a.plant_floor_tol, report=grd)
            feet_rep.setdefault('floor_guard', {})[s] = grd
            gs = [[sg] for sg in segs]
            if a.loop and len(gs) >= 2 and segs[0][0] == 0 and segs[-1][1] == N - 1:
                gs = [gs[0] + gs[-1]] + gs[1:-1]
            groups[s] = gs
        # treadmill: per segment, the unwrapped sample index of its samples (a loop's tail plant, merged with the head plant across the
        # wrap, counts from -(N-1) so it continues the head plant's time line) and one ground velocity for the whole take
        seg_shift = {s: {} for s in SIDES}
        for s in SIDES:
            for g in groups[s]:
                merged = len(g) >= 2 and g[0][0] == 0 and g[-1][1] == N - 1
                for sg in g:
                    seg_shift[s][tuple(sg)] = -(N - 1) if (merged and sg is g[-1]) else 0
        Vg = Vector((0.0, 0.0, 0.0))
        if a.treadmill:
            P_ = [L.fk(w, rh) for w, rh in frames]
            vx, vy = [], []
            for s in SIDES:
                for g in groups[s]:
                    for a_, b_ in g:
                        for i in range(a_, b_):
                            d_ = P_[i + 1][L.bn(s, 'ToeBase')] - P_[i][L.bn(s, 'ToeBase')]
                            vx.append(d_.x * sr); vy.append(d_.y * sr)
            if vx:
                Vg = Vector((float(np.median(vx)), float(np.median(vy)), 0.0))
            feet_rep['treadmill'] = dict(velocity_xy=[r3(Vg.x), r3(Vg.y)], speed=r3(Vg.length), speed_m_s_world=r3(Vg.length),
                                         samples=len(vx), note='fit-scene world metres per second (FK positions are world)')
            print('REFINE treadmill', json.dumps(feet_rep['treadmill']))

        def off(s, sg, i):   # ground offset of sample i (planted on segment sg) in the sliding frame; zero without --treadmill
            return Vg * ((i + seg_shift[s].get(tuple(sg), 0)) / sr)

        def seg_of(g, i):
            return next((sg for sg in g if sg[0] - 4 <= i <= sg[1] + 4), g[0])

        def drift(frs):
            res = {}
            for s in SIDES:
                P = [L.fk(w, rh) for w, rh in frs]
                worst = dict(ankle=0.0, toe=0.0)
                for g in groups[s]:
                    idx = [i for a_, b_ in g for i in range(a_, b_ + 1)]
                    zmin = min(P[i][L.bn(s, 'Foot')].z for i in idx)
                    down = [i for i in idx if P[i][L.bn(s, 'Foot')].z - zmin < 0.01] or idx   # ankle counts while the heel is down
                    for key, bn, ii in (('ankle', L.bn(s, 'Foot'), down), ('toe', L.bn(s, 'ToeBase'), idx)):
                        pts = np.array([[P[i][bn].x - off(s, seg_of(g, i), i).x, P[i][bn].y - off(s, seg_of(g, i), i).y] for i in ii])
                        if len(pts):
                            worst[key] = max(worst[key], float(np.linalg.norm(pts - pts.mean(0), axis=1).max()) * 1000)
                res[s] = {k: r3(v) for k, v in worst.items()}
            return res
        d_before = drift(frames)
        # heel down: ankle pinned (xy) to the plant's mean and the foot held at the plant's flat rotation (mean, yaw-aligned), so ankle
        # and toe joint both stay put; heel up (ankle 0-2 cm over its lowest in the plant, smooth): the pivot moves to the ball, the toe
        # joint is pinned to its mean and the foot keeps the take's pitch/roll (yaw still pinned), the ankle following around the ball.
        # 3-sample blends in/out, like anim_lib.plant_targets
        tg, frot = {}, {}
        for s in SIDES:
            P = [L.fk(w, rh) for w, rh in frames]
            ank = [p[L.bn(s, 'Foot')] for p in P]
            toe = [p[L.bn(s, 'ToeBase')] for p in P]
            yaw = [math.atan2((toe[i] - ank[i]).y, (toe[i] - ank[i]).x) for i in range(N)]
            tgt, wts, fr_ = [None] * N, [0.0] * N, [None] * N
            for g in groups[s]:
                idx = [i for a_, b_ in g for i in range(a_, b_ + 1)]
                c = sum((ank[i] - off(s, seg_of(g, i), i) for i in idx), Vector()) / len(idx)
                zmin = min(ank[i].z for i in idx)
                yc = math.atan2(sum(math.sin(yaw[i]) for i in idx), sum(math.cos(yaw[i]) for i in idx))
                # flat-foot rotation of this plant: mean of the yaw-locked foot rotations over the heel-down samples
                flat = [i for i in idx if ank[i].z - zmin < 0.01] or idx
                qs = [Quaternion((0, 0, 1), L.wrap(yc - yaw[i])) @ frames[i][0][L.bn(s, 'Foot')] for i in flat]
                acc = np.zeros(4)   # (mathutils' 4-D Vector.normalized() only normalizes x, y, z: use numpy)
                for q in qs:
                    acc += np.array(q) * (1 if q.dot(qs[0]) >= 0 else -1)
                qflat = Quaternion(acc / np.linalg.norm(acc))
                # the plant that holds frame 0 (and, returning to the stance, the plant that holds the last frame) is anchored on that
                # frame instead of the mean, so frame 0 stays the start-picture stance the game blends from
                a0 = 0 if 0 in idx else (N - 1 if (a.return_to_stance and N - 1 in idx) else None)
                if a0 is not None:
                    c, yc, qflat = ank[a0] - off(s, seg_of(g, a0), a0), yaw[a0], frames[a0][0][L.bn(s, 'Foot')].copy()
                # the ball pin is where the flat foot puts the toe joint (rigid offset in the foot's frame), so the heel-down and heel-up
                # phases share one contact point
                i0 = idx[0]
                ct = c + qflat @ (frames[i0][0][L.bn(s, 'Foot')].inverted() @ (toe[i0] - ank[i0]))
                for a_, b_ in g:
                    for i in range(max(0, a_ - 3), min(N, b_ + 4)):
                        w = 1.0 if a_ <= i <= b_ else L.smooth(1 - (a_ - i) / 4) if i < a_ else L.smooth(1 - (i - b_) / 4)
                        if w > wts[i]:
                            rz = Quaternion((0, 0, 1), L.wrap(yc - yaw[i]) * w)
                            u = L.smooth((ank[i].z - zmin) / 0.02)
                            qf = frames[i][0][L.bn(s, 'Foot')]
                            qpl = qflat.slerp(Quaternion((0, 0, 1), L.wrap(yc - yaw[i])) @ qf, u)   # heel down: flat; heel up: take's roll
                            qn = qf.slerp(qpl, w)
                            v = qpl @ (qf.inverted() @ (toe[i] - ank[i]))
                            o_ = off(s, (a_, b_), i)
                            pin = Vector((ct.x + o_.x - v.x, ct.y + o_.y - v.y, c.z))   # toe joint on the contact point; heel down => pin == c
                            wts[i] = w; tgt[i] = Vector((ank[i].x + (pin.x - ank[i].x) * w, ank[i].y + (pin.y - ank[i].y) * w, ank[i].z))
                            fr_[i] = qn
            tg[s], frot[s] = tgt, fr_
        frames = apply_plant(frames, tg, frot)
        reach = {}
        for s in SIDES:   # IK reach: samples where the solved ankle misses its pin by > 5 mm (target beyond the straight leg)
            miss = [i for i in range(N) if tg[s][i] is not None and
                    (Vector(L.fk(*frames[i])[L.bn(s, 'Foot')][:2]) - Vector(tg[s][i][:2])).length > 0.005]
            reach[s] = dict(samples_missing_pin=len(miss), first=miss[:8])
        d_after = drift(frames)
        feet_rep.update(plants={s: [[list(sg) for sg in g] for g in groups[s]] for s in SIDES},
                        planted_samples={s: int(sum(b_ - a_ + 1 for g in groups[s] for a_, b_ in g)) for s in SIDES},
                        drift_mm_before=d_before, drift_mm_after=d_after, ik_reach=reach)

        def to_basis(frs):
            Wqi, tR, PAR = L.S['Wqi'], L.S['tR'], L.S['PAR']
            for bn in legb:
                q = np.zeros((N, 4))
                for i, (w, rh) in enumerate(frs):
                    aq = Wqi @ w[bn]; p = PAR[bn]
                    qq = (((Wqi @ w[p]) @ (tR[p].inverted() @ tR[bn])).inverted() @ aq) if p else tR[bn].inverted() @ aq
                    q[i] = list(qq)
                ch.setdefault(bn, {})['q'] = fix_hemi(q)
        to_basis(frames)
        write_channels(arm, act, {b: ch[b] for b in legb}, grid)
        print('REFINE feet', json.dumps(feet_rep['drift_mm_before']), '->', json.dumps(d_after))

        # ---------- 5. toes above the floor: lift the ankle (IK, foot rotation kept) where any foot vertex is under the floor
        fh = foot_heights(grid)
        lifts = {}
        for s in SIDES:
            need = np.maximum(0.0, a.floor - fh[s]['foot'])
            if need.max() > a.max_lift:
                feet_rep.setdefault('floor_mismatch', {})[s] = dict(deepest_mm=r3(need.max() * 1000), samples_over_cap=int((need > a.max_lift).sum()),
                                                                     note='penetration deeper than --max-lift: capped; check --floor / the root height')
                print('REFINE WARNING %s foot %.0f mm under the floor (> --max-lift %.0f mm): lift capped' % (s, need.max() * 1000, a.max_lift * 1000))
                need = np.minimum(need, a.max_lift)
            lifts[s] = smooth_lift(need, a.loop)
            if a.stance_snap:   # the return blend made the last pose equal frame 0 before the clamp; give it frame 0's lift too
                nS = max(2, min(a.stance_snap, N - 1))
                l_ = lifts[s]; before_ = float(l_[N - 1] - l_[0])
                for j in range(N - nS, N):
                    sw = sstep((j - (N - nS) + 1) / nS)
                    l_[j] = max(need[j], (1 - sw) * l_[j] + sw * (0.0 if a.return_target == 'stance' else l_[0]))   # stance: its own pose, no lift
                feet_rep.setdefault('stance_snap', {})[s] = dict(samples=nS, end_minus_start_lift_mm_before=r3(before_ * 1000),
                                                                 after=r3((l_[N - 1] - l_[0]) * 1000))
        if any(l_.max() > 1e-6 for l_ in lifts.values()):
            frames = eval_frames(grid)
            tg = {}
            for s in SIDES:
                tg[s] = [None] * N
                for i, (w, rh) in enumerate(frames):
                    if lifts[s][i] > 1e-6:
                        p = L.fk(w, rh)[L.bn(s, 'Foot')]
                        tg[s][i] = Vector((p.x, p.y, p.z + lifts[s][i]))
            frames = apply_plant(frames, tg, None)
            to_basis(frames)
            write_channels(arm, act, {b: ch[b] for b in legb}, grid)
        if a.loop:   # the leg edits are built cyclic; make the closed end exact and report what that changed
            res_ = max(math.degrees(qang(ch[b]['q'][N - 1], ch[b]['q'][0])) for b in legb)
            for b in legb:
                ch[b]['q'][N - 1] = ch[b]['q'][0]
            write_channels(arm, act, {b: ch[b] for b in legb}, grid)
            feet_rep['loop_leg_end_residual_deg'] = r3(res_)
        feet_rep['toe_clamp'] = {s: dict(max_lift_mm=r3(lifts[s].max() * 1000), samples_lifted=int((lifts[s] > 1e-6).sum())) for s in SIDES}
    REP['feet'] = feet_rep

    # ---------- after
    fr_fin = eval_frames(grid)
    peaks = hand_peaks(fr_fin)
    fh_fin = foot_heights(grid)
    toe_min = min(float(fh_fin[s]['toe'].min()) for s in SIDES)
    foot_min = min(float(fh_fin[s]['foot'].min()) for s in SIDES)
    chf = read_channels(act, grid)
    medf = float(np.median(steps(chf, N, rotb)))
    dup = pose_dist(chf, N - 1, 0, rotb) < 1e-3
    if a.loop:
        seam = pose_dist(chf, N - 2, 0, rotb) / medf
        seam_def = 'loop: last distinct frame (N-2) -> frame 0 / median step; end frame equals frame 0: %s' % dup
    else:
        if a.return_target == 'stance':
            seam = pose_dist_to(chf, N - 1, tq, rotb) / medf
            seam_def = 'one-shot, --return-target stance: last frame -> the stance rig start_pose / median step'
        else:
            seam = pose_dist(chf, N - 1, 0, rotb) / medf
            seam_def = 'one-shot: last frame -> frame 0 / median step'
    # untouched arms: every arm-bone rotation equals the pre-plant channels (plant touches legs only); and the pre-plant channels equal
    # the raw fit outside spike frames and the loop/return blend window
    arm_vs_pre = max((math.degrees(qang(chf[b]['q'][i], ch_pre[b]['q'][i])) for b in armb for i in range(N)), default=0.0)
    ch0p = resample(ch0, tmap) if tmap is not None else ch0     # re-timed clips: compare with the raw fit on the same time map
    arm_vs_raw = max((math.degrees(qang(ch_pre[b]['q'][i], ch0p[b]['q'][i])) for b in armb for i in range(N)
                      if i not in blend_win and i not in spike_frames_arm[b]), default=0.0)
    head_dev = {b: r3(max(math.degrees(qang(chf[b]['q'][i], chf[b]['q'][0])) for i in range(N))) for b in (L.NECK, L.HEAD) if b in chf}
    if not a.no_plant:
        feet_rep['drift_mm_final'] = drift(fr_fin)
        # hero report: how far the soles sit from the floor while planted (lowest foot-region vertex, after the plant + clamp), mm
        feet_rep['plant_sole_mm'] = {s: [dict(samples=[int(a_), int(b_)], min=r3((fh_fin[s]['foot'][a_:b_ + 1].min() - a.floor) * 1000),
                                              max=r3((fh_fin[s]['foot'][a_:b_ + 1].max() - a.floor) * 1000))
                                         for g in groups[s] for a_, b_ in g] for s in SIDES}
        feet_rep['last_sample_sole_mm'] = {s: r3((fh_fin[s]['foot'][N - 1] - a.floor) * 1000) for s in SIDES}
        print('REFINE plant soles (mm above floor, min/max per plant)', json.dumps(feet_rep['plant_sole_mm']), 'last sample', json.dumps(feet_rep['last_sample_sole_mm']))
    drift_after = max((v for s in SIDES for v in feet_rep.get('drift_mm_final', {}).get(s, {}).values()), default=float('nan'))
    if st:
        R.set_frame(grid[0]); V0f = R.mesh_world(mesh)
        dvf = np.linalg.norm(V0f - Vs, axis=1) * 1000
        REP['frame0_vs_start_stance_after'] = dict(mesh_mm_mean=r3(dvf.mean()), mesh_mm_p95=r3(np.percentile(dvf, 95)), mesh_mm_max=r3(dvf.max()))
        R.set_frame(grid[-1]); VLf = R.mesh_world(mesh)
        dvl = np.linalg.norm(VLf - Vs, axis=1) * 1000; dv0l = np.linalg.norm(VLf - V0f, axis=1) * 1000
        REP['last_frame_vs_start_stance'] = dict(mesh_mm_mean=r3(dvl.mean()), mesh_mm_max=r3(dvl.max()))
        REP['last_frame_vs_frame0'] = dict(mesh_mm_mean=r3(dv0l.mean()), mesh_mm_max=r3(dv0l.max()))
        print('REFINE refined frame 0 vs start-picture stance', json.dumps(REP['frame0_vs_start_stance_after']))
    REP['final'] = dict(samples=N, seconds=r3((N - 1) / sr), key_first=grid[0], key_last=grid[-1], seam_ratio=r3(seam), seam_definition=seam_def,
                        median_step_rad=r3(medf), foot_drift_mm=r3(drift_after), toe_min_mm=r3((toe_min - a.floor) * 1000),
                        toe_min_mm_before=REP['raw']['toe_min_mm'], foot_sole_min_mm=r3((foot_min - a.floor) * 1000),
                        peak_hand=peaks, peak_hand_raw=peaks_raw,
                        arm_rotation_change_deg_by_plant=r3(arm_vs_pre), arm_rotation_change_deg_outside_spikes_and_blend=r3(arm_vs_raw),
                        neck_head_max_deg_from_frame0=head_dev)
    sc.frame_start, sc.frame_end = int(math.floor(grid[0])), int(math.ceil(grid[-1]))
    act.name = act.name if act.name.endswith('_refined') else act.name + '_refined'
    REP['final']['action'] = act.name
    REP['channels_other'] = dict(before=other, after=clean_other_channels(act, (grid[0], grid[-1])))
    removed = [x.name for x in bpy.data.actions if x is not act]   # hero output contract: ONE Action, the refined one, active
    for x in [x for x in bpy.data.actions if x is not act]:
        bpy.data.actions.remove(x)
    R.assign_action(arm, act)
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    REP['final']['other_actions_removed'] = removed
    json.dump(REP, open(out_json, 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print('REFINE final', json.dumps({k: v for k, v in REP['final'].items() if k not in ('peak_hand_raw',)}))
    print('REFINE saved', out_blend, out_json)
    if 'retime' in REP:
        rt = REP['retime']
        print('REFINE_HOLDS %s spans %d compressed %d speedup %.2f seconds %.3f -> %.3f hitL %.3f -> %.3f s hitR %.3f -> %.3f s end_vs_frame0_mm %s' % (
            clip, len(rt['spans']), len(rt['compressed']), rt['speedup'], rt['seconds_before'], rt['seconds_after'],
            peaks_raw['Left']['seconds'], peaks['Left']['seconds'], peaks_raw['Right']['seconds'], peaks['Right']['seconds'],
            REP.get('last_frame_vs_frame0', {}).get('mesh_mm_max')), flush=True)
    print('REFINE_GATE %s seam %.2f foot_drift_mm %s toe_min_mm %.1f peakhand_L %d peakhand_R %d%s' % (
        clip, seam, ('%.1f' % drift_after) if drift_after == drift_after else 'n/a', (toe_min - a.floor) * 1000,
        peaks['Left']['sample'], peaks['Right']['sample'],
        (' yaw_locked %.1f' % REP['yaw_lock']['removed_deg_span']) if 'yaw_lock' in REP else ''), flush=True)


if __name__ == '__main__':
    main()
