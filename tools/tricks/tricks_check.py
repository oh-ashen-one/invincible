# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C round 1 checker: measures one capture against docs/night1/tricks/SPEC.md (PLAN-firstpass §4 Tricks).
#   python3 tools/tricks/tricks_check.py <telemetry.csv> [<pose.csv>]
# telemetry.csv = the capture's per-frame traversal telemetry (WebTravCharacter, -WHShotDir); pose.csv = the rendered-bone log of the
# SAME run (-WHTrickPose, WebTravFlips.cpp), joined to the telemetry row by the hero position (identical simulation state per frame).
# Lines:
#   P  distinct programs started in the clip (>= 10), each instance: start, observed length, duration scale, completed to the open-out
#   V1 same-type instances differ >= 40 deg/s in a 0.1 s sample (program rate at the same flip time, and the rendered body-axis rate)
#   V2 durations vary +-10-20 % (flip_scale per instance)
#   K  tight tuck: wrists <= .15 m from the shins, knees <= .25 m apart, held >= .25 s (every tuck hold >= .25 s long)
#   L  0 slow limb samples (critic pose.py rule as in docs/night1/traversal/limb_check.py: in every 0.1 s sample of a trick some limb_z
#      component moves >= .10)
#   pose lines (need pose.csv): G1 layout hip and knee angles >= 170 deg, G2 pointed toes (foot within 35 deg of the shin line),
#      G3 head spot (head-vs-chest flexion moves >= 15 deg in the open-out, before the catch), G4 open-out (last 0.15 s before the
#      program ends / is caught is an open shape turning <= 300 deg/s)
import csv, math, sys, os, collections

OPEN = {'Layout', 'Swan', 'Pencil', 'Straddle', 'Throne', 'Reach', 'Kickout'}


def f(x, d=float('nan')):
    try: return float(x)
    except Exception: return d


def instances(T):
    """split telemetry rows into trick instances (contiguous flip_prog runs with flip_t increasing)"""
    out, cur = [], None
    for i, r in enumerate(T):
        p, ft = r.get('flip_prog', ''), f(r.get('flip_t'), -1)
        if p and ft >= 0:
            if cur and cur['prog'] == p and ft >= cur['rows'][-1][1] - 1e-6:
                cur['rows'].append((i, ft))
            else:
                cur = dict(prog=p, rows=[(i, ft)]); out.append(cur)
        else:
            cur = None
    for c in out:
        r0 = T[c['rows'][0][0]]
        c['t0'] = f(r0['t']); c['len'] = c['rows'][-1][1]; c['scale'] = f(r0.get('flip_scale'), 1.0)
    return out


def ang(a, b):
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    if na < 1e-9 or nb < 1e-9: return float('nan')
    c = sum(x * y for x, y in zip(a, b)) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def sub(a, b): return [x - y for x, y in zip(a, b)]


