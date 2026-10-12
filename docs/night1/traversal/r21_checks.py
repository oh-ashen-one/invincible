#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 21 checker (critic r20 W test, verbatim targets): wall-run sprint stride split into ALONG-RUN foot separation and the
# lateral (ACROSS-RUN) knee gap, contact cadence, swing knee off the wall, posture (vertical: body within 15 deg of the wall's up axis;
# side: body axis 10-40 deg above the run line toward the wall-up axis), side-run length before the first input, the 8 fps frame
# test (w1 2.9-3.6 s: legs apart in >= 3 of 6 frames) and the setback step (c 3.4-3.7 s: every hand / toe within 0.3 m of the support
# surface).  Usage: r21_checks.py <round dir> [--sheets <out dir>]   (pose columns are sampled one row late: shifted())
import csv, glob, os, subprocess, sys

RD = sys.argv[1]
ARGS = sys.argv[2:]
SHEETS = ARGS[ARGS.index('--sheets') + 1] if '--sheets' in ARGS else None
OUT = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)
def load(p):
    with open(p) as f: return list(csv.DictReader(f))
def fl(r, k, d=float('nan')):
    try: return float(r.get(k, ''))
    except (TypeError, ValueError): return d
def sh(rows, k, i):
    return fl(rows[min(i + 1, len(rows) - 1)], k)
