#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 16: TRICK_CAMERA_SPEC.md (director, Fable 5.1) tests TC-A .. TC-K on the telemetry of a clip (60 fps; rendered 1080p run or a
# -nullrhi probe -- the px_* / hero_occl / video tests need a rendered run and print n/a otherwise).
#   usage: trickcam_check.py <telemetry.csv> <label> [--video <mp4>] [--tail 0.5] [--quiet]
# Window per trick program = rows with flip_t >= 0 (the program) through TAIL s (0.5) after its last row. Two readings are printed for
# every distribution test, so nothing is hidden behind a definition:
#   WIN  = the whole window (blend-in, hold, blend-out, tail)        HOLD = program rows (release .. catch) with flipcam_k >= 0.9 (the held trick camera)
# TC-B says it explicitly ("with flipcam_k >= 0.9": p95 / max; "whole window incl. blends": max <= 150 deg/s), TC-A's range is a hold
# number (a blend-in of 30-50 deg is the camera arriving). A line's verdict is PASS when the literal WIN reading passes; "PASS(hold)" when only
# the HOLD reading passes (blend frames break the band) -- the critic's number is the one to watch.
# pcm_* / px_* / view_sun_deg are logged at the start of the NEXT frame: shifted one row (as every other checker).
#   TC-A yaw offset      |pcm_yaw - travel heading at the release| p5-p95 in 30-60 deg; per-trick world-yaw range (hold) <= 20 deg
#   TC-B yaw rate        hold: p95 <= 40 deg/s, max <= 60; window incl. blends: max <= 150
#   TC-C hero height     hero_bbox_h p10 >= .12, p50 .18-.28, p90 <= .36 (+ the pixel mask, rendered runs)
#   TC-D placement       hero_cx p5-p95 inside .35-.60, hero_cy p5-p95 inside .28-.48
#   TC-E pitch           pcm_pitch (+ = up) p5 >= -8, p95 <= +8, |p50| <= 5; median at attach +0.5..1.0 s in 4-12 deg DOWN
#   TC-F height          z_m - pcm_z p50 0.5-2.0 m, p10 >= 0.2
#   TC-G safety          hero_in_frame 100 %, cam_in_geometry 0, cam_lens25 0 (lens sphere 0.25 m), hero_occl 0 (rendered)
#   TC-H sun / glare     view_sun_deg min >= 100; suit-mask luma >= 245 share <= 5 % on every window frame (video)
#   TC-I sky             ring >= 50 % sky AND hero h >= .15 on >= 35 % of trick samples (10 fps, video; sky_check.py does the pooled version)
#   TC-J readability     tuck head-hip axis turns >= 300 deg on screen per backDouble tuck (pose_sig, unchanged from round 13)
#   TC-K continuity      every frame of the clip: pitch <= 3 deg, yaw <= 4 deg, position <= 1.2 m per 1/60 s; blend-out >= 0.40 s from the attach
# plus the flip-quality lines kept from round 14 (E1 eased ends, H1 shapes >= 0.3 s).
import csv, math, sys, os
args = sys.argv[1:]
video = None; tail = 0.5; quiet = False
if '--video' in args:
    k = args.index('--video'); video = args[k + 1]; del args[k:k + 2]
if '--tail' in args:
    k = args.index('--tail'); tail = float(args[k + 1]); del args[k:k + 2]
if '--quiet' in args:
    args.remove('--quiet'); quiet = True
path, label = args[0], (args[1] if len(args) > 1 else '')
R = list(csv.DictReader(open(path)))
SH = ('pcm_x', 'pcm_y', 'pcm_z', 'pcm_pitch', 'pcm_yaw', 'pcm_fov', 'pcm_roll', 'px_top', 'px_bottom', 'px_left', 'px_right', 'view_sun_deg')
for i in range(len(R) - 1):
    for k in SH:
        if k in R[i + 1]: R[i][k] = R[i + 1][k]
R = R[:-1]
n = len(R)
def f(r, k, d=float('nan')):
    try:
        v = r.get(k, '')
        return float(v) if v not in ('', '-', None) else d
    except ValueError:
        return d
def pct(v, p):
    v = sorted(x for x in v if x == x)
    if not v: return float('nan')
    k = (len(v) - 1) * p; a = math.floor(k); b = min(a + 1, len(v) - 1)
    return v[a] + (v[b] - v[a]) * (k - a)
