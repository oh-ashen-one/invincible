#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 23 checks (director r23 target: the vertical wall run must READ as a sprint from the existing wall camera).
#   V23  r22 critic tests, verbatim, on BOTH windows (w2 1.0-2.8 s, c 2.65-4.15 s):
#        a) foot_sep_run_m crosses below .15 m and above .35 m >= 4 times per second (each change between the two states = one crossing)
#        b) bbox_w (hero_bbox_w, the projected bone box) changes >= 25 % within EVERY 0.4 s window: max / min - 1 >= .25
#        c) legs visibly apart in >= 6 of 10 frames at 12 fps (contact sheet; numeric proxy: 3D ankle separation >= .30 m)
#   X23  excursion: per recovery (a foot off the face between two touchdowns) peak toe off the face >= .25 m with that knee .35-.50 m
#        off it at the peak, stance foot on the face; touchdowns alternate L/R with gaps <= .18 s; torso 5-20 deg off wall-up;
#        hips <= .45 m off the face (every row)
#   T22  camera pitch 20-65 deg up on the c vertical window; Z23 w2 zip fire -> perch <= 2 s
# usage: r23_checks.py <dir> [--sheets <dir>] [--video]   (<dir>/<clip>_telemetry.csv or <dir>/<clip>/<clip>_telemetry.csv)
import csv, os, subprocess, sys
import numpy as np
D = sys.argv[1]
ARGS = sys.argv[2:]
SHEETS = ARGS[ARGS.index('--sheets') + 1] if '--sheets' in ARGS else None
OUT = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)
def fl(r, k, d=float('nan')):
    try: return float(r.get(k, ''))
    except (TypeError, ValueError): return d
def sh(rows, k, i): return fl(rows[min(i + 1, len(rows) - 1)], k)   # pose columns are sampled one row late
def find(name):
    for p in (os.path.join(D, name + '_telemetry.csv'), os.path.join(D, name, name + '_telemetry.csv')):
        if os.path.exists(p): return p
    return None
def load(name):
    p = find(name)
    return list(csv.DictReader(open(p))) if p else None