def med(v): v = sorted(v); return v[len(v) // 2] if v else float('nan')
def at(rows, t): return min(range(len(rows)), key=lambda k: abs(fl(rows[k], 't') - t))

CLIPS = sorted(glob.glob(os.path.join(RD, '*_telemetry.csv')))
P('== W21  wall-run stride (sprint): along-run foot separation peaks >= .35 m every cycle; lateral knee gap <= .35 m; a foot touches down every <= .18 s;')
P('         swing knee off the wall; vertical body within 15 deg of wall-up; side body 10-40 deg above the run line (head leading); limbs (hands / toes) <= .3 m')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    if not rows or 'foot_sep_run_m' not in rows[0]: continue
    wr = [i for i, r in enumerate(rows) if r['mode'] == 'wall' and r['sub'] in ('wallRun', 'wallRunSide')]
    if not wr: continue
    # steady rows: skip the first 0.1 s of every contiguous wall-run segment (entry blend)
    segs = []; cur = []
    for i in wr:
        if cur and i != cur[-1] + 1: segs.append(cur); cur = []
        cur.append(i)
    if cur: segs.append(cur)
    for kind in ('wallRun', 'wallRunSide'):
        ix = [i for s in segs for i in s if rows[i]['sub'] == kind and fl(rows[i], 't') >= fl(rows[s[0]], 't') + 0.1]
        if not ix: continue
        sep = [sh(rows, 'foot_sep_run_m', i) for i in ix]
        klat = [sh(rows, 'knee_gap_lat_m', i) for i in ix]
        kw = [max(sh(rows, 'knee_wall_l', i), sh(rows, 'knee_wall_r', i)) for i in ix]
        lim = [sh(rows, 'limb_wall_max_m', i) for i in ix]
        # cycles = gait phase wraps (one cycle = two steps); peak along-run separation per half cycle (one step)
        steps = []; cur = []; prevph = None
        for i in ix:
            ph = fl(rows[i], 'gait_ph'); half = int(ph * 2) if ph == ph else 0
            if prevph is not None and half != prevph and cur: steps.append(cur); cur = []
            cur.append(i); prevph = half
        if cur: steps.append(cur)
        full = steps[1:-1] if len(steps) > 2 else steps
        peaks = [max(sh(rows, 'foot_sep_run_m', i) for i in s) for s in full]
        # touchdowns: a toe reaching the wall (<= .08 m) after being off it
        tds = []
        for side in ('l', 'r'):
            prev = None
            for i in ix:
                on = sh(rows, 'foot_wall_' + side, i) <= 0.08
                if prev is False and on: tds.append(fl(rows[i], 't'))
                prev = on
        tds.sort(); gaps = [b - a for a, b in zip(tds, tds[1:]) if b - a < 0.6]
        line = (f'  {name} {kind}: {len(ix)} rows | along-run foot sep med {med(sep):.2f} max {max(sep):.2f} m, per-step peaks min {min(peaks) if peaks else float("nan"):.2f}'
                f' ({sum(1 for x in peaks if x >= 0.35)}/{len(peaks)} steps >= .35) | lateral knee gap med {med(klat):.2f} max {max(klat):.2f} m'
                f' | knee off wall med {med(kw):.2f} max {max(kw):.2f} m | hands/toes off surface max {max(lim):.2f} m (p90 {sorted(lim)[int(len(lim) * .9)]:.2f})'
                f' | touchdowns {len(tds)}, longest gap {max(gaps) if gaps else float("nan"):.3f} s (med {med(gaps):.3f})')
        if kind == 'wallRun':
            bw = [sh(rows, 'body_wallup_deg', i) for i in ix]; bw = [x for x in bw if x >= 0]
            line += f' | body-to-wall-up <= 15 deg {sum(1 for x in bw if x <= 15) / max(len(bw), 1) * 100:.0f} % (med {med(bw):.1f})'
        else:
            el = [sh(rows, 'body_run_elev_deg', i) for i in ix]; el = [x for x in el if x > -900]
            line += f' | body above run line 10-40 deg {sum(1 for x in el if 10 <= x <= 40) / max(len(el), 1) * 100:.0f} % (med {med(el):.1f}, min {min(el):.1f}, max {max(el):.1f})'
        P(line)

P('\n== S21  side run before the first input (target >= 0.6 s)')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    i0 = next((i for i, r in enumerate(rows) if r['mode'] == 'wall' and r['sub'] == 'wallRunSide'), None)
    if i0 is None: continue
    t0 = fl(rows[i0], 't')
    j = next((k for k in range(i0 + 1, len(rows)) if any(fl(rows[k], c) > 0 and fl(rows[k - 1], c) <= 0 for c in ('in_zip', 'in_swing', 'in_jump', 'in_drop'))), None)
    tend = next((fl(rows[k], 't') for k in range(i0, len(rows)) if rows[k]['sub'] != 'wallRunSide'), fl(rows[-1], 't'))
    P(f'  {name}: wallRunSide from {t0:.2f} s; first button press {"%.2f" % fl(rows[j], "t") if j else "none"} s -> side run before input '
      f'{(fl(rows[j], "t") if j else tend) - t0:.2f} s; side run ends {tend:.2f} s -> ' + ('PASS' if ((fl(rows[j], 't') if j else tend) - t0) >= 0.6 else 'FAIL'))

P('\n== F8  critic r20 frame test: w1 2.9-3.6 s at 8 fps, legs apart (along-run foot sep >= .30 m) in >= 3 of 6 frames')
def frames8(name, t0, t1, thr=0.30):
    p = os.path.join(RD, name + '_telemetry.csv')
    if not os.path.exists(p): return
    rows = load(p)
    ts = [t0 + k / 8 for k in range(int(round((t1 - t0) * 8)))]
    v = []
    for t in ts:
        i = at(rows, t)
        v.append((t, rows[i]['sub'], sh(rows, 'foot_sep_run_m', i), max(sh(rows, 'knee_wall_l', i), sh(rows, 'knee_wall_r', i))))
    ok = sum(1 for _, s, x, _k in v if x >= thr)
    P(f'  {name} {t0}-{t1} s: ' + ', '.join(f'{t:.3f}:{s}:{x:.2f}/{k:.2f}' for t, s, x, k in v) + f'  (sep / knee off wall) -> {ok}/{len(v)} apart -> ' + ('PASS' if ok >= 3 else 'FAIL'))
    if SHEETS:
        mp4 = os.path.join(RD, name + '.mp4')
        if os.path.exists(mp4):
            os.makedirs(SHEETS, exist_ok=True)
            out = os.path.join(SHEETS, f'{name}_{t0}-{t1}_8fps.png')
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', str(t0), '-t', str(t1 - t0), '-i', mp4, '-vf', 'fps=8,crop=iw/2:ih*0.75:iw/4:ih/8,scale=480:-1,tile=6x1', '-frames:v', '1', out])
            P(f'     sheet {out}')
frames8('w1_wallrun_tall_zip', 2.9, 3.6)
frames8('w2_wallrun_side_zip', 3.2, 3.9)
frames8('c_wallrun_perch', 2.8, 3.5)

P('\n== M21  setback step (critic r20: c 3.4-3.7 s every limb within 0.3 m of the wall; r20 = a 3 m hop)')
p = os.path.join(RD, 'c_wallrun_perch_telemetry.csv')
if os.path.exists(p):
    rows = load(p)
    ix = [i for i, r in enumerate(rows) if 3.4 <= fl(r, 't') <= 3.7]
    lim = [(fl(rows[i], 't'), sh(rows, 'limb_wall_max_m', i), max(sh(rows, 'knee_wall_l', i), sh(rows, 'knee_wall_r', i)), rows[i]['mode'] + '/' + rows[i]['sub']) for i in ix]
    bad = [x for x in lim if x[1] > 0.3 or x[1] < 0]
    P(f'  c 3.4-3.7 s: {len(lim)} rows, hands / toes off the support surface max {max(x[1] for x in lim):.2f} m, knees max {max(x[2] for x in lim):.2f} m, modes {sorted(set(x[3] for x in lim))} -> '
      + ('PASS' if not bad else f'FAIL ({len(bad)} rows, first {bad[0][0]:.2f} s {bad[0][1]:.2f} m)'))
    sets = int(fl(rows[-1], 'setbacks', 0)); tops = int(fl(rows[-1], 'topouts', 0))
    z = [fl(rows[i], 'z_m') for i in ix]
    P(f'  setbacks {sets}, top-outs {tops}; hero z over 3.4-3.7 s {min(z):.1f} .. {max(z):.1f} m')

with open(os.path.join(RD, 'R21_CHECK.txt'), 'w') as f: f.write('\n'.join(OUT) + '\n')