def wrap(a): return (a + 180.0) % 360.0 - 180.0
T = [f(r, 't') for r in R]
dt = (T[-1] - T[0]) / max(1, n - 1) if n > 1 else 1 / 60.0
TAILN = int(round(tail / dt))
out = []
def P(s=''): out.append(s)
nfail = [0]
def verdict(win_ok, hold_ok):
    if win_ok: return 'PASS'
    if hold_ok: return 'PASS(hold)'
    nfail[0] += 1
    return 'FAIL'
# ---- trick programs and windows
progs = []
i = 0
while i < n:
    if R[i].get('flip_prog', ''):
        j = i
        while j + 1 < n and R[j + 1].get('flip_prog', '') == R[i]['flip_prog'] and f(R[j + 1], 'flip_t') >= f(R[j], 'flip_t') - 1e-4: j += 1
        progs.append((i, j, R[i]['flip_prog']))
        i = j + 1
    else: i += 1
progs = [(a, b, nm) for a, b, nm in progs if nm != 'wallFront']   # the wall-run top-out flip is framed by the wall camera, not the trick camera
win = set(); hold = set()
pw = []   # per program (a, b, e, rows, holdrows)
fallbacks = []   # TC2 fallback: no clear spot at all -> plain chase (tier 3); not judged by the trick-camera lines, listed below
for a, b, nm in progs:
    if str(R[min(n - 1, a + 2)].get('flipcam_tier', '')).strip() == '3':
        fallbacks.append((nm, T[a], T[min(n - 1, b)]))
        continue
    e = min(n - 1, b + TAILN)
    rows = list(range(a, e + 1))
    hr = [k for k in range(a, b + 1) if f(R[k], 'flipcam_k', 0) >= 0.9]   # the held camera = program rows with k >= .9 (the blend-out after the catch is judged by TC-B WIN / TC-K)
    pw.append((a, b, e, nm, rows, hr))
    win.update(rows); hold.update(hr)
win = sorted(win); hold = sorted(hold)
P('%s (%s): %d flip programs, %.1f s, window rows %d, hold (flipcam_k >= .9) rows %d' % (label, os.path.basename(path), len(progs), T[-1], len(win), len(hold)))
if fallbacks:
    P('  TC2 fallback to the plain chase (no obstruction-free spot at any distance >= 4.0 m; not judged by TC-A..F/H, TC-G below covers them): ' + ', '.join('%s %.2f-%.2f s' % x for x in fallbacks))
if not pw:
    P('  no judged flip programs in this clip'); print('\n'.join(out)); sys.exit(0)
def stat(rows, fn):
    return [fn(R[k]) for k in rows]
# ---- TC-A
head0 = {a: math.degrees(math.atan2(f(R[a], 'vy'), f(R[a], 'vx'))) for a, *_ in pw}
def off_of(k, a): return abs(wrap(f(R[k], 'pcm_yaw') - head0[a]))
offs_w, offs_h = [], []
for a, b, e, nm, rows, hr in pw:
    offs_w += [off_of(k, a) for k in rows]; offs_h += [off_of(k, a) for k in hr]
pA_w = (pct(offs_w, .05), pct(offs_w, .95)); pA_h = (pct(offs_h, .05), pct(offs_h, .95))
okw = 30 <= pA_w[0] and pA_w[1] <= 60; okh = 30 <= pA_h[0] and pA_h[1] <= 60
rng_bad = []
for a, b, e, nm, rows, hr in pw:
    if len(hr) >= 3:
        u = [f(R[hr[0]], 'pcm_yaw')]
        for k in hr[1:]: u.append(u[-1] + wrap(f(R[k], 'pcm_yaw') - (u[-1])))
        rg = max(u) - min(u)
        rng_bad.append((nm, T[a], rg, len(hr)))
rg_ok = all(x[2] <= 20.0 for x in rng_bad)
P('TC-A yaw offset from the release heading: HOLD p5-p95 %.0f-%.0f deg (30-60), WIN %.0f-%.0f; per-trick world-yaw range over the hold: %s (<= 20) -> %s' % (
    pA_h[0], pA_h[1], pA_w[0], pA_w[1], ' '.join('%s@%.2f %.1f' % (nm, t, rg) for nm, t, rg, _ in rng_bad) or 'n/a', verdict(okh and rg_ok, okh and rg_ok)))
