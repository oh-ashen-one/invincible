#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 24 checks (critic r23 biggest gap, SPEC T7 / T3 / T1 / T2 / T4 on a_swing_chain) + the r24 camera hard gate (c 7.7-8.5 s).
#   T7  from the first release, EVERY 4 s window [t, t+4] holds a release whose air phase tops out >= 30 m over the floor (height_above_floor;
#       the release-instant height is listed too) and whose next swing bottoms out 3-13 m over the floor, drop (apex - low) >= 20 m, near the
#       street centre (lateral offset of the low point from the mid line of the open street span, heightmap), hero_occl 0 from the release to
#       the low point (rendered runs only)
#   T3  web_on 25-45 % of the clip;  T1 rope held 0.5-1.6 s per swing;  T2 2-4 attaches in every 8 s window
#   T4  every web-less phase > 0.6 s: a dive or a trick, pose_sig changes at every 0.1 s sample (rhythm_check.py prints it too)
#   CAM c 7.7-8.5 s: hero_in_frame 1, hero_occl <= .02, cam_hero_dist >= 3 m, no yaw reversal against the user's turn
# usage: r24_checks.py <dir> [--clip a_swing_chain] [--rendered]
import csv, gzip, math, os, sys
D = sys.argv[1]
A = sys.argv[2:]
CLIP = A[A.index('--clip') + 1] if '--clip' in A else 'a_swing_chain'
REND = '--rendered' in A
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)
def fl(r, k, d=float('nan')):
    try: return float(r.get(k, ''))
    except (TypeError, ValueError): return d
def find(name):
    for p in (os.path.join(D, name + '_telemetry.csv'), os.path.join(D, name, name + '_telemetry.csv')):
        if os.path.exists(p): return p
    return None
HM = {}
for r in csv.DictReader(gzip.open(os.path.join(HERE, 'city/heightmap_5m.csv.gz'), 'rt')):
    HM[(int(r['x']), int(r['y']))] = (float(r['z']), r['ground'])
def hm(x, y):
    k = (int(round(x / 5.0)) * 5, int(round(y / 5.0)) * 5)
    return HM.get(k, (None, None))
def street_offset(x, y, vx, vy):
    """lateral offset (m) of (x, y) from the centre of the open street span across the travel direction, and the span width"""
    n = math.hypot(vx, vy)
    if n < 1e-3: return None, None
    lx, ly = -vy / n, vx / n
    z0, _ = hm(x, y)
    if z0 is None: return None, None
    def edge(sgn):
        for d in range(1, 80):
            z, _ = hm(x + lx * d * sgn, y + ly * d * sgn)
            if z is None or z > z0 + 4.0: return d
        return 80
    a, b = edge(1), edge(-1)
    return (a - b) / 2.0, a + b
