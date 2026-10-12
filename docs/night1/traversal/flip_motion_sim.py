# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 18: OFFLINE estimator of the critic r17 "alive limbs" test for every flip program, before an engine run.
#   python3 flip_motion_sim.py <HeroFlips_report.json> [program ...]
# Replicates WebTravFlips (program table, momentum integration, shape blend with FlipLead / FlipLag, shape-axis compensation) and
# the anim instance's layering (upper body = blend of the A/B clips at their hold progress, legs = the lagging blend), takes the
# per-frame joint positions that make_flip_shapes.py dumps (body frame, relative to the hips), rotates them by the program's
# pitch / twist and reports, per program, the critic's test: limb_z (hand / foot height over the hips, world up) sampled every
# 0.1 s from the release to the catch -- a sample FAILS when no limb_z component changed by >= 0.10 since the previous sample.
# All six 1/60 s sampling phases are checked (the rendered telemetry is sampled every 6th frame from whatever phase the trick starts on).
# Approximations: BodyQ (facing / lean) is ignored, poses are blended in joint POSITIONS (UE blends local rotations), the node
# crossfade into the trick and the catch's spring-back are not modelled. Use it to design; the engine probe (pose_check.py) decides.
import json
import math
import sys

INERTIA = {'Tuck': 1.0, 'Pike': 1.35, 'Layout': 3.2, 'Swan': 7.5, 'Pencil': 9.0, 'Straddle': 7.5, 'Throne': 9.0, 'Twist': 3.5,
           'Reach': 7.0, 'Kickout': 10.5}
AXIS = {'Tuck': 20.0, 'Pike': 22.0, 'Swan': -15.0, 'Kickout': -6.0, 'Reach': 3.0}
# (name, pitch, [(shape, dur, twist, easeIn, easeOut)], catchOpen) -- keep in step with WebTravFlips.cpp Programs()
PROGRAMS = {
    'backDouble': (-720.0, [('Tuck', 1.20, 0, 0.85, 0.8), ('Kickout', 0.60, 0, 0, 0)], 0.2),
    'frontPikeSwan': (360.0, [('Pike', 0.40, 0, 1.3, 0.3), ('Swan', 0.55, 0, 0, 0), ('Tuck', 0.38, 0, 1.2, 0.7), ('Reach', 0.26, 0, 0, 0)], 0.16),
    'corkscrew': (360.0, [('Layout', 0.31, 0, 0, 0), ('Twist', 0.42, 360, 0, 0), ('Straddle', 0.36, 0, 0, 0), ('Tuck', 0.34, 0, 1.2, 0.7),
                          ('Reach', 0.24, 0, 0, 0)], 0.16),
    'backSingle': (-360.0, [('Tuck', 0.32, 0, 0.5, 0.3), ('Pencil', 0.36, 0, 0, 0), ('Tuck', 0.32, 0, 0.3, 0.6), ('Reach', 0.24, 0, 0, 0)], 0.16),
}
LEAD, LAG = 0.04, 0.07
BPRE, BPOST, ENVIN, ENVOUT, EASEW = 0.06, 0.11, 0.12, 0.22, 0.45
LEG = ('thigh', 'shin', 'foot', 'toe', 'glute')
LIMBS = ('hand.L', 'hand.R', 'foot.L', 'foot.R')