def main(tel, pose=None):
    T = list(csv.DictReader(open(tel)))
    name = os.path.basename(tel).replace('_telemetry.csv', '')
    I = instances(T)
    out = []
    P = out.append
    P('== %s: %d rows, %.1f s, %d trick instances' % (name, len(T), f(T[-1]['t']), len(I)))
    # ---- P
    progs = collections.OrderedDict()
    for c in I: progs.setdefault(c['prog'], []).append(c)
    P('P  distinct programs: %d (>= 10 -> %s)' % (len(progs), 'PASS' if len(progs) >= 10 else 'FAIL'))
    for c in I:
        rws = [T[i] for i, _ in c['rows']]
        shapes = []
        for r in rws:
            s = r.get('flip_shape', '')
            if s and (not shapes or shapes[-1] != s): shapes.append(s)
        c['shapes'] = shapes
        c['open_end'] = shapes[-1] in OPEN if shapes else False
        P('   %6.2f s  %-16s len %.2f s  scale %.3f  shapes %s' % (c['t0'], c['prog'], c['len'], c['scale'], '>'.join(shapes)))
    # ---- V1
    P('V1 same-type pairs: max |rate difference| over 0.1 s samples at the same flip time (program rate / rendered axis rate)')
    v1 = []
    def series(c, col):
        d = {}
        for i, ft in c['rows']:
            d[round(ft * 10)] = f(T[i][col])
        return d
    def axis_rate(c):
        rows = c['rows']; d = {}
        for k in range(len(rows) - 6):
            i0, t0 = rows[k]; i1, t1 = rows[k + 6]
            a0, a1 = f(T[i0]['body_pitch_deg']), f(T[i1]['body_pitch_deg'])
            da = (a1 - a0 + 180) % 360 - 180
            if t1 > t0: d.setdefault(round(t0 * 10), da / (t1 - t0))
        return d
    for p, cs in progs.items():
        cs = [c for c in cs if c['scale'] > 0]   # wallFront (wall top-out) is one fixed program, not a release variant
        for a in range(len(cs)):
            for b in range(a + 1, len(cs)):
                sa, sb = series(cs[a], 'flip_rate_dps'), series(cs[b], 'flip_rate_dps')
                ks = sorted(set(sa) & set(sb))
                dm = max((abs(sa[k] - sb[k]) for k in ks), default=0)
                ra, rb = axis_rate(cs[a]), axis_rate(cs[b])
                kr = sorted(set(ra) & set(rb))
                dr = max((abs(ra[k] - rb[k]) for k in kr), default=0)
                v1.append((p, dm, dr))
                P('   %-16s %.2f s vs %.2f s: program %.0f deg/s, rendered %.0f deg/s over %d samples -> %s' % (p, cs[a]['t0'], cs[b]['t0'], dm, dr, len(ks), 'PASS' if dm >= 40 and dr >= 40 else 'FAIL'))
    P('V1 %s (%d same-type pairs, %d >= 40 deg/s on both)' % ('PASS' if v1 and all(x[1] >= 40 and x[2] >= 40 for x in v1) else ('FAIL' if v1 else 'NO PAIRS'), len(v1), sum(1 for x in v1 if x[1] >= 40 and x[2] >= 40)))
    # ---- V2
    sc = [c['scale'] for c in I if c['scale'] > 0]   # wallFront (wall top-out) is not a release variant: scale 0
    if sc:
        dev = [abs(s - 1) for s in sc]
        P('V2 duration scale per instance: min %.3f max %.3f (spread %+.0f %% .. %+.0f %%); instances deviating >= 10 %%: %d of %d; all within 22 %%: %s' % (
            min(sc), max(sc), (min(sc) - 1) * 100, (max(sc) - 1) * 100, sum(1 for d in dev if d >= 0.10), len(sc), all(d <= 0.22 for d in dev)))
        for p, cs in progs.items():
            s2 = [c['scale'] for c in cs if c['scale'] > 0]
            if len(s2) > 1:
                P('   %-16s scales %s (same-type spread %.0f %%)' % (p, ' '.join('%.3f' % x for x in s2), (max(s2) / min(s2) - 1) * 100))
        ok = min(sc) <= 0.9 and max(sc) >= 1.1 and all(d <= 0.22 for d in dev)
        P('V2 %s (needs instances below 0.90 and above 1.10, none beyond +-22 %%)' % ('PASS' if ok else 'FAIL'))
    # ---- K
    P('K  tuck holds (rows with flip_shape = Tuck on body and legs and tuck_w >= .99)')
    holds, run = [], []
    for c in I:
        run = []
        for i, ft in c['rows'] + [(None, None)]:
            r = T[i] if i is not None else None
            if r and r.get('flip_shape') == 'Tuck' and r.get('flip_shape_legs') == 'Tuck' and f(r.get('tuck_w'), 0) >= 0.99:
                run.append(r)
            else:
                if run:
                    ok = [x for x in run if f(x['tuck_wrist_shin_m']) <= 0.15 and f(x['tuck_knee_gap_m']) <= 0.25]
                    holds.append((c['prog'], f(run[0]['t']), len(run) / 60.0, len(ok) / 60.0, max(f(x['tuck_wrist_shin_m']) for x in run), max(f(x['tuck_knee_gap_m']) for x in run)))
                run = []
    for h in holds:
        P('   %-16s %.2f s: tucked %.2f s, tight %.2f s, wrist-shin max %.3f m, knees max %.3f m' % h)
    long_h = [h for h in holds if h[2] >= 0.25]
    kp = bool(long_h) and all(h[3] >= 0.25 for h in long_h)
    if holds:
        P('K  %s (%d tuck holds >= .25 s, all tight >= .25 s: %s; wrist-shin max %.3f m, knee gap max %.3f m)' % ('PASS' if kp else 'FAIL', len(long_h), kp, max(h[4] for h in holds), max(h[5] for h in holds)))
    # ---- L
    rows = [r for k, r in enumerate(T) if k % 6 == 0 and f(r.get('flip_t'), -1) >= 0]
    slow, n = [], 0
    for a, b in zip(rows, rows[1:]):
        if a.get('flip_prog') != b.get('flip_prog'): continue
        za = [float(x) for x in a['limb_z'].split()]; zb = [float(x) for x in b['limb_z'].split()]
        d = max(abs(x - y) for x, y in zip(za, zb)); n += 1
        if d < 0.10: slow.append((f(a['t']), d, a['flip_shape'], a['flip_prog']))
    P('L  slow limb samples: %d of %d -> %s' % (len(slow), n, 'PASS' if not slow else 'FAIL'))
    for s in slow: P('   slow t %.2f dmax %.3f %s / %s' % s)
    # ---- pose lines
    if pose and os.path.exists(pose):
        Pz = list(csv.DictReader(open(pose)))
        key = lambda x, y, z: (round(f(x), 2), round(f(y), 2), round(f(z), 2))
        PI = {}
        for r in Pz: PI.setdefault(key(r['x_m'], r['y_m'], r['z_m']), r)
        J = [PI.get(key(r['x_m'], r['y_m'], r['z_m'])) for r in T]
        P('pose rows joined: %d of %d telemetry rows (%d in tricks)' % (sum(1 for j in J if j), len(T), sum(1 for c in I for i, _ in c['rows'] if J[i])))
        def b(r, n): return [f(r[n + '_x']), f(r[n + '_y']), f(r[n + '_z'])]
        # G1 layout
        g1 = []
        for c in I:
            hips, knees = [], []
            for k, (i, ft) in enumerate(c['rows']):
                r, j = T[i], J[i]
                if not j or r.get('flip_shape') != 'Layout' or r.get('flip_shape_legs') != 'Layout': continue
                # inside a held layout: the same shape 0.1 s before and after on body and legs (no shape blend)
                if k < 6 or k + 6 >= len(c['rows']): continue
                rp, rn = T[c['rows'][k - 6][0]], T[c['rows'][k + 6][0]]
                if not all(x.get('flip_shape') == 'Layout' and x.get('flip_shape_legs') == 'Layout' for x in (rp, rn)): continue
                H, S2 = b(j, 'hips'), b(j, 'spine2')
                for sd in 'LR':
                    Th, Kn, Ft = b(j, 'thigh_' + sd), b(j, 'shin_' + sd), b(j, 'foot_' + sd)
                    hips.append(180 - ang(sub(S2, H), sub(Th, Kn)))   # trunk line vs thigh line (180 = straight)
                    knees.append(ang(sub(Th, Kn), sub(Ft, Kn)))     # hip joint - knee - ankle
            if hips:
                hs, ks = sorted(hips), sorted(knees)
                g1.append((c['prog'], c['t0'], len(hips) // 2, hs[len(hs) // 2], hs[0], ks[len(ks) // 2], ks[0]))
        for g in g1: P('   G1 %-16s %.2f s: %d held layout rows, hip median %.1f min %.1f deg, knee median %.1f min %.1f deg' % g)
        if g1:
            ok = all(g[3] >= 170 and g[5] >= 170 for g in g1)
            P('G1 %s layout hips / knees >= 170 deg (median per held layout; minimum hip %.1f, knee %.1f)' % ('PASS' if ok else 'FAIL', min(g[4] for g in g1), min(g[6] for g in g1)))
        else:
            P('G1 NO DATA (no held layout rows joined)')
        # G2 pointed toes
        tot = good = 0; worst = []
        for c in I:
            for i, ft in c['rows']:
                j = J[i]
                if not j: continue
                for sd in 'LR':
                    Kn, A_, To = b(j, 'shin_' + sd), b(j, 'foot_' + sd), b(j, 'toe_' + sd)
                    a = ang(sub(A_, Kn), sub(To, A_))
                    if a == a:
                        tot += 1; good += a <= 35; worst.append(a)
        if tot:
            worst.sort()
            P('G2 %s pointed toes: foot within 35 deg of the shin line in %.1f %% of %d trick foot samples (median %.1f, p95 %.1f deg)' % (
                'PASS' if good / tot >= 0.9 else 'FAIL', 100.0 * good / tot, tot, worst[len(worst) // 2], worst[int(len(worst) * 0.95)]))
        # G3 head spot + G4 open-out
        g3 = []; g4 = []
        for c in I:
            rows_c = [(T[i], J[i], ft) for i, ft in c['rows'] if J[i]]
            if len(rows_c) < 20: continue
            L = c['len']
            fl = []
            for r, j, ft in rows_c:
                hu = [f(j['head_ux']), f(j['head_uy']), f(j['head_uz'])]; cu = [f(j['chest_ux']), f(j['chest_uy']), f(j['chest_uz'])]
                fl.append((ft, ang(hu, cu)))
            late = [a for ft, a in fl if ft >= 0.55 * L]
            if late:
                g3.append((c['prog'], c['t0'], max(late) - min(late), max(a for _, a in fl) - min(a for _, a in fl)))
            last = [(r, ft) for r, j, ft in rows_c if ft >= L - 0.15]
            if last:
                op = all(r.get('flip_shape') in OPEN for r, _ in last)
                rt = max(abs(f(r['flip_rate_dps'])) for r, _ in last)
                g4.append((c['prog'], c['t0'], op, rt))
        for g in g3: P('   G3 %-16s %.2f s: head-vs-chest change in the open-out %.1f deg (whole trick %.1f deg)' % g)
        if g3:
            P('G3 %s head spot: %d of %d instances move the head >= 15 deg relative to the chest in the open-out' % ('PASS' if all(g[2] >= 15 for g in g3) else 'FAIL', sum(1 for g in g3 if g[2] >= 15), len(g3)))
        for g in g4: P('   G4 %-16s %.2f s: last 0.15 s open %s, rate max %.0f deg/s' % g)
        if g4:
            P('G4 %s open-out: %d of %d instances end in an open shape at <= 300 deg/s' % ('PASS' if all(g[2] and g[3] <= 300 for g in g4) else 'FAIL', sum(1 for g in g4 if g[2] and g[3] <= 300), len(g4)))
    return '\n'.join(out)


if __name__ == '__main__':
    print(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
