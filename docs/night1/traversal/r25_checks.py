#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 25 telemetry gates (render-independent parts; the rope luminance test is rope_r25_check.py, the run cadence video FFT cadence_r25.py):
#   G1  owner bug 5 (critic r24 secondary 1): c 8.6-10.5 s -- hero_in_frame = 1 on every row, cam-hero 3.4-7 m, camera pitch change <= 15 deg
#       inside every 0.3 s window (max - min of the pitch over the window), occl 0 where rendered (hero_occl >= 0)
#   G1b the r24 ground-orbit gate, c 7.7-8.5 s: hero_in_frame 49/49, occl 0 (rendered), cam-hero >= 3 m, yaw backtrack 0 deg
#   P1  pawn run: speed / sub over 1.5-11 s (the cadence itself is measured on the video)
# usage: r25_checks.py <dir with *_telemetry.csv> [more dirs ...]
import csv, os, sys


def load(p):
    return list(csv.DictReader(open(p)))


def f(r, k, d=-1.0):
    try:
        return float(r[k])
    except (KeyError, ValueError):
        return d


def gate_c(rows, label):
    W = [r for r in rows if 8.6 - 1e-6 <= f(r, 't') <= 10.5 + 1e-6]
    if not W:
        print(f'  {label}: no rows in 8.6-10.5 s'); return False
    out = [r['t'] for r in W if f(r, 'hero_in_frame') < 1]
    dist = [f(r, 'cam_hero_dist_m') for r in W]
    occ = [f(r, 'hero_occl') for r in W if f(r, 'hero_occl') >= 0]
    T = [f(r, 't') for r in W]; Pt = [f(r, 'cam_pitch_deg') for r in W]
    worst = 0.0; wt = None
    for i in range(len(T)):
        j = i; lo = hi = Pt[i]
        while j < len(T) and T[j] - T[i] <= 0.3 + 1e-6:
            lo = min(lo, Pt[j]); hi = max(hi, Pt[j]); j += 1
        if hi - lo > worst: worst, wt = hi - lo, T[i]
    held = sum(1 for r in W if f(r, 'cam_perch_hold', 0) > 0)
    ok_f = not out; ok_d = 3.4 <= min(dist) and max(dist) <= 7.0; ok_p = worst <= 15.0; ok_o = (max(occ) if occ else 0.0) <= 0.0
    print(f'  {label} G1 8.6-10.5 s ({len(W)} rows): hero_in_frame {len(W) - len(out)}/{len(W)}' + (f' (out {out[0]}..{out[-1]})' if out else '') +
          f', cam-hero {min(dist):.2f}-{max(dist):.2f} m (3.4-7), max pitch change in 0.3 s {worst:.1f} deg at {wt:.2f} s (<= 15), '
          f'occl max {max(occ) if occ else -1:.3f} ({"rendered" if occ else "not rendered"}), perch yaw hold rows {held}'
          f' -> {"PASS" if ok_f and ok_d and ok_p and ok_o else "FAIL"}')
    return ok_f and ok_d and ok_p and ok_o


def gate_c_r24(rows, label):
    W = [r for r in rows if 7.7 - 1e-6 <= f(r, 't') <= 8.5 + 1e-6]
    inf = sum(1 for r in W if f(r, 'hero_in_frame') >= 1)
    occ = [f(r, 'hero_occl') for r in W if f(r, 'hero_occl') >= 0]
    dmin = min(f(r, 'cam_hero_dist_m') for r in W)
    # yaw backtrack: the turn direction is the sign of the net yaw change from the turn start (6.9 s script look -> cam yaw); report the
    # largest move against the running extreme in the window
    Y = [f(r, 'cam_yaw_deg') for r in W]
    import math
    def wrap(a): return (a + 180.0) % 360.0 - 180.0
    net = wrap(Y[-1] - Y[0]); sgn = -1.0 if net < 0 else 1.0
    ext = Y[0]; back = 0.0
    for y in Y[1:]:
        d = wrap(y - ext) * sgn
        if d > 0: ext = y
        else: back = max(back, -d)
    ok = inf == len(W) and (max(occ) if occ else 0.0) <= 0.0 and dmin >= 3.0 and back <= 0.5
    print(f'  {label} G1b 7.7-8.5 s ({len(W)} rows): hero_in_frame {inf}/{len(W)}, occl max {max(occ) if occ else -1:.3f}, cam-hero min {dmin:.2f} m, '
          f'yaw {Y[0]:.1f} -> {Y[-1]:.1f}, max backtrack {back:.1f} deg -> {"PASS" if ok else "FAIL"}')
    return ok


def pawn(rows, label):
    W = [r for r in rows if 1.5 - 1e-6 <= f(r, 't') <= 11.0 + 1e-6]
    sp = [f(r, 'hspeed_mps') for r in W]
    subs = {}
    for r in W: subs[r['sub']] = subs.get(r['sub'], 0) + 1
    clips = {}
    for r in W: clips[r['anim_clip']] = clips.get(r['anim_clip'], 0) + 1
    y0, y1 = f(W[0], 'y_m'), f(W[-1], 'y_m')
    print(f'  {label} P1 1.5-11 s ({len(W)} rows): speed {min(sp):.2f}-{max(sp):.2f} m/s (median {sorted(sp)[len(sp) // 2]:.2f}), subs {subs}, '
          f'anim clips {clips}, y {y0:.1f} -> {y1:.1f}, in frame {sum(1 for r in W if f(r, "hero_in_frame") >= 1)}/{len(W)}')


for d in sys.argv[1:]:
    print(f'== {d}')
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        if os.path.isdir(p):
            q = [os.path.join(p, x) for x in os.listdir(p) if x.endswith('_telemetry.csv')]
            if not q: continue
            p = q[0]; n = os.path.basename(p)
        if not n.endswith('_telemetry.csv'): continue
        lab = n[:-len('_telemetry.csv')]
        rows = load(p)
        if lab.startswith('c_wallrun_perch'):
            gate_c(rows, lab); gate_c_r24(rows, lab)
        if lab.startswith('p1'):
            pawn(rows, lab)
