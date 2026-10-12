#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life: analyse the probe's foot log (Saved/Logs/life_feet.csv: per frame, per watched walker, root + ankle world positions, cm).
#   python3 tools/life/analyze_feet.py life_feet.csv [--json out.json]
# reports  (1) gait-phase spread (CH19): phase of each walker's left ankle in its own stride cycle at the start of the window (forward-most ankle = cycle start),
#          pairwise circular phase differences, the number of near-lockstep pairs
#          (2) stance sliding (CH17): ankle world displacement during a planted stance, and its speed, per walker (cross-check of the engine-side WH_LIFE_FOOT line)
import csv, collections, json, math, sys
rows = list(csv.DictReader(open(sys.argv[1])))
by = collections.defaultdict(list)
for r in rows: by[int(r['walker'])].append({k: float(v) for k, v in r.items()})
res = {'walkers': {}}
phases = []
for w, rs in sorted(by.items()):
    if len(rs) < 60: continue
    ox = [r['ox'] for r in rs]; oy = [r['oy'] for r in rs]
    hx, hy = ox[-1] - ox[0], oy[-1] - oy[0]; L = math.hypot(hx, hy)
    if L < 200: continue                                   # a walker that hardly moved (waiting) has no gait
    hx /= L; hy /= L
    f = [(r['lx'] - r['ox']) * hx + (r['ly'] - r['oy']) * hy for r in rs]
    t = [r['t'] for r in rs]
    # local maxima of the left ankle's forward coordinate = start of a stride cycle
    pk = [t[i] for i in range(2, len(f) - 2) if f[i] == max(f[i - 2:i + 3]) and f[i] > 15.0]
    if len(pk) < 3: continue
    period = (pk[-1] - pk[0]) / (len(pk) - 1)
    ph = ((t[0] - pk[0]) / period) % 1.0
    # stance: ankle within 12 cm of floor
    disp = []; inc = False
    for side in ('l', 'r'):
        z = [r[side + 'z'] - r['oz'] for r in rs]; x = [r[side + 'x'] for r in rs]; y = [r[side + 'y'] for r in rs]
        start = None
        for i in range(len(rs)):
            on = z[i] < 10.5
            if on and start is None: start = i
            if (not on or i == len(rs) - 1) and start is not None:
                if t[i - 1] - t[start] >= 0.12: disp.append(math.hypot(x[i - 1] - x[start], y[i - 1] - y[start]))
                start = None
    res['walkers'][w] = {'period_s': round(period, 3), 'phase0': round(ph, 3), 'root_speed_cm_s': round(L / (t[-1] - t[0]), 1),
                         'stance_disp_cm_median': round(sorted(disp)[len(disp) // 2], 1) if disp else None, 'stances': len(disp)}
    phases.append(ph)
n = len(phases)
diffs = [min(abs(a - b), 1 - abs(a - b)) for i, a in enumerate(phases) for b in phases[i + 1:]]
R = math.hypot(sum(math.cos(2 * math.pi * p) for p in phases), sum(math.sin(2 * math.pi * p) for p in phases)) / max(1, n)
res['gait'] = {'walkers': n, 'phases': sorted(round(p, 3) for p in phases), 'max_pairwise_diff_cycles': round(max(diffs), 3) if diffs else None,
               'mean_pairwise_diff_cycles': round(sum(diffs) / len(diffs), 3) if diffs else None, 'pairs_within_0.05_cycle': sum(d < 0.05 for d in diffs), 'pairs': len(diffs),
               'resultant_length_R (0 = evenly spread, 1 = lockstep)': round(R, 3)}
print(json.dumps(res['gait'], indent=1))
allst = [v['stance_disp_cm_median'] for v in res['walkers'].values() if v['stance_disp_cm_median'] is not None]
print('per-walker median stance ankle displacement (cm):', sorted(allst))
if '--json' in sys.argv: json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