# ---- TC-B
def yrate(rows):
    v = []
    for k in rows:
        if k >= 1: v.append(abs(wrap(f(R[k], 'pcm_yaw') - f(R[k - 1], 'pcm_yaw'))) / dt)
    return v
rh = []; rw = []
for a, b, e, nm, rows, hr in pw:
    rh += yrate(hr); rw += yrate(rows)
ok = (pct(rh, .95) <= 40 and (max(rh) if rh else 0) <= 60 and (max(rw) if rw else 0) <= 150)
if not rh: ok = False
P('TC-B yaw rate: HOLD p95 %.1f / max %.1f deg/s (<= 40 / 60); WIN incl. blends max %.0f deg/s (<= 150) -> %s' % (
    pct(rh, .95), max(rh) if rh else float('nan'), max(rw) if rw else float('nan'), 'PASS' if ok else (nfail.__setitem__(0, nfail[0] + 1) or 'FAIL')))
# ---- TC-C (verdict on the rendered hero MASK when the run has pixels -- the critic's measure; the bone box (bones +-10 cm) is ~6-10 % larger)
hb_w = stat(win, lambda r: f(r, 'hero_bbox_h')); hb_h = stat(hold, lambda r: f(r, 'hero_bbox_h'))
def cband(v): return (pct(v, .10), pct(v, .50), pct(v, .90))
def mh(rows): return [(f(R[k], 'px_bottom') - f(R[k], 'px_top')) / 1080.0 for k in rows if f(R[k], 'px_top', -1) >= 0 and f(R[k], 'px_bottom', -1) > f(R[k], 'px_top', -1)]
mk_w, mk_h = mh(win), mh(hold)
has_mask = len(mk_w) > 30
cw, ch = cband(hb_w), cband(hb_h)
def okband(b): return b[0] >= .12 and .18 <= b[1] <= .28 and b[2] <= .36
if has_mask:
    mw, mhh = cband(mk_w), cband(mk_h)
    okw, okh = okband(mw), okband(mhh)
    mtxt = 'MASK WIN %.3f/%.3f/%.3f, HOLD %.3f/%.3f/%.3f | bone box WIN %.3f/%.3f/%.3f, HOLD %.3f/%.3f/%.3f' % (*mw, *mhh, *cw, *ch)
else:
    okw, okh = okband(cw), okband(ch)
    mtxt = 'bone box WIN %.3f/%.3f/%.3f, HOLD %.3f/%.3f/%.3f (mask n/a: no render)' % (*cw, *ch)
P('TC-C hero height p10/p50/p90 (>= .12 / .18-.28 / <= .36): %s -> %s' % (mtxt, verdict(okw, okh)))
# ---- TC-D
cx_w = stat(win, lambda r: f(r, 'hero_cx')); cx_h = stat(hold, lambda r: f(r, 'hero_cx'))
cy_w = stat(win, lambda r: f(r, 'hero_cy')); cy_h = stat(hold, lambda r: f(r, 'hero_cy'))
okw = pct(cx_w, .05) >= .35 and pct(cx_w, .95) <= .60 and pct(cy_w, .05) >= .28 and pct(cy_w, .95) <= .48
okh = pct(cx_h, .05) >= .35 and pct(cx_h, .95) <= .60 and pct(cy_h, .05) >= .28 and pct(cy_h, .95) <= .48
P('TC-D placement: WIN cx %.2f-%.2f cy %.2f-%.2f, HOLD cx %.2f-%.2f cy %.2f-%.2f (cx .35-.60, cy .28-.48) -> %s' % (
    pct(cx_w, .05), pct(cx_w, .95), pct(cy_w, .05), pct(cy_w, .95), pct(cx_h, .05), pct(cx_h, .95), pct(cy_h, .05), pct(cy_h, .95), verdict(okw, okh)))
# ---- TC-E
pp_w = stat(win, lambda r: f(r, 'pcm_pitch')); pp_h = stat(hold, lambda r: f(r, 'pcm_pitch'))
okw = pct(pp_w, .05) >= -8 and pct(pp_w, .95) <= 8 and abs(pct(pp_w, .5)) <= 5
okh = pct(pp_h, .05) >= -8 and pct(pp_h, .95) <= 8 and abs(pct(pp_h, .5)) <= 5
att = [k for k in range(1, n) if R[k]['mode'] == 'swing' and R[k - 1]['mode'] != 'swing']
settle = []
for a, b, e, nm, rows, hr in pw:
    k = next((k for k in att if k >= b), None)
    if k is None: continue
    w = [f(R[j], 'pcm_pitch') for j in range(k, n) if T[k] + 0.5 <= T[j] <= T[k] + 1.0]
    if len(w) >= 20: settle.append((nm, T[k], pct(w, .5)))
