#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r22: pick the w2 route variant whose side run covers 3.1-3.9 s ON the sunlit west face of the 96 m tower
# (x ~267.5, y -620..-570; sun yaw -178 elev 8: the park west of it keeps the face lit from ~15 m up).
# usage: pick_route.py <probe dir> <name> ...   -> prints a table, writes <probe dir>/PICK (best name)
import csv, os, sys
PD = sys.argv[1]
def fl(r, k):
    try: return float(r[k])
    except (KeyError, TypeError, ValueError): return float('nan')
best = None
for n in sys.argv[2:]:
    p = os.path.join(PD, n, n + '_telemetry.csv')
    if not os.path.exists(p): print(n, 'no telemetry'); continue
    rows = list(csv.DictReader(open(p)))
    wall = [r for r in rows if r['mode'] == 'wall']
    if not wall: print(n, 'never on a wall'); continue
    t0 = fl(wall[0], 't'); x0 = fl(wall[0], 'x_m'); y0 = fl(wall[0], 'y_m'); z0 = fl(wall[0], 'z_m')
    side = [r for r in rows if r['sub'] == 'wallRunSide']
    ts = fl(side[0], 't') if side else float('nan'); te = fl(side[-1], 't') if side else float('nan')
    def ok(r): return r['sub'] == 'wallRunSide' and 265.0 <= fl(r, 'x_m') <= 271.0 and -619.0 <= fl(r, 'y_m') <= -571.0 and fl(r, 'z_m') >= 21.0  # above the street-tree canopy / its shadow (~15 m)
    ts12 = [3.1 + k / 12 for k in range(10)]
    cov = 0
    for t in ts12:
        r = min(rows, key=lambda q: abs(fl(q, 't') - t))
        cov += ok(r)
    perch = any(r['mode'] == 'perch' and fl(r, 't') > 3.9 for r in rows)
    zs = [fl(r, 'z_m') for r in side] or [float('nan')]
    score = cov + (0.5 if perch else 0) + (0.3 if not n.startswith('w2s_direct') else 0) - (0.001 * ts if ts == ts else 0)  # prefer the swing entry
    print(f'{n}: wall at {t0:.2f}s ({x0:.1f},{y0:.1f},{z0:.1f}); side {ts:.2f}-{te:.2f}s z {min(zs):.1f}-{max(zs):.1f}; '
          f'12fps 3.1-3.85 on the lit face {cov}/10; perch {perch}; score {score:.3f}')
    if best is None or score > best[0]: best = (score, n)
if best:
    open(os.path.join(PD, 'PICK'), 'w').write(best[1] + '\n')
    print('PICK', best[1])
