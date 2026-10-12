#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 15: critic r14 single-gap test ("the trick camera climbs to 20-27 deg up and looks into the sun, which flares out the
# flips") on a RENDERED capture:
#   U1 pcm_pitch never above 10 deg up (all frames)            U2 trick frames (flipcam_k >= 0.5): pitch <= 8 deg up
#   S1 trick frames: view >= 100 deg from the sun (view_sun_deg = rendered camera forward vs the direction to the sun)
#   L1 no frame with > 5 % of the hero-box pixels at luma >= 245 (video; hero box = telemetry px_*)
#   T11 median pitch 4-12 deg down (TRAVERSAL-SPEC T11 median; window = first web attach .. end, as spec_cam_check.py)
#   H1 trick frames: hero height over the lower street wall's roofline at the flow flip (flow_roof_m) -- apex >= 3 m over it
# Camera-manager / capture columns are read at the start of the next frame: shifted one row (as spec_cam_check.py).
# usage: suncam_check.py <telemetry.csv> <label> [--video <mp4>]
import csv, math, sys, os
args = sys.argv[1:]
video = None
if '--video' in args:
    k = args.index('--video'); video = args[k + 1]; del args[k:k + 2]
rows = list(csv.DictReader(open(args[0])))
lab = args[1]
for i in range(len(rows) - 1):
    for k in ('px_top', 'px_bottom', 'px_left', 'px_right', 'pcm_pitch', 'pcm_yaw', 'pcm_fov', 'pcm_roll', 'view_sun_deg'):
        if k in rows[i + 1]:
            rows[i][k] = rows[i + 1][k]
rows = rows[:-1]
def f(r, k, d=float('nan')):
    try: return float(r[k])
    except (KeyError, ValueError, TypeError): return d
def pct(v, p):
    v = sorted(v)
    if not v: return float('nan')
    k = (len(v) - 1) * p; a = math.floor(k); b = min(a + 1, len(v) - 1)
    return v[a] + (v[b] - v[a]) * (k - a)
res = []
def line(n, ok, txt):
    res.append(ok); print('  %-4s %s  %s' % (n, 'PASS' if ok else 'FAIL', txt))
print('%s: %d frames' % (lab, len(rows)))
P = [f(r, 'pcm_pitch') for r in rows]
imax = max(range(len(P)), key=lambda i: P[i])
line('U1', max(P) <= 10.0, 'pitch max %.1f deg up at %.2f s (<= 10)' % (max(P), f(rows[imax], 't')))
TR = [r for r in rows if f(r, 'flipcam_k', 0) >= 0.5]
if TR:
    tp = [f(r, 'pcm_pitch') for r in TR]
    line('U2', max(tp) <= 8.0, 'trick frames (%d): pitch p5 %.1f / p50 %.1f / max %.1f deg up (<= 8)' % (len(TR), pct(tp, .05), pct(tp, .5), max(tp)))
    sd = [f(r, 'view_sun_deg') for r in TR if f(r, 'view_sun_deg', -1) >= 0]
    if sd:
        bad = [r for r in TR if 0 <= f(r, 'view_sun_deg', -1) < 100]
        line('S1', not bad, 'trick frames: view-to-sun angle min %.0f / p50 %.0f deg (>= 100)%s' % (min(sd), pct(sd, .5),
             ', %d frames under 100 (%.2f-%.2f s)' % (len(bad), f(bad[0], 't'), f(bad[-1], 't')) if bad else ''))
    else:
        line('S1', False, 'no view_sun_deg (no sun found)')
    # H1: per flow flip, highest body height vs the roofline it was solved for
    progs = []
    cur = None
    for r in rows:
        fp = r.get('flip_prog', '')
        if fp and (cur is None or cur['p'] != fp or f(r, 'flip_t') < cur['lt'] - 0.05):
            cur = {'p': fp, 't0': f(r, 't'), 'roof': f(r, 'flow_roof_m', -1), 'rise': f(r, 'flow_rise_m', 0), 'hmax': -1e9, 'lt': 0}
            progs.append(cur)
        if fp and cur:
            cur['lt'] = f(r, 'flip_t'); cur['hmax'] = max(cur['hmax'], f(r, 'z_m') - 0.9)  # feet over the street (body centre 0.9 m over the feet; street z ~0)
        if not fp: cur = None
    for p in progs:
        if p['roof'] >= 0:
            print('       flip %-14s at %.2f s: lower roofline %.1f m, rise %.1f m, feet apex %.1f m -> %+.1f m over the roofline'
                  % (p['p'], p['t0'], p['roof'], p['rise'], p['hmax'], p['hmax'] - p['roof']))
        else:
            print('       flip %-14s at %.2f s: no roofline sample (rise %.1f m), feet apex %.1f m' % (p['p'], p['t0'], p['rise'], p['hmax']))
t0 = next((f(r, 't') for r in rows if r['mode'] == 'swing'), 0.0)
pd = [-f(r, 'pcm_pitch') for r in rows if f(r, 't') >= t0]
line('T11', 4 <= pct(pd, .5) <= 12, 'pitch down from the first attach: p5 %+.1f p50 %+.1f p95 %+.1f deg (median 4-12)' % (pct(pd, .05), pct(pd, .5), pct(pd, .95)))
if video and os.path.exists(video):
    import cv2, numpy as np
    cap = cv2.VideoCapture(video)
    i = 0; worst = (0.0, 0.0); nbad = 0; vals = []; hworst = (0.0, 0.0); hbad = 0; hvals = []
    while True:
        ok, im = cap.read()
        if not ok or i >= len(rows): break
        r = rows[i]
        t, b, l, rr = [int(f(r, k, -1)) for k in ('px_top', 'px_bottom', 'px_left', 'px_right')]
        if b - t > 8 and rr - l > 4 and t >= 0:
            g = cv2.cvtColor(im[max(0, t):b, max(0, l):rr], cv2.COLOR_BGR2GRAY)
            if g.size:
                fr = float((g >= 245).mean())
                vals.append(fr)
                if fr > worst[0]: worst = (fr, f(r, 't'))
                if fr > 0.05: nbad += 1
                # L1h: the hero's own pixels -- the saturated suit (S > 90) closed / dilated into a silhouette mask; clipped pixels
                # inside it (a bright sky / haze behind the hero fills the box but is not the hero)
                hsv = cv2.cvtColor(im[max(0, t):b, max(0, l):rr], cv2.COLOR_BGR2HSV)
                m = ((hsv[..., 1] > 90) & (hsv[..., 2] > 35)).astype(np.uint8)
                m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
                m = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
                if m.sum() > 50:
                    fh = float((g[m] >= 245).mean())
                    hvals.append(fh)
                    if fh > hworst[0]: hworst = (fh, f(r, 't'))
                    if fh > 0.05: hbad += 1
        i += 1
    line('L1', nbad == 0, 'hero-box pixels at luma >= 245: p50 %.3f / p99 %.3f / max %.3f at %.2f s; frames > 5 %%: %d of %d'
         % (pct(vals, .5), pct(vals, .99), worst[0], worst[1], nbad, len(vals)))
    line('L1h', hbad == 0, 'hero-silhouette pixels (suit mask) at luma >= 245: p50 %.3f / p99 %.3f / max %.3f at %.2f s; frames > 5 %%: %d of %d'
         % (pct(hvals, .5), pct(hvals, .99), hworst[0], hworst[1], hbad, len(hvals)))
print('  => %s' % ('PASS' if all(res) else 'FAIL (%d lines)' % res.count(False)))