sok = all(-12 <= m <= -4 for _, _, m in settle)
P('TC-E pitch (+ up): WIN p5/p50/p95 %.1f/%.1f/%.1f, HOLD %.1f/%.1f/%.1f (p5 >= -8, p95 <= +8, |p50| <= 5); median at attach +0.5..1.0 s (4-12 down): %s -> %s' % (
    pct(pp_w, .05), pct(pp_w, .5), pct(pp_w, .95), pct(pp_h, .05), pct(pp_h, .5), pct(pp_h, .95),
    ' '.join('%.2f:%+.1f' % (t, m) for _, t, m in settle) or 'n/a', verdict(okw and sok, okh and sok)))
# ---- TC-F
dz_w = stat(win, lambda r: f(r, 'z_m') - f(r, 'pcm_z')); dz_h = stat(hold, lambda r: f(r, 'z_m') - f(r, 'pcm_z'))
okw = .5 <= pct(dz_w, .5) <= 2.0 and pct(dz_w, .1) >= .2; okh = .5 <= pct(dz_h, .5) <= 2.0 and pct(dz_h, .1) >= .2
P('TC-F lens below the hips (z_m - pcm_z): WIN p10/p50/p90 %.2f/%.2f/%.2f, HOLD %.2f/%.2f/%.2f m (p50 .5-2.0, p10 >= .2) -> %s' % (
    pct(dz_w, .1), pct(dz_w, .5), pct(dz_w, .9), pct(dz_h, .1), pct(dz_h, .5), pct(dz_h, .9), verdict(okw, okh)))
# ---- TC-G
_ws = set(win)
for nm_, t0_, t1_ in fallbacks:
    _ws.update(k for k in range(n) if t0_ - 1e-6 <= T[k] <= t1_ + tail)   # safety lines judge the fallback too
win = sorted(_ws)
inf = [k for k in win if f(R[k], 'hero_in_frame', 1) < 0.5]
geo = [k for k in win if f(R[k], 'cam_in_geometry', 0) > 0.5]
lens = [k for k in win if f(R[k], 'cam_lens25', 0) > 0.5]
occl = [k for k in win if f(R[k], 'hero_occl', 0) > 0.001]
has_occl = any(f(R[k], 'hero_occl', -1) >= 0 for k in win) and video is not None
okg = not inf and not geo and not lens and not occl
if not okg: nfail[0] += 1
def rng(ks): return '%.2f-%.2f' % (T[ks[0]], T[ks[-1]]) if ks else ''
P('TC-G safety: hero out of frame %d rows %s | camera in geometry %d %s | lens sphere 0.25 m touching %d %s | hero occluded %s -> %s' % (
    len(inf), rng(inf), len(geo), rng(geo), len(lens), rng(lens), ('%d %s' % (len(occl), rng(occl))) if has_occl else 'n/a (no render)', 'PASS' if okg else 'FAIL'))