def t7(rows, label):
    hf = lambda r: fl(r, 'height_above_floor_m') if fl(r, 'height_above_floor_m') < 900 else 0.0
    ev, i, n = [], 1, len(rows)
    while i < n:
        if rows[i - 1]['mode'] == 'swing' and rows[i]['mode'] == 'air':
            t_rel, h_rel = fl(rows[i], 't'), hf(rows[i])
            j = i; apex = h_rel; occ = 0.0; sub = rows[i]['sub']; tr = rows[i]['trick']
            while j < n and rows[j]['mode'] == 'air':
                apex = max(apex, hf(rows[j])); occ = max(occ, fl(rows[j], 'hero_occl', 0.0)); j += 1
            if j >= n or rows[j]['mode'] != 'swing': ev.append(dict(t=t_rel, rel=h_rel, apex=apex, low=None, sub=sub, trick=tr, end=rows[min(j, n-1)]['mode'])); i = j; continue
            k = j; low = 1e9; lr = None
            while k < n and rows[k]['mode'] == 'swing':
                h = hf(rows[k]); occ = max(occ, fl(rows[k], 'hero_occl', 0.0) if (lr is None or h < low) else 0.0)
                if h < low: low, lr = h, rows[k]
                k += 1
            complete = k < n or fl(lr, 't') < fl(rows[-1], 't') - 0.05   # the low point is known once he rises out of it
            off, wid = street_offset(fl(lr, 'x_m'), fl(lr, 'y_m'), fl(lr, 'vx'), fl(lr, 'vy'))
            ev.append(dict(t=t_rel, rel=h_rel, apex=apex, low=low, tlow=fl(lr, 't'), drop=apex - low, occ=occ, off=off, wid=wid, sub=sub, trick=tr,
                           complete=complete, hs=fl(rows[i], 'hspeed_mps'), vz=fl(rows[i], 'vz'), want=fl(rows[i], 'alt_apex_want_m', -1)))
            i = j; continue
        i += 1
    P(f"  {label}: releases {len(ev)}")
    P(f"   {'t_rel':>6} {'h_rel':>5} {'apex':>5} {'want':>5} {'vz':>5} {'hs':>5} {'low':>5} {'t_low':>6} {'drop':>5} {'off':>5} {'span':>4} {'occl':>5}  kind / verdict")
    good = []
    for e in ev:
        if e['low'] is None:
            P(f"   {e['t']:6.2f} {e['rel']:5.1f} {e['apex']:5.1f}   (no next swing: ends in {e['end']})"); continue
        offok = e['off'] is not None and (abs(e['off']) <= max(4.0, e['wid'] / 6.0))
        ok = e['apex'] >= 30 and 3 <= e['low'] <= 13 and e['drop'] >= 20 and (not REND or e['occ'] <= 0.0) and e['complete']
        if ok: good.append(e)
        why = []
        if e['apex'] < 30: why.append('apex<30')
        if not 3 <= e['low'] <= 13: why.append('low out')
        if e['drop'] < 20: why.append('drop<20')
        if REND and e['occ'] > 0: why.append('OCCL')
        if not e['complete']: why.append('swing runs past the clip end')
        P(f"   {e['t']:6.2f} {e['rel']:5.1f} {e['apex']:5.1f} {e['want']:5.1f} {e['vz']:5.1f} {e['hs']:5.1f} {e['low']:5.1f} {e['tlow']:6.2f} {e['drop']:5.1f} "
          f"{(e['off'] if e['off'] is not None else float('nan')):5.1f} {(e['wid'] or 0):4d} {e['occ']:5.3f}  {(e['trick'] or e['sub'])[:12]:12s} "
          f"{'OK' if ok else 'no: ' + ','.join(why)}{'' if offok else ' (low off-centre)'}")
    t_end = fl(rows[-1], 't')
    if not ev: P('  T7 FAIL (no release)'); return False
    t0 = ev[0]['t']; bad = []; t = t0; nw = 0
    while t + 4.0 <= t_end + 1e-6:
        nw += 1
        if not any(t - 1e-6 <= e['t'] <= t + 4.0 + 1e-6 for e in good): bad.append(round(t, 1))
        t += 0.1
    P(f"  T7 4 s windows from the first release {t0:.2f} s to {t_end:.2f} s: {nw - len(bad)}/{nw} hold a qualifying release" + (f"; failing window starts {bad[0]}..{bad[-1]} ({len(bad)})" if bad else '') + f" -> {'PASS' if not bad and nw else 'FAIL'}")
    offs = [abs(e['off']) for e in good if e['off'] is not None]
    if offs: P(f"  low points of the qualifying drops: lateral offset from the street centre {min(offs):.1f}-{max(offs):.1f} m (span {min(e['wid'] for e in good)}-{max(e['wid'] for e in good)} m)")
    return not bad and nw > 0
def rhythm(rows, label):
    t = [fl(r, 't') for r in rows]; web = [fl(r, 'web_on', 0) for r in rows]
    dur = t[-1] - t[0]
    share = sum(1 for w in web if w > 0.5) / len(rows)
    first = next((x for x, r in zip(t, rows) if r['mode'] == 'swing'), t[0])
    share2 = sum(1 for x, w in zip(t, web) if w > 0.5 and x >= first) / max(1, sum(1 for x in t if x >= first))
    P(f"  T3 web_on {share*100:.1f} % of the clip, {share2*100:.1f} % from the first attach ({first:.2f} s) (25-45) -> {'PASS' if 0.25 <= share <= 0.45 else 'FAIL'}")
    sw = []; cur = None
    for x, r in zip(t, rows):
        if r['mode'] == 'swing' and cur is None: cur = [x, x]
        elif r['mode'] == 'swing': cur[1] = x
        elif cur is not None: sw.append(cur); cur = None
    if cur is not None: sw.append(cur)   # a swing still running at the clip end counts as an attach (not as a full hold)
    full = [s for s in sw if s[1] < t[-1] - 0.02]
    held = [round(s[1] - s[0] + 1/60, 2) for s in full]
    P(f"  T1 rope held per swing (s): {held} (0.5-1.6) -> {'PASS' if held and all(0.5 <= h <= 1.6 for h in held) else 'FAIL'}")
    at = [s[0] for s in sw]; badw = []; nw = 0; x = t[0]
    while x + 8.0 <= t[-1] + 1e-6:
        c = sum(1 for a in at if x <= a < x + 8.0); nw += 1
        if not 2 <= c <= 4: badw.append((round(x, 1), c))
        x += 0.5
    P(f"  T2 attaches per 8 s window: {[sum(1 for a in at if x0 <= a < x0 + 8) for x0 in [t[0] + 0.5 * k for k in range(nw)]]} (2-4) -> {'PASS' if not badw else 'FAIL ' + str(badw[:4])}")
    # T4: web-less phases > 0.6 s: dive or trick, pose_sig differs at every 0.1 s sample (pose columns lag one row)
    gaps = []; cur = None
    for k, r in enumerate(rows):
        off = r['mode'] in ('air',) and fl(r, 'web_on', 0) < 0.5
        if off and cur is None: cur = [k, k]
        elif off: cur[1] = k
        elif cur is not None: gaps.append(cur); cur = None
    allok = True
    for a, b in gaps:
        d = t[b] - t[a]
        if d <= 0.6: continue
        samp = [rows[min(k + 1, len(rows) - 1)]['pose_sig'] for k in range(a, b + 1, 6)]
        ch = sum(1 for u, v in zip(samp, samp[1:]) if u != v); nn = max(1, len(samp) - 1)
        kinds = sorted(set(('trick' if rows[k]['trick'] else 'dive' if rows[k]['air_flavor'] in ('dive',) or rows[k]['sub'] == 'dive' else rows[k]['sub']) for k in range(a, b + 1)))
        ok = ch == nn
        allok &= ok
        P(f"  T4 web-less {t[a]:.2f}-{t[b]:.2f} {d:.2f} s: pose changes {ch}/{nn} at 0.1 s  subs {kinds} -> {'ok' if ok else 'HELD POSE'}")
    P(f"  T4 -> {'PASS' if allok else 'FAIL'}")
