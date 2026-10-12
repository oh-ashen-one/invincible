#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 17: TC8 / critic r16 single-gap test per flip program, on the telemetry (rendered or probe):
#   * apex: the hips (z_m = body centre) at the program's highest row must be >= 3 m over the LOWER roofline within 30 m
#     (roofline per street side = the highest roof >= 16 m over the street inside the 30 m half-disc on that side of the travel
#     direction, from the engine heightmap city/heightmap_5m.csv.gz (5 m grid of the traversal world's tops, -WHTravHeightmap);
#     cells under 16 m are street trees / awnings; a side with nothing taller counts as 16 m; the lower side wins);
#   * share of program rows with the hips >= roofline + 3;
#   * flipcam_k at flip_t 0.35 (critic r16: >= 0.9);
#   * view_sun_deg min over the trick window (program + 0.5 s; >= 100);
#   * camera side / tier chosen at the release.
# usage: roof_check.py <telemetry.csv> <label> [--hm <heightmap.csv[.gz]>]
import csv, sys, os, gzip, math
args = sys.argv[1:]
HM = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'city', 'heightmap_5m.csv.gz')
if '--hm' in args:
    i = args.index('--hm'); HM = args[i + 1]; del args[i:i + 2]
path, label = args[0], (args[1] if len(args) > 1 else os.path.basename(args[0]))
op = gzip.open if HM.endswith('.gz') else open
H = {}
with op(HM, 'rt') as fh:
    for r in csv.DictReader(fh):
        H[(int(round(float(r['x']))), int(round(float(r['y']))))] = float(r['z'])
def hm(x, y): return H.get((int(round(x / 5.0)) * 5, int(round(y / 5.0)) * 5), 0.0)
def lower_roof(x, y, vx, vy, R=30.0, minh=16.0):
    n = math.hypot(vx, vy)
    if n < 1e-3: return None, None, None
    fx, fy = vx / n, vy / n; rx, ry = -fy, fx
    street = 0.0
    top = [None, None]
    for dx in range(-30, 31, 5):
        for dy in range(-30, 31, 5):
            if dx * dx + dy * dy > R * R: continue
            lat = dx * rx + dy * ry
            if abs(lat) < 2.0: continue
            z = hm(x + dx, y + dy)
            if z - street < minh: continue
            s = 0 if lat < 0 else 1
            top[s] = z if top[s] is None else max(top[s], z)
    top = [minh if t is None else t for t in top]  # a side with nothing >= 16 m is low (= 16 m), as FlowRoofTarget
    return min(top), top[0], top[1]
T = list(csv.DictReader(open(path)))
def f(r, k, d=float('nan')):
    try: return float(r[k])
    except (KeyError, ValueError, TypeError): return d
progs = []; cur = None
for k, r in enumerate(T):
    p = r.get('flip_prog', '')
    ft = f(r, 'flip_t', -1)
    if p and ft >= 0:
        if cur is None or cur['name'] != p or ft < f(T[cur['rows'][-1]], 'flip_t', 0): cur = {'name': p, 'rows': []}; progs.append(cur)
        cur['rows'].append(k)
    else: cur = None
print('# %s: %d flip programs (roof_check.py, TC8 + critic r16 test)' % (label, len(progs)))
allpass = True; shares = []
for i, P in enumerate(progs):
    rows = P['rows']; r0 = T[rows[0]]
    ka = max(rows, key=lambda k: f(T[k], 'z_m'))
    ra = T[ka]
    roof, tl, tr = lower_roof(f(ra, 'x_m'), f(ra, 'y_m'), f(r0, 'vx'), f(r0, 'vy'))
    apex = f(ra, 'z_m')
    t0 = f(r0, 't'); t1 = f(T[rows[-1]], 't')
    win = [k for k in range(rows[0], len(T)) if f(T[k], 't') <= t1 + 0.5]
    vs = [f(T[k], 'view_sun_deg') for k in win if f(T[k], 'view_sun_deg', -1) >= 0]
    k35 = next((k for k in rows if f(T[k], 'flip_t') >= 0.35), rows[-1])
    above = [k for k in rows if roof is not None and f(T[k], 'z_m') >= roof + 3.0]
    share = len(above) / len(rows) if roof is not None else float('nan')
    margin = apex - roof if roof is not None else float('nan')
    ok_apex = roof is None or margin >= 3.0
    ok_k = f(T[k35], 'flipcam_k') >= 0.9
    ok_sun = (min(vs) >= 100.0) if vs else False
    allpass &= ok_apex and ok_k and ok_sun
    if roof is not None: shares.append(share)
    print('  %d %-14s t %.2f-%.2f  hips start %.1f apex %.1f (t %.2f) catch %.1f | lower roofline %s (sides %s / %s) -> apex margin %s %s, rows >= roof+3 %s'
          % (i + 1, P['name'], t0, t1, f(r0, 'z_m'), apex, f(ra, 't'), f(T[rows[-1]], 'z_m'),
             '%.1f' % roof if roof is not None else 'none', '%.0f' % tl if tl is not None else '-', '%.0f' % tr if tr is not None else '-',
             '%+.1f m' % margin if roof is not None else 'n/a', 'PASS' if ok_apex else 'FAIL', '%.0f %%' % (100 * share) if roof is not None else 'n/a'))
    print('      flipcam_k at flip_t .35 = %.2f %s | view_sun min %.0f p50 %.0f %s | side %+.0f deg tier %s | solver roof %.1f apex want %.1f'
          % (f(T[k35], 'flipcam_k'), 'PASS' if ok_k else 'FAIL', min(vs) if vs else -1, sorted(vs)[len(vs) // 2] if vs else -1, 'PASS' if ok_sun else 'FAIL',
             f(T[min(rows[-1], rows[0] + 30)], 'flipcam_yaw_deg'), T[min(rows[-1], rows[0] + 30)].get('flipcam_tier', '?'),
             f(r0, 'flow_roof_m', -1), f(r0, 'flow_apex_want_z', 0)))
print('  => %s (%d programs; mean share of rows >= roofline + 3: %s)' % ('ALL PASS' if allpass and progs else 'FAIL', len(progs),
      '%.0f %%' % (100 * sum(shares) / len(shares)) if shares else 'n/a'))
