#!/usr/bin/env python3
"""Round 09: in-place hit-reaction clips for the street enemies (numpy, no Blender, no engine).

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

The browser game's thug clips carry their travel in the pelvis ('hips' translation x / z): thugStumbleBack ends 0.30 m behind the start,
thugKnockdown 0.53 m, the hero's getUp starts 0.53 m behind where it ends.  Played as they are, the actor stays where it is while the pose
walks away from it, and every hand-over to the guard idle snaps the pelvis back (a shuffling slide).  This tool writes the same clips
IN PLACE: the pelvis x / z is held at the guard value (0, -0.025 m) and the travel goes into clip_motion.json, which the choreography
(tools/ue_char/fight/choreo.py) turns into the actor's path, so the world-space motion is exactly the original clip's and the pose returns to
the guard without a pop.  Only the pelvis translation changes; every rotation, the pelvis height and every other bone are copied.

  python3 tools/ue_char/fight/make_fight_clips.py [--out <dir>]      (reads public/assets/thug.glb + spiderman.glb and $P2_SCRATCH/ueimport/SK_Thug.glb)
  writes  $P2_SCRATCH/ueimport/SK_Street_Fight.glb   (mesh of SK_Thug + the 5 clips below; the build imports the clips and deletes the mesh)
          tools/ue_char/fight/clip_motion.json        (per clip: duration, per-key hips travel relative to the clip start, m)
Clips: hitBack (thugStumbleBack), hitLeft (thugStumbleLeft), hitRight (thugStumbleRight), down (thugKnockdown), getUp (hero getUp: a backward roll over the head),
       getUp2 (round 10, a SECOND get-up: an elbow-propped sit-up from the knocked-down pose, rising through a squat to the guard; authored here from the thug's own
       knockdown pose, a spine flexion on top of it, and the second half of the thug's thugGetUp; the original thugGetUp is NOT used as it is: its pelvis dips 0.4 - 1.0 m below the floor).
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'heroanim'))
from p2paths import WT, SCRATCH  # noqa: E402
from ganim import Doc  # noqa: E402

GUARD_XZ = np.array([0.0, -0.025])       # pelvis x / z of the guard idle (thugIdle): every in-place clip holds it
SRC = [  # (new name, source file, source clip)
    ('hitBack', 'thug', 'thugStumbleBack'), ('hitLeft', 'thug', 'thugStumbleLeft'), ('hitRight', 'thug', 'thugStumbleRight'),
    ('down', 'thug', 'thugKnockdown'), ('getUp', 'hero', 'getUp')]


def _by_name(doc, clip, t):
    L = doc.sample(doc.tracks(clip), t)
    return {doc.names[i]: v for i, v in L.items()}


def _blend(A, B, u):
    from ganim import qslerp
    return {n: (A[n][0] * (1 - u) + B[n][0] * u, qslerp(A[n][1], B[n][1], u), A[n][2] * (1 - u) + B[n][2] * u) for n in A}


def _smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def compose_getup2(thug_src, fps=30.0, T1=0.40, X=0.55, lie_t=0.80, gu_start=0.80, floor=0.02):
    """Round 10: a sit-up get-up on the thug skeleton.  Phase 1 (0 - T1): from the knocked-down pose (thugKnockdown at lie_t) the three spine joints flex about their local X
    (+24 / +24 / +20 deg, neck -10: the torso props itself up on the elbows).  Phase 2: a smooth cross-fade (X s) into thugGetUp from gu_start (the crouch with the hands
    on the thighs) which then plays out to the guard stance.  A floor constraint lifts the pelvis so no foot / toe / hand / head joint goes below `floor` m.
    Returns (times, {name: (K,3) translation} for the hips, {name: (K,4) rotations}, raw hips translation (K,3))."""
    from ganim import qmul, qaxis
    lie = _by_name(thug_src, 'thugKnockdown', lie_t); sit = dict(lie)
    for j, ang in (('spine', 24), ('spine1', 24), ('spine2', 20), ('neck', -10)):
        t_, q_, s_ = sit[j]; sit[j] = (t_, qmul(q_, qaxis((1, 0, 0), np.radians(ang))), s_)
    T = T1 + (thug_src.duration('thugGetUp') - gu_start)
    T = round(T * fps) / fps                       # Interchange refuses a clip whose length is not a whole number of 30 fps frames (r10: 1.02 s failed to import)
    times = np.arange(0, int(round(T * fps)) + 1) / fps
    poses = []
    for t in times:
        P1 = _blend(lie, sit, _smooth(t / T1) if t < T1 else 1.0)
        B = _by_name(thug_src, 'thugGetUp', min(gu_start + max(0.0, t - T1), thug_src.duration('thugGetUp')))
        poses.append(_blend(P1, B, _smooth((t - T1) / X) if t > T1 else 0.0))
    # floor constraint: world heights of the extremities through the thug skeleton
    names = list(poses[0].keys()); idx = thug_src.idx
    for k, Ln in enumerate(poses):
        L = {idx[n]: v for n, v in Ln.items() if n in idx}
        R = thug_src.rest_local()
        for i in R:
            if i not in L: L[i] = R[i]
        Wm = thug_src.world(L)
        ymin = min(Wm[idx[n]][1, 3] for n in ('toe.L', 'toe.R', 'foot.L', 'foot.R', 'hand.L', 'hand.R', 'head'))
        if ymin < floor:
            t_, q_, s_ = Ln['hips']; t_ = t_.copy(); t_[1] += floor - ymin; Ln['hips'] = (t_, q_, s_)
    # smooth the correction (one pass of a 3-key box filter on hips y) so the pelvis does not jitter
    hy = np.array([p['hips'][0][1] for p in poses]); hy2 = hy.copy()
    for k in range(1, len(hy) - 1): hy2[k] = max(hy[k], (hy[k - 1] + hy[k] + hy[k + 1]) / 3.0)
    for k, Ln in enumerate(poses):
        t_, q_, s_ = Ln['hips']; t_ = t_.copy(); t_[1] = hy2[k]; Ln['hips'] = (t_, q_, s_)
    rot = {n: np.array([p[n][1] for p in poses]) for n in names}
    hips_t = np.array([p['hips'][0] for p in poses])
    return times, rot, hips_t


def main(out_dir=None):
    thug_src = Doc(os.path.join(WT, 'public/assets/thug.glb'))
    hero_src = Doc(os.path.join(WT, 'public/assets/spiderman.glb'))
    base = Doc(os.path.join(SCRATCH, 'ueimport', 'SK_Thug.glb'))      # stripped thug mesh + skeleton (prep_glbs.py)
    hips_base = base.idx['hips']
    by_name = {nm: i for i, nm in enumerate(base.names)}
    base.j['animations'] = []
    motion = {}
    for name, which, clip in SRC:
        d = thug_src if which == 'thug' else hero_src
        tr = d.tracks(clip)
        T = d.duration(clip)
        chans, samps = [], []
        times = None
        for node, chs in tr.items():
            nm = d.names[node]
            if nm not in by_name:
                continue
            for path, (t_, v_, interp) in chs.items():
                v = np.array(v_, float)
                if node == d.idx['hips'] and path == 'translation':
                    hips_t = t_.copy(); hips_raw = v.copy()
                    v = v.copy(); v[:, 0] = GUARD_XZ[0]; v[:, 2] = GUARD_XZ[1]
                ti = base._append(np.asarray(t_, np.float32).reshape(-1, 1), 'SCALAR')
                oi = base._append(v, {'translation': 'VEC3', 'rotation': 'VEC4', 'scale': 'VEC3'}[path])
                samps.append({'input': ti, 'output': oi, 'interpolation': 'LINEAR'})
                chans.append({'sampler': len(samps) - 1, 'target': {'node': by_name[nm], 'path': path}})
        base.j['animations'].append({'name': name, 'channels': chans, 'samplers': samps})
        rel = hips_raw[:, [0, 2]] - hips_raw[0, [0, 2]]          # travel relative to the clip start (m): x = the actor's LEFT, z = forward
        motion[name] = {'source': '%s:%s' % (which, clip), 'duration': float(T), 'times': [round(float(x), 5) for x in hips_t],
                        'dx_left': [round(float(x), 5) for x in rel[:, 0]], 'dz_fwd': [round(float(x), 5) for x in rel[:, 1]],
                        'hips_y': [round(float(x), 5) for x in hips_raw[:, 1]]}
        print('%-9s %-18s T=%.2f  K=%d  travel left %+.3f m, forward %+.3f m, hips y %.2f..%.2f' %
              (name, which + ':' + clip, T, len(hips_t), rel[-1, 0], rel[-1, 1], hips_raw[:, 1].min(), hips_raw[:, 1].max()))
    # ---- round 10: the second get-up (composite)
    times, rot, hips_t = compose_getup2(thug_src)
    chans, samps = [], []
    ti = base._append(np.asarray(times, np.float32).reshape(-1, 1), 'SCALAR')
    for nm, q in rot.items():
        if nm not in by_name: continue
        qi = base._append(q, 'VEC4'); samps.append({'input': ti, 'output': qi, 'interpolation': 'LINEAR'}); chans.append({'sampler': len(samps) - 1, 'target': {'node': by_name[nm], 'path': 'rotation'}})
    v = hips_t.copy(); raw = v.copy(); v[:, 0] = GUARD_XZ[0]; v[:, 2] = GUARD_XZ[1]
    oi = base._append(v, 'VEC3'); samps.append({'input': ti, 'output': oi, 'interpolation': 'LINEAR'}); chans.append({'sampler': len(samps) - 1, 'target': {'node': by_name['hips'], 'path': 'translation'}})
    base.j['animations'].append({'name': 'getUp2', 'channels': chans, 'samplers': samps})
    rel = raw[:, [0, 2]] - raw[0, [0, 2]]
    motion['getUp2'] = {'source': 'composite:thugKnockdown(lie)+spine flexion+thugGetUp(0.8-1.4)', 'duration': float(times[-1]), 'times': [round(float(x), 5) for x in times],
                        'dx_left': [round(float(x), 5) for x in rel[:, 0]], 'dz_fwd': [round(float(x), 5) for x in rel[:, 1]], 'hips_y': [round(float(x), 5) for x in raw[:, 1]]}
    print('%-9s %-18s T=%.2f  K=%d  travel left %+.3f m, forward %+.3f m, hips y %.2f..%.2f' % ('getUp2', 'composite', times[-1], len(times), rel[-1, 0], rel[-1, 1], raw[:, 1].min(), raw[:, 1].max()))
    out = os.path.join(out_dir or os.path.join(SCRATCH, 'ueimport'), 'SK_Street_Fight.glb')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    base.write(out)
    json.dump(motion, open(os.path.join(HERE, 'clip_motion.json'), 'w'), indent=1)
    print('wrote', out, os.path.getsize(out) // 1024, 'KB and clip_motion.json')


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[a.index('--out') + 1] if '--out' in a else None)