def cam_gate(rows, label, t0=7.7, t1=8.5):
    w = [r for r in rows if t0 - 1e-6 <= fl(r, 't') <= t1 + 1e-6]
    if not w: P(f"  {label}: no rows in {t0}-{t1}"); return False
    inf = sum(1 for r in w if fl(r, 'hero_in_frame') >= 1); occ = max(fl(r, 'hero_occl', 0) for r in w)
    dmin = min(fl(r, 'cam_hero_dist_m') for r in w)
    yaws = [fl(r, 'cam_yaw_deg') for r in w]
    un = [yaws[0]]
    for y in yaws[1:]: un.append(un[-1] + ((y - un[-1] + 180) % 360 - 180))
    # the user turn sign (look input) over the window: cam_look_dir column (r24), else the net yaw change
    dirs = [fl(r, 'cam_look_dir', 0) for r in w]
    sg = -1 if sum(dirs) < 0 else 1 if sum(dirs) > 0 else (-1 if un[-1] < un[0] else 1)
    back = 0.0; best = un[0]
    for y in un:
        best = min(best, y) if sg < 0 else max(best, y)
        back = max(back, (y - best) if sg < 0 else (best - y))   # yaw moved back against the turn
    crane = max(fl(r, 'cam_gnd_crane_m', 0) for r in w)
    ok = inf == len(w) and occ <= 0.02 and dmin >= 3.0 and back <= 2.0
    P(f"  {label} {t0}-{t1} s ({len(w)} rows): hero_in_frame {inf}/{len(w)}, hero_occl max {occ:.3f}, cam-hero min {dmin:.2f} m, "
      f"yaw {un[0]:.1f} -> {un[-1]:.1f} (turn {'-' if sg < 0 else '+'}), max backtrack {back:.1f} deg, crane max {crane:.2f} m -> {'PASS' if ok else 'FAIL'}"
      f" [geometry part (frame, distance, reversal): {'GEOM_OK' if inf == len(w) and dmin >= 3.0 and back <= 2.0 else 'GEOM_FAIL'}]")
    return ok
P(f"== r24 checks on {D}")
p = find(CLIP)
if p:
    rows = list(csv.DictReader(open(p)))
    P(f"== T7 / T3 / T1 / T2 / T4 on {CLIP} ({len(rows)} rows, {fl(rows[-1], 't'):.2f} s)")
    t7(rows, CLIP); rhythm(rows, CLIP)
pc = find('c_wallrun_perch')
if pc:
    rows = list(csv.DictReader(open(pc)))
    P("== CAM hard gate (critic r23 secondary 1)")
    cam_gate(rows, 'c_wallrun_perch')
    zr = next((r for r in rows if r['sub'] == 'zipFire'), None); pr = next((r for r in rows if r['mode'] == 'perch'), None)
    P(f"  c zip {zr['t'] if zr else '-'} -> perch {pr['t'] if pr else 'none'} (last {rows[-1]['mode']}/{rows[-1]['sub']})")
open(os.path.join(D, 'R24_CHECK.txt') if os.path.isdir(D) else 'R24_CHECK.txt', 'w').write('\n'.join(OUT) + '\n')
