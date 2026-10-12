#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island r04: the fire-escape test of the round-03 critic on the r3 crosstown-east telemetry (from t = 2.4 s):
  * stuck: no 1 s window (from t0 on) in which the hero moves < 3 m (3D distance between the window's first and last frame
    AND path length; both are reported, the pass line uses the net displacement)
  * topOut loops: wall top-outs (telemetry `topouts` counter increments) after t0 that start within 4 m (horizontal) of an earlier top-out
    after t0 = a repeated top-out at the same spot; pass <= 1
  * clear: the hero is east of x = -235.5 m (x_m > -235.5) at t = 3.5 s and stays out of the 4 m disc around the r03 loop spot afterwards
usage: island_fe_check.py <telemetry.csv> [out.json] [--t0 2.4]"""
import csv, json, math, sys


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    t0 = 2.4
    if '--t0' in sys.argv: t0 = float(sys.argv[sys.argv.index('--t0') + 1])
    rows = list(csv.DictReader(open(a[0])))
    T = [float(r['t']) for r in rows]; P = [(float(r['x_m']), float(r['y_m']), float(r['z_m'])) for r in rows]
    tops = [int(float(r.get('topouts') or 0)) for r in rows]
    tend = T[-1]
    # stuck windows
    worst = (1e9, None); n_stuck = 0; stuck_ts = []
    j = 0
    for i in range(len(rows)):
        if T[i] < t0 or T[i] + 1.0 > tend: continue
        while j < len(rows) and T[j] < T[i] + 1.0: j += 1
        if j >= len(rows): break
        d = math.dist(P[i], P[j])
        if d < worst[0]: worst = (d, T[i])
        if d < 3.0:
            n_stuck += 1
            if not stuck_ts or T[i] - stuck_ts[-1][1] > 1 / 30: stuck_ts.append([T[i], T[i]])
            else: stuck_ts[-1][1] = T[i]
    # top-outs after t0
    evs = []
    for i in range(1, len(rows)):
        if tops[i] > tops[i - 1] and T[i] >= t0: evs.append((T[i], P[i]))
    loops = 0
    for k, (t, p) in enumerate(evs):
        if any(math.hypot(p[0] - q[0], p[1] - q[1]) < 4.0 for (_, q) in evs[:k]): loops += 1
    LOOP = (-235.5, 616.4)
    i35 = min(range(len(rows)), key=lambda i: abs(T[i] - 3.5))
    back = [T[i] for i in range(len(rows)) if T[i] > 3.5 and math.hypot(P[i][0] - LOOP[0], P[i][1] - LOOP[1]) < 4.0]
    out = {'csv': a[0], 't0': t0, 'frames': len(rows), 't_end': tend,
           'stuck_1s_windows_under_3m': n_stuck, 'stuck_spans_t': [[round(x, 3), round(y + 1.0, 3)] for x, y in stuck_ts],
           'min_1s_displacement_m': round(worst[0], 3), 'min_at_t': worst[1],
           'topouts_after_t0': len(evs), 'topout_events': [[round(t, 3)] + [round(v, 2) for v in p] for t, p in evs],
           'topout_loops_same_spot': loops,
           'x_at_3p5': round(P[i35][0], 3), 'pos_at_3p5': [round(v, 2) for v in P[i35]],
           'within_4m_of_r03_loop_after_3p5_s': len(back),
           'pass': {'never_stuck': n_stuck == 0, 'topout_loops_le_1': loops <= 1, 'past_x_by_3p5': P[i35][0] > -235.5 and not back}}
    out['pass']['all'] = all(out['pass'].values())
    s = json.dumps(out, indent=1)
    if len(a) > 1: open(a[1], 'w').write(s)
    print(s)


if __name__ == '__main__':
    main()
