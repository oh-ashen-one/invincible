#!/usr/bin/env python3
"""Round 10: does an enemy's hand weapon (bat, pipe, pistol) pass through the hero's body?  (CPU, numpy; the REAL skinned meshes posed like the engine, see preview_cpu.py)

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.  Critic r09: 'the hero's left arm is an untextured grey limb' = the Brute's steel pipe passing through
the hero's back (a grey L-shaped elbow fitting sticking out of his flank).  The weapon vertices of each armed enemy (the vertices skinned to hand.R that are > 0.17 m from the wrist in the
bind pose) are tested against capsules round the hero's torso / head / limbs; a frame is a hit when > MIN_VERTS weapon vertices lie deeper than MARGIN cm inside a capsule.
  python3 tools/ue_char/fight/weapon_clip_check.py [out.json] [--step 0.05] [--t0 0.65] [--t1 24.65] [--pipe-scale 1.0] [--bat-scale 1.0]
Needs P2_SCRATCH (the ueimport GLBs of the last build).  Prints the hit intervals per weapon."""
import os, sys, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.argv_saved = list(sys.argv)
import preview_cpu as pc  # noqa: E402

MARGIN, MIN_VERTS, WRIST_R = 1.0, 6, 0.17
ARMED = {'Fight_Thug': 'bat', 'Fight_Brute': 'pipe', 'Fight_Hood': 'pistol'}
# (bone a, bone b, radius cm)
CAPS = [('hips', 'spine', 15.0), ('spine', 'spine1', 16.0), ('spine1', 'spine2', 16.5), ('spine2', 'neck', 15.5), ('neck', 'head', 10.0),
        ('upperArm.L', 'forearm.L', 5.5), ('forearm.L', 'hand.L', 4.5), ('upperArm.R', 'forearm.R', 5.5), ('forearm.R', 'hand.R', 4.5),
        ('thigh.L', 'shin.L', 8.5), ('shin.L', 'foot.L', 5.5), ('thigh.R', 'shin.R', 8.5), ('shin.R', 'foot.R', 5.5)]
BONES = sorted({b for c in CAPS for b in c[:2]})


def seg_dist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab + 1e-9), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


class Weapon:
    def __init__(self, label, scale=1.0):
        self.ac = pc.Actor(label); ac = self.ac
        names = [ac.doc.j['nodes'][i]['name'] for i in ac.joints]; hr = names.index('hand.R')
        dom = ac.J[np.arange(len(ac.J)), np.argmax(ac.W, 1)]
        wrist = np.linalg.inv(ac.ibm[hr])[:3, 3]
        far = np.linalg.norm(ac.P - wrist, axis=1) > WRIST_R
        self.mask = (dom == hr) & far
        self.scale = scale; self.wrist = wrist

    def verts(self, t):
        P, _ = self.ac.world_mesh(t)            # right-handed (x, -y_ue, z)
        W = P[self.mask].copy(); W[:, 1] *= -1
        return W


def hero_caps(hero, t):
    _, _, b = hero.world_bones(t, BONES)
    return [(np.array(b[a]), np.array(b[c]), r) for a, c, r in CAPS]


def main():
    a = [x for x in sys.argv_saved[1:]]
    opt = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
    out = a[0] if a and not a[0].startswith('--') else None
    step, t0, t1 = opt('--step', 0.05), opt('--t0', 0.65), opt('--t1', 24.65)
    hero = pc.Actor('Fight_Hero'); ws = {l: Weapon(l) for l in ARMED}
    res = {l: [] for l in ARMED}
    n = int(round((t1 - t0) / step)) + 1
    for k in range(n):
        t = t0 + k * step; caps = hero_caps(hero, t)
        for l, w in ws.items():
            V = w.verts(t); depth = np.zeros(len(V))
            for pa, pb, r in caps: depth = np.maximum(depth, r - seg_dist(V, pa, pb))
            inside = int((depth > MARGIN).sum()); res[l].append((round(t, 3), inside, round(float(depth.max()), 1)))
    summary = {}
    for l, rows in res.items():
        hits = [r for r in rows if r[1] > MIN_VERTS]; iv = []
        for r in hits:
            if iv and r[0] - iv[-1][1] < step * 1.5: iv[-1][1] = r[0]; iv[-1][2] = max(iv[-1][2], r[2])
            else: iv.append([r[0], r[0], r[2]])
        summary[l] = {'weapon': ARMED[l], 'frames_total': len(rows), 'frames_hit': len(hits), 'seconds_hit': round(len(hits) * step, 2), 'max_depth_cm': max(r[2] for r in rows), 'intervals': iv}
        print('%-12s %-6s hit frames %3d / %d (%.2f s), max depth %.1f cm, intervals (start, end, depth): %s' % (l, ARMED[l], len(hits), len(rows), len(hits) * step, summary[l]['max_depth_cm'], [(x[0], x[1], x[2]) for x in iv]))
    if out: json.dump({'step': step, 'summary': summary, 'rows': res}, open(out, 'w'))


if __name__ == '__main__':
    main()
