# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C r01: offline estimate of the L line (critic pose.py rule: in every 0.1 s sample of a trick some hand / foot height relative to
# the hips moves >= 0.10 m). Combines flip_sim.py's momentum timeline (pitch, twist, shape timing with the arm lead / leg lag) with the keyed
# clips' body-frame hand / foot positions from make_flip_shapes.py's report (frames 0..30 of each 1 s clip, played over the shape's hold).
# Ignores the anim instance's IK / additive layers and the release orientation: a screening tool, the engine probe is the measurement.
#   python3 tools/tricks/limb_sim.py <HeroFlips_report.json> [--validate <telemetry.csv>]
import csv, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flip_sim as FS

ENDS = ('hand.L', 'hand.R', 'foot.L', 'foot.R')
UPPER = ('hand.L', 'hand.R')


def clip_pos(R, clip, u, bone):
    fr = R['frames']['flip' + clip]
    x = min(max(u, 0.0), 1.0) * (len(fr) - 1)
    i = min(int(x), len(fr) - 2); w = x - i
    a, b = fr[i][bone], fr[i + 1][bone]
    return [a[k] + (b[k] - a[k]) * w for k in range(3)]


def shape_at(P, t):
    """(A, B, W, HA, HB) like WebFlips::ShapeAt"""
    t = min(max(t, 0.0), P.dur - 1e-4)
    k = P.seg_at(t); s0 = P.starts[k]; s1 = s0 + P.segs[k]['dur']
    hold = lambda j, tt: min(1.0, max(0.0, (tt - P.starts[j]) / max(0.05, P.segs[j]['dur'])))
    if k > 0 and t < s0 + FS.BPOST:
        return P.segs[k - 1]['shape'], P.segs[k]['shape'], FS.smooth((t - (s0 - FS.BPRE)) / (FS.BPRE + FS.BPOST)), 1.0, hold(k, t)
    if k + 1 < len(P.segs) and t > s1 - FS.BPRE:
        return P.segs[k]['shape'], P.segs[k + 1]['shape'], FS.smooth((t - (s1 - FS.BPRE)) / (FS.BPRE + FS.BPOST)), hold(k, t), 0.0
    return P.segs[k]['shape'], P.segs[k]['shape'], 0.0, hold(k, t), hold(k, t)


def body_pos(R, P, t, bone, lead=0.04, lag=0.07):
    tt = t + lead if bone in UPPER else t - lag
    A, B, W, HA, HB = shape_at(P, tt)
    pa, pb = clip_pos(R, A, HA, bone), clip_pos(R, B, HB, bone)
    return [pa[k] + (pb[k] - pa[k]) * W for k in range(3)]


def pitch_twist(P, t):
    """cumulative pitch (deg, + = front) and twist (deg) at t"""
    n = max(1, int(t * 240)); dt = t / n
    ph = sum(P.rate((i + 0.5) * dt) for i in range(n)) * dt
    tw, st = 0.0, 0.0
    for s in P.segs:
        if s['tw']:
            u = min(1.0, max(0.0, (t - st) / max(0.05, s['dur']))); tw += s['tw'] * 0.5 * (1 - math.cos(math.pi * u))
        st += s['dur']
    return ph, tw


def world_z(p, ph, tw, sgn=1.0):
    f, u, x = p
    c, s = math.cos(math.radians(tw)), math.sin(math.radians(tw))
    f2 = f * c - x * s
    a = math.radians(ph)
    return u * math.cos(a) - sgn * f2 * math.sin(a)


def series(R, P, lead=0.04, lag=0.07, dt=1 / 60.0):
    out = []
    t, ph, sub = 0.0, 0.0, 4
    while t < P.dur:
        tw = twist(P, t)
        out.append((t, [world_z(body_pos(R, P, t, b, lead, lag), ph, tw) for b in ENDS], A_shape(P, t)))
        for i in range(sub): ph += P.rate(t + (i + 0.5) * dt / sub) * dt / sub
        t += dt
    return out


def twist(P, t):
    tw, st = 0.0, 0.0
    for s in P.segs:
        if s['tw']:
            u = min(1.0, max(0.0, (t - st) / max(0.05, s['dur']))); tw += s['tw'] * 0.5 * (1 - math.cos(math.pi * u))
        st += s['dur']
    return tw