# ---- TC-H
vs = [f(R[k], 'view_sun_deg', -1) for k in win if f(R[k], 'flipcam_k', 0) >= 0.5]; vs = [x for x in vs if x >= 0]   # as r14 S1 / suncam_check: trick frames = flipcam_k >= .5
vs9 = [f(R[k], 'view_sun_deg', -1) for k in hold]; vs9 = [x for x in vs9 if x >= 0]                                     # the held camera only
okh1 = bool(vs) and min(vs) >= 100.0
okh1_hold = bool(vs9) and min(vs9) >= 100.0
lum_txt = 'suit-mask luma n/a (no video)'
okh2 = True
if video and os.path.exists(video):
    try:
        import cv2, numpy as np
        cap = cv2.VideoCapture(video); i = 0; worst = (0.0, 0.0); nbad = 0; vals = []; want = set(win)
        while True:
            ok_, im = cap.read()
            if not ok_ or i >= n: break
            if i in want:
                r = R[i]
                t, b, l, rr = [int(f(r, k, -1)) for k in ('px_top', 'px_bottom', 'px_left', 'px_right')]
                if b - t > 8 and rr - l > 4 and t >= 0:
                    crop = im[max(0, t):b, max(0, l):rr]
                    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                    m = ((hsv[..., 1] > 90) & (hsv[..., 2] > 35)).astype(np.uint8)   # the saturated suit, closed + dilated into a silhouette
                    # round 16: a TIGHT suit mask (close 9x9 fills the white emblem / specular spots inside the suit, dilate 3x3): the r14/r15 21x21 close + 5x5
                    # dilate bridged the gaps between the arms and counted the bright SKY there as 'suit' (f1 3.55 s: 7 % 'clipped', the suit itself not)
                    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)); m = cv2.dilate(m, np.ones((3, 3), np.uint8)) > 0
                    if m.sum() > 50:
                        fh = float((g[m] >= 245).mean()); vals.append(fh)
                        if fh > worst[0]: worst = (fh, T[i])
                        if fh > 0.05: nbad += 1
            i += 1
        okh2 = nbad == 0
        lum_txt = 'suit-mask luma>=245 share: p99 %.3f max %.3f @ %.2f s, frames > 5 %%: %d of %d' % (pct(vals, .99), worst[0], worst[1], nbad, len(vals))
    except ImportError:
        lum_txt = 'suit-mask luma n/a (opencv missing)'
okH = okh1 and okh2
okHh = okh1_hold and okh2
if not okHh: nfail[0] += 1
P('TC-H sun/glare: view_sun_deg min %.0f (flipcam_k >= .5, r14 S1) / %.0f (held, k >= .9) (>= 100); %s -> %s' % (min(vs) if vs else float('nan'), min(vs9) if vs9 else float('nan'), lum_txt, 'PASS' if okH else ('PASS(hold)' if okHh else 'FAIL')))
# ---- TC-I (video)
P('TC-I sky: run sky_check.py <round dir> <clips> (pooled over f1-f5; >= 35 %% of trick samples with ring >= 50 %% sky and hero h >= .15)')
# ---- TC-J + flip quality lines
def unwrap(v):
    u = [v[0]]
    for x in v[1:]:
        d = (x - u[-1] + 180) % 360 - 180
        u.append(u[-1] + d)
    return u
bp = [f(R[min(k + 1, n - 1)], 'body_pitch_deg') for k in range(n)]
def sig_head(k):
    s = R[min(k + 1, n - 1)].get('pose_sig', '').split()
    return (float(s[0]), float(s[1])) if len(s) >= 2 else None