def sm(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class Prog:
    def __init__(self, name):
        self.name = name
        self.pitch, self.segs, self.catch_open = PROGRAMS[name]
        self.dur = sum(s[1] for s in self.segs)
        self.starts = []
        a = 0.0
        for s in self.segs:
            self.starts.append(a)
            a += s[1]
        n = int(math.ceil(self.dur * 240)) + 1
        g, acc = [0.0], 0.0
        for i in range(1, n + 1):
            t = (i - 0.5) / 240
            acc += self.env(t) / self.inertia(t) / 240
            g.append(acc)
        gend = g[min(n, int(math.ceil(self.dur * 240)))]
        self.L = self.pitch / gend
        self.G = [v * self.L for v in g]

    def seg_at(self, t):
        acc = 0.0
        for i, s in enumerate(self.segs):
            acc += s[1]
            if t < acc:
                return i
        return len(self.segs) - 1

    def seg_inertia(self, k, t):
        sh, d, _, ei, eo = self.segs[k]
        u = min(max((t - self.starts[k]) / max(0.05, d), 0.0), 1.0)
        return INERTIA[sh] * (1 + ei * (1 - sm(u / EASEW)) + eo * (1 - sm((1 - u) / EASEW)))

    def inertia(self, t):
        t = min(max(t, 0.0), self.dur - 1e-4)
        k = self.seg_at(t)
        s0 = self.starts[k]
        s1 = s0 + self.segs[k][1]
        if k > 0 and t < s0 + BPOST:
            w = sm((t - (s0 - BPRE)) / (BPRE + BPOST))
            return self.seg_inertia(k - 1, t) * (1 - w) + self.seg_inertia(k, t) * w
        if k + 1 < len(self.segs) and t > s1 - BPRE:
            w = sm((t - (s1 - BPRE)) / (BPRE + BPOST))
            return self.seg_inertia(k, t) * (1 - w) + self.seg_inertia(k + 1, t) * w
        return self.seg_inertia(k, t)

    def env(self, t):
        return (0.35 + 0.65 * sm(t / ENVIN)) * (0.12 + 0.88 * sm((self.dur - t) / ENVOUT))

    def shape_at(self, t):
        t = min(max(t, 0.0), self.dur - 1e-4)
        k = self.seg_at(t)
        s0 = self.starts[k]
        s1 = s0 + self.segs[k][1]

        def hold(j, tt):
            return min(max((tt - self.starts[j]) / max(0.05, self.segs[j][1]), 0.0), 1.0)
        if k > 0 and t < s0 + BPOST:
            return self.segs[k - 1][0], self.segs[k][0], sm((t - (s0 - BPRE)) / (BPRE + BPOST)), 1.0, hold(k, t)
        if k + 1 < len(self.segs) and t > s1 - BPRE:
            return self.segs[k][0], self.segs[k + 1][0], sm((t - (s1 - BPRE)) / (BPRE + BPOST)), hold(k, t), 0.0
        return self.segs[k][0], self.segs[k][0], 0.0, hold(k, t), hold(k, t)

    def sample(self, t):
        tc = min(max(t, 0.0), self.dur)
        x = tc * 240
        i0 = min(max(int(math.floor(x)), 0), len(self.G) - 2)
        f = min(max(x - i0, 0.0), 1.0)
        pitch = self.G[i0] + (self.G[i0 + 1] - self.G[i0]) * f
        tw, st = 0.0, 0.0
        for s in self.segs:
            if s[2]:
                u = min(max((tc - st) / max(0.05, s[1]), 0.0), 1.0)
                tw += s[2] * 0.5 * (1 - math.cos(math.pi * u))
            st += s[1]
        up = self.shape_at(t + LEAD)
        lg = self.shape_at(t - LAG)
        axis = AXIS.get(up[0], 0.0) * (1 - up[2]) + AXIS.get(up[1], 0.0) * up[2]
        return pitch, tw, up, lg, axis


def clip_pose(frames, shape, hold):
    seq = frames['flip' + shape]
    x = min(max(hold, 0.0), 1.0) * (len(seq) - 1)
    i = min(int(x), len(seq) - 2)
    f = x - i
    return {b: [seq[i][b][c] * (1 - f) + seq[i + 1][b][c] * f for c in range(3)] for b in seq[i]}


def blend(pa, pb, w):
    return {b: [pa[b][c] * (1 - w) + pb[b][c] * w for c in range(3)] for b in pa}


def body_pose(frames, up, lg):
    A, B, W, HA, HB = up
    LA, LB, LW, LHA, LHB = lg
    U = blend(clip_pose(frames, A, HA), clip_pose(frames, B, HB), W)
    Lg = blend(clip_pose(frames, LA, LHA), clip_pose(frames, LB, LHB), LW)
    return {b: (Lg[b] if b.split('.')[0] in LEG else U[b]) for b in U}


def world(v, pitch_deg, twist_deg):
    # body (forward, up, x(+L)) -> UE (X fwd, Y right, Z up); Q = Ry(pitch) * Rz(twist)
    x, y, z = v[0], -v[2], v[1]
    a = math.radians(twist_deg)
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    p = math.radians(pitch_deg)
    x, z = x * math.cos(p) + z * math.sin(p), -x * math.sin(p) + z * math.cos(p)
    return x, y, z


def run(frames, name, verbose=True):
    P = Prog(name)
    t_end = P.dur - P.catch_open
    rows = []
    for i in range(int(t_end * 60) + 1):
        t = i / 60.0
        pitch, tw, up, lg, axis = P.sample(t)
        pose = body_pose(frames, up, lg)
        rot = pitch - axis * sm(t / 0.15)
        lz = [world(pose[l], rot, tw)[2] for l in LIMBS]
        zs = [world(v, rot, tw)[2] for v in pose.values()]
        rows.append((t, lz, max(zs) - min(zs) + 0.2, up[0] if up[2] < 0.5 else up[1]))
    worst, fails_all, tight = 0, [], []
    for ph in range(6):
        smp = rows[ph::6]
        fails = []
        for i in range(len(smp) - 1):
            dmax = max(abs(smp[i + 1][1][k] - smp[i][1][k]) for k in range(4))
            if dmax < 0.10:
                fails.append((round(smp[i][0], 2), round(dmax, 3), smp[i][3]))
            elif dmax < 0.14:
                tight.append((round(smp[i][0], 2), round(dmax, 3), smp[i][3]))
        fails_all.append(fails)
        worst = max(worst, len(fails))
    nsamp = len(rows[0::6]) - 1
    ext = {}
    for t, _, e, sh in rows:
        ext.setdefault(sh, []).append(e)
    if verbose:
        print('%-14s dur %.2f catch %.2f | samples/phase %d | slow samples per phase %s' % (name, P.dur, t_end, nsamp, [len(f) for f in fails_all]))
        for ph, f in enumerate(fails_all):
            if f:
                print('    phase %d: %s' % (ph, f))
        if tight:
            print('    tight (.10-.14): ' + str(sorted(set(tight))))
        print('    z-extent (m, +0.2 pad) by shape: ' + ', '.join('%s %.2f-%.2f' % (k, min(v), max(v)) for k, v in ext.items()))
    return worst


if __name__ == '__main__':
    rep = json.load(open(sys.argv[1]))
    frames = rep['frames']
    names = sys.argv[2:] or ['backDouble', 'frontPikeSwan', 'corkscrew']
    tot = sum(run(frames, n) for n in names)
    print('TOTAL worst-phase slow samples:', tot)