def med(v): v = sorted(v); return v[len(v) // 2] if v else float('nan')

WINDOWS = (('w2_wallrun_side_zip', 1.0, 2.8), ('c_wallrun_perch', 2.65, 4.15))
ok_all = True
P('== V23  r22 critic tests on the vertical run (verbatim), both windows')
for name, t0, t1 in WINDOWS:
    rows = load(name)
    if not rows: P(f'  {name}: no telemetry'); ok_all = False; continue
    ix = [i for i, r in enumerate(rows) if t0 - 1e-6 <= fl(r, 't') <= t1 + 1e-6]
    modes = sorted({rows[i]['mode'] + '/' + rows[i]['sub'] for i in ix})
    # a) crossings
    st, n = None, 0
    for i in ix:
        s = sh(rows, 'foot_sep_run_m', i)
        if s < 0: continue
        if s < 0.15 and st != 'lo': n += st is not None; st = 'lo'
        elif s > 0.35 and st != 'hi': n += st is not None; st = 'hi'
    dur = fl(rows[ix[-1]], 't') - fl(rows[ix[0]], 't')
    a_ok = n / dur >= 4
    # b) bbox_w windows
    ts = [fl(rows[i], 't') for i in ix]; bw = [sh(rows, 'hero_bbox_w', i) for i in ix]
    worst, nwin, npass = 9.0, 0, 0
    for k in range(len(ix)):
        if ts[k] + 0.4 > ts[-1] + 1e-6: break
        w = [bw[j] for j in range(k, len(ix)) if ts[j] <= ts[k] + 0.4 + 1e-6 and bw[j] > 0]
        if not w: continue
        ch = max(w) / min(w) - 1; nwin += 1; npass += ch >= 0.25; worst = min(worst, ch)
    b_ok = nwin > 0 and npass == nwin
    # c) 12 fps proxy
    apart, tot, det = 0, 0, []
    for k in range(10):
        t = t0 + 0.2 + k / 12.0
        i = min(ix, key=lambda j: abs(fl(rows[j], 't') - t))
        a3 = sh(rows, 'ankle_sep_3d_m', i)
        tot += 1; apart += a3 >= 0.30; det.append(f'{t:.2f}:{a3:.2f}')
    c_ok = apart >= 6
    ok_all &= a_ok and b_ok and c_ok
    P(f'  {name} {t0:.2f}-{t1:.2f} s ({len(ix)} rows; {", ".join(modes)})')
    P(f'    a) foot_sep_run crossings {n} in {dur:.2f} s = {n / dur:.1f}/s (>= 4) -> {"PASS" if a_ok else "FAIL"}')
    P(f'    b) bbox_w {min(b for b in bw if b > 0):.3f}-{max(bw):.3f}; 0.4 s windows with >= 25 % change {npass}/{nwin}, worst {100 * worst:.0f} % -> {"PASS" if b_ok else "FAIL"}')
    P(f'    c) 12 fps frames from {t0 + 0.2:.2f} s, 3D ankle sep >= .30 m: {apart}/{tot} [{" ".join(det)}] -> {"PASS" if c_ok else "FAIL"} (proxy; see the sheet)')

P('\n== X23  excursion (director r23): recovery toe >= .25 m off the face with the knee .35-.50 m at that peak; stance on the face;')
P('         touchdowns alternate, gaps <= .18 s; torso 5-20 deg off wall-up; hips <= .45 m off the face')
for name, t0, t1 in WINDOWS:
    rows = load(name)
    if not rows: continue
    ix = [i for i, r in enumerate(rows) if t0 - 1e-6 <= fl(r, 't') <= t1 + 1e-6 and r['mode'] == 'wall']
    tds, recs = [], []
    for s in ('l', 'r'):
        prev, cur = None, []
        for i in ix:
            fw = sh(rows, 'foot_wall_' + s, i); on = fw <= 0.08
            if on and prev is False:
                tds.append((fl(rows[i], 't'), s))
                if cur:
                    j = max(cur, key=lambda q: sh(rows, 'foot_wall_' + s, q))
                    recs.append((fl(rows[j], 't'), s, sh(rows, 'foot_wall_' + s, j), sh(rows, 'knee_wall_' + s, j)))
                cur = []
            if not on: cur.append(i)
            prev = on
    tds.sort(); gaps = [b[0] - a[0] for a, b in zip(tds, tds[1:])]
    alt = sum(a[1] != b[1] for a, b in zip(tds, tds[1:]))
    recs.sort()
    good = [r for r in recs if r[2] >= 0.25 and 0.35 <= r[3] <= 0.50]
    tw = [sh(rows, 'torso_wallup_deg', i) for i in ix]; tw = [x for x in tw if x >= 0]
    hw = [sh(rows, 'hip_wall_m', i) for i in ix]; hw = [x for x in hw if x > -0.5]
    P(f'  {name}: recoveries {len(recs)}, toe >= .25 & knee .35-.50 at the peak {len(good)}/{len(recs)} '
      f'[{" ".join(f"{t:.2f}{s}:{f:.2f}/{k:.2f}" for t, s, f, k in recs)}]')
    P(f'    touchdowns {len(tds)}, alternating {alt}/{max(len(tds) - 1, 0)}, gap med {med(gaps):.3f} max {max(gaps) if gaps else float("nan"):.3f} s'
      f' (<= .18: {sum(g <= 0.18 + 1e-6 for g in gaps)}/{len(gaps)})')
    if tw: P(f'    torso off wall-up {min(tw):.1f}-{max(tw):.1f} deg, med {med(tw):.1f}; 5-20 deg {100 * sum(5 <= x <= 20 for x in tw) / len(tw):.0f} %')
    if hw: P(f'    hips off the face {min(hw):.2f}-{max(hw):.2f} m; <= .45 m {100 * sum(x <= 0.45 for x in hw) / len(hw):.0f} %')

rows = load('c_wallrun_perch')
if rows:
    cp = [fl(r, 'cam_pitch_deg') for r in rows if 2.65 <= fl(r, 't') <= 4.15 and r['mode'] == 'wall']
    st = [x for x in cp[int(len(cp) * 0.1):]]
    P(f'\n== T22  c camera pitch on the vertical window: {min(cp):.1f}..{max(cp):.1f} deg (steady after the blend-in {min(st):.1f}..{max(st):.1f}); '
      f'20-65 up {100 * sum(20 <= x <= 65 for x in cp) / len(cp):.0f} % of rows')
rows = load('w2_wallrun_side_zip')
if rows:
    fire = next((r for r in rows if r['sub'] == 'zipFire'), None)
    if fire:
        tf = fl(fire, 't'); pr = next((r for r in rows if fl(r, 't') > tf and r['mode'] == 'perch'), None)
        P(f'\n== Z23  w2 zip: fire {tf:.2f} s ({fire["zip_why"]}), perch '
          + (f'{fl(pr, "t"):.2f} s at z {fl(pr, "z_m"):.1f} -> {fl(pr, "t") - tf:.2f} s {"PASS" if fl(pr, "t") - tf <= 2.0 else "FAIL"}' if pr else f'none by {fl(rows[-1], "t"):.2f} s (z {fl(rows[-1], "z_m"):.1f}) -> FAIL'))

if SHEETS:
    from PIL import Image, ImageDraw
    os.makedirs(SHEETS, exist_ok=True)
    for name, t0, t1 in WINDOWS:
        mp4 = os.path.join(D, name + '.mp4')
        rows = load(name)
        if not os.path.exists(mp4) or not rows: continue
        tiles = []
        for k in range(10):
            t = t0 + 0.2 + k / 12.0
            i = min(range(len(rows)), key=lambda j: abs(fl(rows[j], 't') - t))
            r = rows[min(i + 1, len(rows) - 1)]
            raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', f'{t:.4f}', '-i', mp4, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                 capture_output=True).stdout
            if len(raw) < 1920 * 1080 * 3: continue
            im = Image.fromarray(np.frombuffer(raw[:1920 * 1080 * 3], np.uint8).reshape(1080, 1920, 3))
            l, rr, tp, bt = fl(r, 'px_left'), fl(r, 'px_right'), fl(r, 'px_top'), fl(r, 'px_bottom')
            cx = (l + rr) / 2 if rr > l > 0 else 960; cy = (tp + bt) / 2 if bt > tp > 0 else 540
            if cx <= 1.5: cx *= 1920; cy *= 1080
            box = (int(cx - 210), int(cy - 300), int(cx + 210), int(cy + 300))
            tile = im.crop(box).resize((280, 400))
            ImageDraw.Draw(tile).text((6, 6), f'{t:.2f}s', fill=(255, 255, 0))
            tiles.append(tile)
        if tiles:
            sheet = Image.new('RGB', (280 * 5, 400 * ((len(tiles) + 4) // 5)))
            for k, tl in enumerate(tiles): sheet.paste(tl, ((k % 5) * 280, (k // 5) * 400))
            out = os.path.join(SHEETS, f'{name}_vertical_{t0 + 0.2:.2f}_12fps.png'); sheet.save(out); P(f'  sheet {out}')

P('\nV23 overall (a, b, c proxy on both windows): ' + ('PASS' if ok_all else 'FAIL'))
open(os.path.join(D, 'R23_CHECK.txt') if os.path.isdir(D) else 'R23_CHECK.txt', 'w').write('\n'.join(OUT) + '\n')
