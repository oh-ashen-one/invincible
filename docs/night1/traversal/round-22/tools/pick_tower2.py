#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r22: pick the tower route (west face of the 284 m tower at x ~-228, y -62..-43, lit above ~48 m: the only long west face
# whose sun line clears the hinterland at the 8 deg golden-hour sun; the fin at y -40 is the end of the run).
# usage: pick_tower.py <probe dir> <w2 names...> -- <w1 names...>  -> PICK_T2 / PICK_T1
import csv, os, sys
PD = sys.argv[1]; a = sys.argv[2:]; k = a.index('--'); W2, W1 = a[:k], a[k + 1:]
def fl(r, c):
    try: return float(r[c])
    except (KeyError, TypeError, ValueError): return float('nan')
def load(n):
    p = os.path.join(PD, n, n + '_telemetry.csv')
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None
def on(r): return r['mode'] == 'wall' and -231.5 <= fl(r, "x_m") <= -227.5 and -62.5 <= fl(r, 'y_m') <= -42.5 and fl(r, 'z_m') >= 50
best = None
for n in W2:
    rows = load(n)
    if not rows: print(n, 'no telemetry'); continue
    wall = [r for r in rows if r['mode'] == 'wall']
    side = [r for r in rows if r['sub'] == 'wallRunSide']
    cov = 0
    for k2 in range(10):
        t = 3.1 + k2 / 12; r = min(rows, key=lambda q: abs(fl(q, 't') - t))
        cov += (r['sub'] == 'wallRunSide' and on(r))
    perch = any(r['mode'] == 'perch' for r in rows)
    print(f'{n}: wall {fl(wall[0], "t") if wall else -1:.2f}s ({fl(wall[0], "x_m") if wall else 0:.1f},{fl(wall[0], "y_m") if wall else 0:.1f},{fl(wall[0], "z_m") if wall else 0:.1f})'
          f'; side {fl(side[0], "t") if side else -1:.2f}-{fl(side[-1], "t") if side else -1:.2f}s z {min([fl(r, "z_m") for r in side] or [0]):.1f}-{max([fl(r, "z_m") for r in side] or [0]):.1f}'
          f' y {min([fl(r, "y_m") for r in side] or [0]):.1f}..{max([fl(r, "y_m") for r in side] or [0]):.1f}; 12 fps on the lit face {cov}/10; perch {perch}')
    if cov >= 7 and (best is None or cov > best[0]): best = (cov, n)
if best: open(os.path.join(PD, 'PICK_T2'), 'w').write(best[1] + '\n'); print('PICK_T2', best[1])
b1 = None
for n in W1:
    rows = load(n)
    if not rows: continue
    wr = [r for r in rows if r['mode'] == 'wall' and on(r)]
    zp = next((fl(r, 't') for r in rows if r['mode'] == 'zip'), -1)
    print(f'{n}: lit wall rows {len(wr)}; z {min([fl(r, "z_m") for r in wr] or [0]):.1f}-{max([fl(r, "z_m") for r in wr] or [0]):.1f}; zip at {zp:.2f}; perch {any(r["mode"] == "perch" for r in rows)}')
    if wr and (b1 is None or len(wr) > b1[0]): b1 = (len(wr), n)
if b1: open(os.path.join(PD, 'PICK_T1'), 'w').write(b1[1] + '\n'); print('PICK_T1', b1[1])