jlines = []; qlines = []; jfail = 0
for a, b, nm in progs:
    if b >= n - 2:
        qlines.append('-- %s %.2f-%.2f s: still playing on the clip\'s last frame -- not judged' % (nm, T[a], T[b])); continue
    runs = []
    for k in range(a, b + 1):
        s = R[k].get('flip_shape', '')
        if runs and runs[-1][0] == s: runs[-1][2] = k
        else: runs.append([s, k, k])
    qlines.append('-- %s %.2f-%.2f s   H1 shapes: ' % (nm, T[a], T[b]) + ' '.join('%s %.2f' % (s, T[e] - T[s0] + 1 / 60.0) for s, s0, e in runs))
    for s, s0, e in runs:
        d = T[e] - T[s0] + 1 / 60.0
        last = (s0, e) == (runs[-1][1], runs[-1][2])
        if d < 0.3 - 1 / 120.0 and not (last and s == 'Reach'):
            qlines.append('      H1 FAIL %s shown %.2f s < 0.3' % (s, d))
    for s, s0, e in runs:
        if s != 'Tuck' or T[e] - T[s0] < 0.2 or nm == 'wallFront': continue
        hv = [h for h in (sig_head(k) for k in range(s0, e + 1)) if h]
        if len(hv) < 3: continue
        L = [math.hypot(*h) for h in hv]; mx = max(L)
        angs = [math.degrees(math.atan2(h[0], h[1])) for h, l in zip(hv, L) if l >= 0.25 * mx]
        u = unwrap(angs); turn = abs(u[-1] - u[0])
        prog_turn = abs(f(R[e], 'flip_pitch_deg') - f(R[s0], 'flip_pitch_deg'))
        good = turn >= 300 or prog_turn < 400
        jlines.append('%s tuck %.2f-%.2f: axis turns %.0f deg on screen (program %.0f) %s' % (nm, T[s0], T[e], turn, prog_turn, 'ok' if good else 'SHORT'))
        if not good: jfail += 1
    uu = unwrap([bp[k] for k in range(a, b + 1)])
    step = 2
    rate = [abs(uu[min(len(uu) - 1, i + step)] - uu[max(0, i - step)]) / max(1e-3, T[a + min(len(uu) - 1, i + step)] - T[a + max(0, i - step)]) for i in range(len(uu))]
    for s, s0, e in runs:
        if s not in ('Tuck', 'Pike') or T[e] - T[s0] < 0.2: continue
        seg = rate[s0 - a:e - a + 1]; m = len(seg); q1, q3 = max(1, m // 4), max(1, m - m // 4)
        si, sm, so = sum(seg[:q1]) / q1, sum(seg[q1:q3]) / max(1, q3 - q1), sum(seg[q3:]) / max(1, m - q3)
        good = si <= 0.7 * sm and so <= 0.7 * sm
        qlines.append('      E1 %s %.2f-%.2f ends %.0f%% / %.0f%% of mid, peak %.0f deg/s %s' % (s, T[s0], T[e], 100 * si / max(1, sm), 100 * so / max(1, sm), max(seg), 'ok' if good else 'FAIL'))
if jfail: nfail[0] += 1
P('TC-J readability: ' + ('; '.join(jlines) if jlines else 'no backDouble / tuck run in this clip') + ' -> ' + ('FAIL' if jfail else 'PASS' if jlines else 'n/a'))
# ---- TC-K
pitch = [f(r, 'pcm_pitch') for r in R]; yaw = [f(r, 'pcm_yaw') for r in R]
px = [(f(r, 'pcm_x'), f(r, 'pcm_y'), f(r, 'pcm_z')) for r in R]
bp_, by_, bpos = [], [], []
for k in range(1, n):
    if R[k - 1]['frame'] == '' or f(R[k], 't') - f(R[k - 1], 't') > 2.5 * dt: continue
    bp_.append((abs(pitch[k] - pitch[k - 1]), k)); by_.append((abs(wrap(yaw[k] - yaw[k - 1])), k))
    bpos.append((math.dist(px[k], px[k - 1]), k))
mp, my, mpos = max(bp_), max(by_), max(bpos)
kok = mp[0] <= 3.0 and my[0] <= 4.0 and mpos[0] <= 1.2
outs = []   # (attach t, seconds from the attach until flipcam_k <= 0.5, until <= 0.02 (nan = the next trick starts first / clip ends))
for a, b, e, nm, rows, hr in pw:
    k = next((k for k in att if k >= b - 2), None)
    if k is None: continue
    j = next((j for j in range(k, n) if f(R[j], 'flipcam_k', 1) <= 0.50), None)
    j2 = next((j for j in range(k, n) if f(R[j], 'flipcam_k', 1) <= 0.02), None)
    outs.append((T[k], (T[j] - T[k]) if j is not None else float('nan'), (T[j2] - T[k]) if j2 is not None else float('nan')))
ook = all(x[1] >= 0.40 for x in outs if x[1] == x[1])
if not (kok and ook): nfail[0] += 1
P('TC-K continuity (whole clip): max pitch %.2f deg/frame @ %.2f s (<= 3), yaw %.2f @ %.2f s (<= 4), position %.2f m @ %.2f s (<= 1.2); blend-out, seconds from the attach until flipcam_k <= .5 (and <= .02): %s (>= 0.40) -> %s' % (
    mp[0], T[mp[1]], my[0], T[my[1]], mpos[0], T[mpos[1]], ' '.join('%.2f:%.2f(%.2f)' % x for x in outs) or 'n/a', 'PASS' if kok and ook else 'FAIL'))
# ---- selection log
tiers = []
for a, b, e, nm, rows, hr in pw:
    r = R[min(n - 1, a + 2)]
    tiers.append('%s@%.2f off %+.0f tier %s dist %.1f->%.1f' % (nm, T[a], f(r, 'flipcam_yaw_deg', 0), r.get('flipcam_tier', '?'), f(r, 'flipcam_dist_m', 0), min(f(R[k], 'flipcam_dist_m', 99) for k in hold if a <= k <= b) if any(a <= k <= b for k in hold) else 0))
P('selection: ' + ' | '.join(tiers))
if not quiet:
    for q in qlines: P(q)
P('SUMMARY %s: %d FAIL line(s)' % (label, nfail[0]))
print('\n'.join(out))
