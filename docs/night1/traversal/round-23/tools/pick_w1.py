#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r23: w1 on the sunlit tower face (x -231.5..-227.5, y -62.5..-42.5, z >= 50) with a zip that perches; writes PICK_T1
import csv, os, sys
PD = sys.argv[1]
def fl(r, c):
    try: return float(r[c])
    except (KeyError, TypeError, ValueError): return float('nan')
def on(r): return r['mode'] == 'wall' and -231.5 <= fl(r, 'x_m') <= -227.5 and -62.5 <= fl(r, 'y_m') <= -42.5 and fl(r, 'z_m') >= 50
best = None
for n in sys.argv[2:]:
    p = os.path.join(PD, n, n + '_telemetry.csv')
    if not os.path.exists(p): print(n, 'no telemetry'); continue
    rows = list(csv.DictReader(open(p)))
    wr = [r for r in rows if on(r)]
    zf = next((fl(r, 't') for r in rows if r['sub'] == 'zipFire'), -1)
    pr = next((fl(r, 't') for r in rows if r['mode'] == 'perch' and fl(r, 't') > zf > 0), -1)
    print(f'{n}: lit wall rows {len(wr)} z {min([fl(r, "z_m") for r in wr] or [0]):.1f}-{max([fl(r, "z_m") for r in wr] or [0]):.1f}; zip {zf:.2f} -> perch {pr:.2f}')
    if len(wr) >= 60 and pr > 0 and pr - zf <= 2.0 and (best is None or len(wr) > best[0]): best = (len(wr), n)
if best: open(os.path.join(PD, 'PICK_T1'), 'w').write(best[1] + '\n'); print('PICK_T1', best[1])