def A_shape(P, t): return P.segs[P.seg_at(t)]['shape']


def lcheck(ser):
    rows = ser[::6]
    slow = []
    for a, b in zip(rows, rows[1:]):
        d = max(abs(x - y) for x, y in zip(a[1], b[1]))
        if d < 0.10: slow.append((a[0], d, a[2]))
    return slow


def validate(R, tel, margin=0.10):
    """the keyed clips of report R replayed on a capture's MEASURED program pitch / twist (telemetry flip_pitch_deg / flip_twist_deg): the
    L rule at every 0.1 s sampling phase (6 offsets), against the measured limb_z of the same capture"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tricks_check as TC
    progs = {p['name']: p for p in FS.parse(FS.SRC)}
    T = list(csv.DictReader(open(tel)))
    I = TC.instances(T)
    slow_m, slow_p, n, worst = 0, 0, 0, []
    LL = [(0.04, 0.07)] if not os.environ.get('SCAN') else [(a, b) for a in (0.02, 0.05, 0.08) for b in (0.05, 0.09, 0.13)]
    for c in I:
        if c['prog'] not in progs: continue
        P = FS.Prog(progs[c['prog']], c['scale'])
        dur = P.dur
        Zs = [[[world_z(body_pos(R, P, min(ft, dur), b, le, la), float(T[i]['flip_pitch_deg']), float(T[i]['flip_twist_deg'])) for b in ENDS]
               for i, ft in c['rows']] for le, la in LL]
        M = [[float(x) for x in T[i]['limb_z'].split()] for i, _ in c['rows']]
        for k in range(len(M) - 6):
            if c['rows'][k + 6][1] > dur: continue   # past the program end (the ping-pong is not modelled)
            dp = min(max(abs(x - y) for x, y in zip(Z[k], Z[k + 6])) for Z in Zs); dm = max(abs(x - y) for x, y in zip(M[k], M[k + 6]))
            n += 1; slow_p += dp < margin; slow_m += dm < margin
            if dp < margin: worst.append((dp, c['prog'], round(c['rows'][k][1], 2), T[c['rows'][k][0]]['flip_shape']))
            if dm < margin: print('   measured slow %-16s t0 %.2f flip_t %.2f / dur %.2f  %-8s %.3f (model %.3f)' % (c['prog'], c['t0'], c['rows'][k][1], P.dur, T[c['rows'][k][0]]['flip_shape'], dm, dp))
    worst.sort()
    print('validate %s: %d frame pairs 0.1 s apart (all phases); slow (< %.2f m): measured %d, model %d' % (os.path.basename(tel), n, margin, slow_m, slow_p))
    agg = {}
    for d, p, ft, sh in worst: agg.setdefault((p, sh), []).append((ft, d))
    for (p, sh), v in sorted(agg.items(), key=lambda x: -len(x[1])):
        print('   %-16s %-8s %3d pairs, t %.2f-%.2f, min %.3f' % (p, sh, len(v), min(x[0] for x in v), max(x[0] for x in v), min(x[1] for x in v)))


def main():
    R = json.load(open(sys.argv[1]))
    if '--validate' in sys.argv:
        validate(R, sys.argv[sys.argv.index('--validate') + 1], float(os.environ.get('MARGIN', '0.10'))); return
    progs = FS.parse(FS.SRC)
    worst_all = 0
    for p in progs:
        if p['name'] == 'wallFront': continue
        line = []
        for sc in (0.85, 1.0, 1.2):
            for lead, lag in ((0.02, 0.05), (0.04, 0.07), (0.08, 0.11)):
                P = FS.Prog(p, sc)
                for off in range(6):   # sample phase vs the 0.1 s grid
                    ser = series(R, P, lead, lag)[off:]
                    sl = lcheck(ser)
                    if sl: line.append((sc, lead, off, sl))
        worst_all += len(line)
        if line:
            print('%-16s %d slow configs; e.g. %s' % (p['name'], len(line), '; '.join('sc %.2f lead %.2f off %d: %s' % (a, b, c, ' '.join('%.2f/%.3f/%s' % s for s in d[:3])) for a, b, c, d in line[:4])))
        else:
            print('%-16s no slow samples (3 scales x 3 lead/lag x 6 phases)' % p['name'])
    print('TOTAL slow configs', worst_all)


if __name__ == '__main__':
    main()
