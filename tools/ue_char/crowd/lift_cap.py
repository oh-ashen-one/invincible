"""Round 09: cap the swing-foot lift of the crowd walk clips (numpy; used by eval/citizen_rig.load_people).

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

Critic r08: 'the hijab walker's rear shin goes horizontal at 18 % of stature (1080 frame 0.25 s, 7.0 s)'; 'cap the civilian swing-foot height at 10 % of stature'.
The shipped crowd walks kick the rear foot up to 0.32 - 0.44 m (walkBrisk) above the ankle's standing height.  For every walk clip and each leg the knee flexion is
scaled back (the shin and the foot rotate about the knee, the thigh is untouched, the planted foot is never affected) so that the ankle rises at most CAP_STATURE
x stature above its lowest point, with a smooth saturation (tanh) so no frame pops.  The rigid chain thigh -> shin -> foot of the baked skinning matrices is asserted.
  python3 tools/ue_char/crowd/lift_cap.py          prints the ankle lift per walk clip before / after
"""
import json, os, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
NPC = os.path.join(ROOT, 'public/assets/city/npc')
WALKS = ('walk', 'walkF', 'walkBrisk', 'walkStroll', 'walkOld')
STATURE = 1.72          # the crowd skeleton's standing height (m): hips 0.92 .. head top ~1.75 (people.json)
CAP_STATURE = 0.10      # swing-foot lift cap, fraction of stature
SOFT = 0.04             # m: saturation starts this far below the cap


def _rot_vec(R):
    """Rotation matrix -> rotation vector."""
    c = np.clip((np.trace(R) - 1) / 2, -1, 1); a = np.arccos(c)
    if a < 1e-9: return np.zeros(3)
    ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    n = np.linalg.norm(ax)
    if n < 1e-9:
        # 180 deg: axis from the symmetric part
        w, v = np.linalg.eigh((R + R.T) / 2 - np.eye(3) * (c)); return v[:, -1] * a
    return ax / n * a


def _rot_from_vec(v):
    a = np.linalg.norm(v)
    if a < 1e-12: return np.eye(3)
    k = v / a; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def cap_lift(p, M, stature=STATURE, cap=CAP_STATURE, soft=SOFT, clips=WALKS):
    """M: (frames, nb, 4, 4) skinning matrices; returns a modified copy and a report {clip: (lift_before, lift_after)} (m above the lowest ankle)."""
    M = M.copy(); names = [b['name'] for b in p['bones']]; bones = p['bones']
    rep = {}
    for cn in clips:
        cl = p['clips'][cn]; r0, n = cl['row'], cl['len']
        lo = 1e9; hi_b = 0; hi_a = 0
        for side in 'LR':
            ti, si, fi = names.index('thigh' + side), names.index('shin' + side), names.index('foot' + side)
            hs, hf = np.array(bones[si]['head']), np.array(bones[fi]['head'])
            ank = [M[r0 + f, fi] @ np.r_[hf, 1.0] for f in range(n)]
            lo = min(lo, min(a[1] for a in ank))
        for side in 'LR':
            ti, si, fi = names.index('thigh' + side), names.index('shin' + side), names.index('foot' + side)
            hs, hf = np.array(bones[si]['head']), np.array(bones[fi]['head'])
            for f in range(n):
                Mt, Ms, Mf = M[r0 + f, ti], M[r0 + f, si], M[r0 + f, fi]
                knee = (Ms @ np.r_[hs, 1.0])[:3]; ank = (Mf @ np.r_[hf, 1.0])[:3]
                # rigid chain check: the foot follows the shin
                ank_chain = knee + Ms[:3, :3] @ (hf - hs)
                assert np.abs(ank_chain - ank).max() < 2e-3, (cn, side, f, ank_chain, ank)
                h = ank[1] - lo
                hi_b = max(hi_b, h)
                c = cap * stature; c0 = max(0.0, c - soft)
                ht = h if h <= c0 else c0 + (c - c0) * np.tanh((h - c0) / max(1e-6, c - c0))
                if ht >= h - 1e-5:
                    hi_a = max(hi_a, h); continue
                # relative knee rotation (thigh frame); scale it by s in [0, 1] until the ankle reaches the target height
                Rt, Rs = Mt[:3, :3], Ms[:3, :3]
                rel = _rot_vec(Rt.T @ Rs)
                def ankle_y(s):
                    Rs2 = Rt @ _rot_from_vec(rel * s)
                    return (knee + Rs2 @ (hf - hs))[1] - lo
                a_, b_ = 0.0, 1.0
                for _ in range(40):
                    m = (a_ + b_) / 2
                    if ankle_y(m) > ht: b_ = m
                    else: a_ = m
                s = a_
                Rs2 = Rt @ _rot_from_vec(rel * s)
                ank2 = knee + Rs2 @ (hf - hs)
                Rf2 = Rs2 @ Rs.T @ Mf[:3, :3]
                Ms2 = Ms.copy(); Ms2[:3, :3] = Rs2; Ms2[:3, 3] = knee - Rs2 @ hs
                Mf2 = Mf.copy(); Mf2[:3, :3] = Rf2; Mf2[:3, 3] = ank2 - Rf2 @ hf
                M[r0 + f, si], M[r0 + f, fi] = Ms2, Mf2
                hi_a = max(hi_a, ank2[1] - lo)
        rep[cn] = (hi_b, hi_a)
    return M, rep


if __name__ == '__main__':
    p = json.load(open(os.path.join(NPC, 'people.json')))
    A = np.frombuffer(open(os.path.join(NPC, 'people.bin'), 'rb').read(), np.float32, p['frames'] * p['nb'] * 12, p['anim']).reshape(p['frames'], p['nb'], 3, 4)
    M = np.zeros((p['frames'], p['nb'], 4, 4)); M[:, :, :3, :] = A; M[:, :, 3, 3] = 1
    M2, rep = cap_lift(p, M)
    for cn, (b, a) in rep.items():
        print('%-11s ankle lift above the lowest ankle: %.3f m (%.1f %% of stature) -> %.3f m (%.1f %%)' % (cn, b, 100 * b / STATURE, a, 100 * a / STATURE))
