#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r24: owner-bug numbers r23 vs r24 (swings in x1 / x2 / m1 / s1, hero in frame and occlusion, perch occlusion, w2 zip -> perch).
import csv, os
TD = '/Users/midir/sm2-n1/traversal/docs/night1/traversal'
def L(r, c):
    p = f'{TD}/round-{r}/{c}_telemetry.csv'
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None
def swings(rows):
    out = []; cur = None
    for x in rows:
        if x['mode'] == 'swing':
            if cur is None: cur = [float(x['t']), float(x['t'])]
            else: cur[1] = float(x['t'])
        elif cur: out.append(cur); cur = None
    if cur: out.append(cur)
    return [(round(a, 2), round(b - a + 1 / 60, 2)) for a, b in out]
for r in ('23', '24'):
    print(f'== round {r}')
    for c in ('x1_rmb_cancel_flip', 'x2_rmb_cancel_wall', 'm1_mouse_swing', 's1_high_swing'):
        rows = L(r, c)
        if not rows: continue
        print(f'  {c}: swings (start, s) {swings(rows)} | hero in frame {sum(float(x["hero_in_frame"]) for x in rows) / len(rows):.2f} | hero_occl max {max(float(x["hero_occl"]) for x in rows):.3f}')
    for c in ('c_wallrun_perch', 'w1_wallrun_tall_zip', 'w2_wallrun_side_zip', 'r1_roofrun_zip'):
        rows = L(r, c)
        if not rows: continue
        p = [x for x in rows if x['mode'] == 'perch']; z = next((x for x in rows if x['sub'] == 'zipFire'), None)
        print(f'  {c}: zip {z["t"] if z else "-"} -> perch {p[0]["t"] if p else "none"} | perch rows {len(p)}, hero_occl max on the perch {max((float(x["hero_occl"]) for x in p), default=-1):.3f}')
