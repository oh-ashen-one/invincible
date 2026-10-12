#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 20 checker: world parity (floor audit vs a top-down depth render), camera occlusion / luma per clip, street-axis hold,
# perch occlusion after landing, wall-run top-outs / setbacks, E from a side run, wall posture numbers, air body-to-velocity,
# zip reach, mouse-look injection, lit mid-air landing check.  Usage: r20_checks.py <round dir> [--depth <depth csv>] [--frames]
import csv, glob, gzip, math, os, subprocess, sys

RD = sys.argv[1]
ARGS = sys.argv[2:]
DEPTH = ARGS[ARGS.index('--depth') + 1] if '--depth' in ARGS else os.path.join(RD, 'depth_audit.csv')
OUT = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)

def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return rows

def fl(r, k, d=float('nan')):
    try: return float(r.get(k, ''))
    except (TypeError, ValueError): return d

def shifted(rows, k, i):
    # pose / pixel columns are sampled at the start of the next frame: row i's pose is in row i+1
    j = min(i + 1, len(rows) - 1)
    return fl(rows[j], k)

# ------------------------------------------------------------------ F: floor audit vs depth render
P('== F  world parity: traversal floor (GroundHeight from 600 m) vs a top-down orthographic scene-depth render, 5 m grid')
if os.path.exists(DEPTH):
    import numpy as np
    rows = load(DEPTH)
    raw = os.path.splitext(DEPTH)[0] + '_solid_raw.csv'
    best = None
    if os.path.exists(raw):
        with open(raw) as f:
            hdr = f.readline().split()
            meta = dict(zip(hdr[1::2], hdr[2::2]))
            img = np.loadtxt(f, delimiter=',')
        n = int(meta['n']); xc, yc, w = float(meta['xc']), float(meta['yc']), float(meta['w'])
        xs = np.array([float(r['x']) for r in rows]); ys = np.array([float(r['y']) for r in rows]); tr = np.array([float(r['trav']) for r in rows])
        u = np.clip(((ys - (yc - w / 2)) / w * n).astype(int), 0, n - 1)   # column from y
        v = np.clip((((xc + w / 2) - xs) / w * n).astype(int), 0, n - 1)   # row from x
        variants = {
            'row=x-down,col=y-right (assumed)': (v, u), 'row=x-up,col=y-right': (n - 1 - v, u), 'row=x-down,col=y-left': (v, n - 1 - u),
            'row=x-up,col=y-left': (n - 1 - v, n - 1 - u), 'transposed': (u, v), 'transposed,flip-r': (n - 1 - u, v),
            'transposed,flip-c': (u, n - 1 - v), 'transposed,flip-rc': (n - 1 - u, n - 1 - v)}
        for name, (r_, c_) in variants.items():
            vis = img[r_, c_]
            ok = (vis > -9000) & (tr > -999)
            med = float(np.median(np.abs(tr[ok] - vis[ok]))) if ok.any() else 1e9
            if best is None or med < best[1]: best = (name, med, vis)
        P(f'  orientation check over 8 variants: best "{best[0]}" (median |trav - vis| {best[1]:.2f} m)')
    for col, label in (('vis_solid', 'visual surface without the name-excluded signs / screens / props / foliage'), ('vis_all', 'visual surface incl. every visible primitive')):
        good = above = n = 0; worst = []
        offs = []
        for i, r in enumerate(rows):
            t = fl(r, 'trav'); vv = fl(r, col)
            if col == 'vis_solid' and best is not None: vv = float(best[2][i])
            if t < -999 or vv < -9000: continue
            n += 1
            d = t - vv
            if abs(d) <= 1.0: good += 1
            if d > 1.0: above += 1; worst.append((d, r['x'], r['y'], t, vv, r['src']))
            if int(r['src']) in (1, 2) and abs(d) < 5: offs.append(d)
        worst.sort(reverse=True)
        offs.sort()
        P(f'  {label}: {n} cells, |floor - visual| <= 1 m on {good / max(n, 1) * 100:.2f} % (target >= 99.5 %), floor > visual + 1 m on {above} cells (target 0)'
          + (f'; ground-cell median offset {offs[len(offs) // 2]:+.2f} m' if offs else ''))
        for d, x, y, t, vv, src in worst[:8]:
            P(f'     ({x}, {y}): floor {t:.1f} (src {src}) visual {vv:.1f}  (+{d:.1f} m)')
else:
    P('  no depth audit csv (', DEPTH, ')')

# ------------------------------------------------------------------ per clip
LUMA = {}
def luma(mp4):
    if mp4 in LUMA: return LUMA[mp4]
    out = subprocess.run(['ffprobe', '-v', 'error', '-f', 'lavfi', '-i', f'movie={mp4},signalstats', '-show_entries', 'frame_tags=lavfi.signalstats.YAVG', '-of', 'csv=p=0'],
                         capture_output=True, text=True).stdout.split()
    LUMA[mp4] = [float(x.strip(',')) for x in out if x.strip(',').strip()]
    return LUMA[mp4]

CLIPS = sorted(glob.glob(os.path.join(RD, '*_telemetry.csv')))
P('\n== C  camera: hero_occl >= 0.5, camera in geometry (sphere 0.15) / enclosed (rays), mean frame luma < 25 with the hero on screen (y range = 8 bit)')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    occ = [fl(rows[min(i + 1, len(rows) - 1)], 'hero_occl') for i in range(len(rows))]
    on = [shifted(rows, 'px_top', i) >= 0 for i in range(len(rows))]
    n_occ = sum(1 for o in occ if o >= 0.5)
    n_geo = sum(1 for r in rows if fl(r, 'cam_in_geometry') > 0)
    n_enc = sum(1 for r in rows if fl(r, 'cam_enclosed', 0) > 0)
    mp4 = os.path.join(RD, name + '.mp4')
    dark = '-'
    if os.path.exists(mp4):
        L = luma(mp4)
        k = min(len(L), len(rows))
        d = [i for i in range(k) if on[i] and L[i] < 25]
        dark = f'{len(d)} dark frames (min luma {min(L[:k]) if k else -1:.1f}, mean {sum(L[:k]) / max(k, 1):.1f})' + (f' first at {fl(rows[d[0]], "t"):.2f} s' if d else '')
    worst = max(occ) if occ else -1
    vis_low = sum(1 for r in rows if fl(r, 'vis_pts', 4) < 3)
    P(f'  {name}: {len(rows)} frames | hero_occl >= .5: {n_occ} (max {worst:.2f}) | cam in geometry {n_geo}, enclosed {n_enc} | probe points < 3 visible {vis_low} | luma: {dark}')

P('\n== Y  street-axis hold (f1 / f4: hero y within +-6 m of the y -560 street axis while swinging)')
for nm in ('f1_flow_backDouble', 'f4_chain_flips', 'f5_canyon_backDouble', 'a_swing_chain'):
    p = os.path.join(RD, nm + '_telemetry.csv')
    if not os.path.exists(p): continue
    rows = load(p)
    ys = [fl(r, 'y_m') for r in rows]; xs = [fl(r, 'x_m') for r in rows]
    P(f'  {nm}: y {min(ys):.1f} .. {max(ys):.1f}, x {min(xs):.1f} .. {max(xs):.1f}' + (f' -> {"PASS" if min(ys) >= -566 and max(ys) <= -554 else "FAIL"} (f1/f4 axis y -560)' if nm[:2] in ('f1', 'f4') else ''))

P('\n== K  perch camera: hero_occl <= 0.3 within 0.3 s of the perch landing')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    for i in range(1, len(rows)):
        if rows[i]['mode'] == 'perch' and rows[i - 1]['mode'] != 'perch':
            t0 = fl(rows[i], 't')
            win = [(fl(rows[j], 't'), fl(rows[min(j + 1, len(rows) - 1)], 'hero_occl')) for j in range(i, len(rows)) if fl(rows[j], 't') <= t0 + 1.5]
            ok_t = next((t for t, o in win if 0 <= o <= 0.3), None)
            late = [o for t, o in win if t >= t0 + 0.3]
            P(f'  {name}: perch at {t0:.2f} s; occl <= .3 first at {"%.2f" % ok_t if ok_t is not None else "never"} s; max occl after +0.3 s {max(late) if late else -1:.2f} -> '
              + ('PASS' if ok_t is not None and ok_t <= t0 + 0.3 and (not late or max(late) <= 0.3) else 'FAIL'))

P('\n== W  wall run: top-outs / setbacks, posture (vertical: body within 15 deg of the wall up axis; side: body within 20 deg of the run direction),'
  ' silhouette w/h <= .55 (rendered mask), knee gap <= .35 m, alternate contacts every <= .18 s')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    wr = [i for i, r in enumerate(rows) if r['mode'] == 'wall' and r['sub'] in ('wallRun', 'wallRunSide')]
    tops = int(fl(rows[-1], 'topouts', 0)) if rows else 0
    sets = int(fl(rows[-1], 'setbacks', 0)) if rows else 0
    if not wr and not tops: continue
    vert = [i for i in wr if rows[i]['sub'] == 'wallRun']; side = [i for i in wr if rows[i]['sub'] == 'wallRunSide']
    def share(ix, k, lim):
        v = [shifted(rows, k, i) for i in ix]; v = [x for x in v if x >= 0]
        return (sum(1 for x in v if x <= lim) / len(v) * 100, sorted(v)[len(v) // 2], max(v)) if v else (float('nan'),) * 3
    bv = share(vert, 'body_wallup_deg', 15); bs = share(side, 'body_vel_deg', 20)
    wh = []; whs_side = []
    for i in wr:
        t_, b_, l_, r_ = (shifted(rows, k, i) for k in ('px_top', 'px_bottom', 'px_left', 'px_right'))
        if t_ >= 0 and b_ > t_:
            # r20: a vertical run is judged by w/h; a side run's body lies along the run (horizontal on screen), so its silhouette is judged
            # by the thin side over the long side (min / max)
            if rows[i]['sub'] == 'wallRun': wh.append((r_ - l_) / (b_ - t_))
            elif r_ > l_: whs_side.append(min(r_ - l_, b_ - t_) / max(r_ - l_, b_ - t_))
    kg = [shifted(rows, 'tuck_knee_gap_m', i) for i in wr]
    # contacts: a limb is on the wall when its toe / palm is <= 0.08 m off the facade; longest time between two contact changes
    ch = []; last = None; lastt = None; previ = None
    for i in wr:
        st = tuple(shifted(rows, k, i) <= 0.08 for k in ('foot_wall_l', 'foot_wall_r', 'hand_wall_l', 'hand_wall_r'))
        t = fl(rows[i], 't')
        if previ is not None and i != previ + 1: last = None; lastt = None   # r20: a new wall-run segment (setback mantle / corner) restarts the clock
        previ = i
        if last is not None and st != last:
            if lastt is not None: ch.append(t - lastt)
            lastt = t
        if lastt is None: lastt = t
        last = st
    whs = sorted(wh)
    P(f'  {name}: top-outs {tops}, setbacks mantled {sets} | vertical rows {len(vert)}: body-to-wall-up <= 15 deg {bv[0]:.0f} % (med {bv[1]:.1f}, max {bv[2]:.1f})'
      f' | side rows {len(side)}: body-to-run <= 20 deg {bs[0]:.0f} % (med {bs[1]:.1f}) | vertical w/h med {whs[len(whs) // 2] if whs else float("nan"):.2f} p90 {whs[int(len(whs) * .9)] if whs else float("nan"):.2f}'
      f' | side thin/long med {sorted(whs_side)[len(whs_side) // 2] if whs_side else float("nan"):.2f}'
      f' | knee gap med {sorted(kg)[len(kg) // 2] if kg else float("nan"):.2f} max {max(kg) if kg else float("nan"):.2f} m | longest contact hold {max(ch) if ch else float("nan"):.2f} s')

P('\n== Z  E presses -> where he ends (0.4 s later and at the end of the zip)')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    for i in range(1, len(rows)):
        if fl(rows[i], 'in_zip') > 0 and fl(rows[i - 1], 'in_zip') <= 0:
            t0 = fl(rows[i], 't')
            seq = []; end = None
            for j in range(i, len(rows)):
                m = rows[j]['mode'] + '/' + rows[j]['sub']
                if not seq or seq[-1] != m: seq.append(m)
                if fl(rows[j], 't') > t0 + 4: break
                if rows[j]['mode'] in ('perch', 'ground') and j > i + 3: end = (fl(rows[j], 't'), rows[j]['mode'], fl(rows[j], 'z_m')); break
            why = rows[min(i + 2, len(rows) - 1)].get('zip_why', '')
            P(f'  {name}: t {t0:.2f} from {rows[i - 1]["mode"]}/{rows[i - 1]["sub"]} why={why}: {" > ".join(seq[:6])}' + (f' -> {end[1]} at {end[0]:.2f} s, z {end[2]:.1f}' if end else ' -> no perch / roof within 4 s'))

P('\n== A  air at speed: body axis (hips -> head) within 30 deg of the velocity when speed >= 30 m/s in air (not trick / launch subs)')
SKIP = {'trick', 'topOut', 'zipPull', 'jumpLaunch', 'wallJump', 'pointLaunch', 'vault'}
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    ix = [i for i, r in enumerate(rows) if r['mode'] == 'air' and r['sub'] not in SKIP and fl(r, 'speed_mps') >= 30]
    if not ix: continue
    v = [shifted(rows, 'body_vel_deg', i) for i in ix]
    ok = sum(1 for x in v if 0 <= x <= 30)
    bad = [fl(rows[i], 't') for i, x in zip(ix, v) if x > 30]
    P(f'  {name}: {len(ix)} rows >= 30 m/s in air, within 30 deg {ok / len(ix) * 100:.0f} % (median {sorted(v)[len(v) // 2]:.1f} deg)' + (f'; first misses at {", ".join("%.2f" % t for t in bad[:5])} s' if bad else ''))
for nm, ts in (('a_swing_chain', (4.25, 10.25)),):
    p = os.path.join(RD, nm + '_telemetry.csv')
    if not os.path.exists(p): continue
    rows = load(p)
    for tt in ts:
        i = min(range(len(rows)), key=lambda k: abs(fl(rows[k], 't') - tt))
        P(f'  {nm} @ {tt} s: {rows[i]["mode"]}/{rows[i]["sub"]} speed {fl(rows[i], "speed_mps"):.1f} m/s, body-to-velocity {shifted(rows, "body_vel_deg", i):.1f} deg')

P('\n== R  zip flight reach (w1 3.8-4.4 s): zip_reach_w and hand height over the hips')
for nm in ('w1_wallrun_tall_zip', 'c_wallrun_perch', 'r1_roofrun_zip', 'w2_wallrun_side_zip'):
    p = os.path.join(RD, nm + '_telemetry.csv')
    if not os.path.exists(p): continue
    rows = load(p)
    zr = [(fl(r, 't'), shifted(rows, 'zip_reach_w', i), rows[min(i + 1, len(rows) - 1)]['limb_z']) for i, r in enumerate(rows) if r['sub'] == 'zipFlight']
    if zr:
        full = sum(1 for _, w_, _ in zr if w_ >= 0.9)
        P(f'  {nm}: zipFlight {zr[0][0]:.2f}-{zr[-1][0]:.2f} s, reach weight >= .9 on {full}/{len(zr)} rows; limb_z (hands L R, feet L R over the hips, m) mid-flight: {zr[len(zr) // 2][2]}')

P('\n== X  RMB response (owner bug 1): every fresh RMB press during a trick / top-out flip / wall run -> time to the swing (target <= 0.1 s)')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    for i in range(1, len(rows)):
        if fl(rows[i], 'in_swing') > 0 and fl(rows[i - 1], 'in_swing') <= 0:
            m0 = rows[i - 1]['mode'] + '/' + rows[i - 1]['sub']
            busy = rows[i - 1]['mode'] == 'wall' or rows[i - 1]['sub'] in ('trick', 'topOut')
            t0 = fl(rows[i], 't')
            ts = next((fl(rows[j], 't') for j in range(i, len(rows)) if rows[j]['mode'] == 'swing'), None)
            dt = (ts - t0) if ts is not None else None
            P(f'  {name}: press at {t0:.2f} s from {m0}' + (f' -> swing at {ts:.2f} s (+{dt:.2f} s)' if dt is not None else ' -> no swing') +
              (' -> ' + ('PASS' if dt is not None and dt <= 0.1 + 1e-6 else 'FAIL') if busy else ' (not busy: info)'))

P('\n== S  air pose by speed (air rows, not trick / launch subs): hands / feet height over the hips (limb_z, m), body-to-velocity, procedural weights')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    bins = {}
    for i, r in enumerate(rows):
        if r['mode'] != 'air' or r['sub'] in SKIP: continue
        sp = fl(r, 'speed_mps'); b = '<20' if sp < 20 else '20-30' if sp < 30 else '30-44' if sp < 44 else '>=44'
        lz = rows[min(i + 1, len(rows) - 1)]['limb_z'].split()
        if len(lz) != 4: continue
        bins.setdefault(b, []).append(([float(x) for x in lz], shifted(rows, 'body_vel_deg', i), shifted(rows, 'air_fast_w', i), shifted(rows, 'air_track_k', i), r['anim_node']))
    for b in ('<20', '20-30', '30-44', '>=44'):
        v = bins.get(b)
        if not v: continue
        med = lambda a: sorted(a)[len(a) // 2]
        hands = med([(x[0][0] + x[0][1]) / 2 for x in v]); feet = med([(x[0][2] + x[0][3]) / 2 for x in v])
        P(f'  {name} {b:>6} m/s: {len(v):4d} rows | hands {hands:+.2f} m, feet {feet:+.2f} m over the hips | body-to-velocity med {med([x[1] for x in v]):.0f} deg'
          f' | air_fast_w med {med([x[2] for x in v]):.2f}, track_k med {med([x[3] for x in v]):.2f} | upright fallCalm rows (node air_fallCalm, body-to-vel > 60): '
          f'{sum(1 for x in v if x[4] == "air_fallCalm" and x[1] > 60)}')

P('\n== I  mouse look injection (-WHTravInputTest=mouseLook)')
lg = os.path.join(RD, 'inputtest_mouselook.log')
if os.path.exists(lg):
    for line in open(lg):
        if 'mouseLook' in line: P('  ' + line.strip())
mt = glob.glob(os.path.join(RD, 'probes', 'mouselook_telemetry.csv')) + glob.glob(os.path.join(RD, 'mouselook_telemetry.csv'))
if mt:
    rows = load(mt[0])
    lp = [fl(r, 'look_px') for r in rows]
    yw = [fl(r, 'cam_yaw_deg') for r in rows]
    P(f'  telemetry: look_px > 0 on {sum(1 for x in lp if x > 0)} frames (sum {sum(lp):.0f} px), camera yaw {yw[0]:.1f} -> {yw[-1]:.1f} deg')

P('\n== L  landings: where each air -> ground / land happened, floor source, frame luma')
for p in CLIPS:
    name = os.path.basename(p)[:-len('_telemetry.csv')]
    rows = load(p)
    mp4 = os.path.join(RD, name + '.mp4')
    L = luma(mp4) if os.path.exists(mp4) else []
    for i in range(1, len(rows)):
        if rows[i - 1]['mode'] == 'air' and rows[i]['mode'] in ('ground', 'land'):
            P(f'  {name}: landing at {fl(rows[i], "t"):.2f} s ({rows[i]["sub"]}) z {fl(rows[i], "z_m"):.1f}, over floor {fl(rows[i], "height_above_floor_m"):.2f} m, floor src {rows[i]["ground_src"]}, frame luma {L[i] if i < len(L) else -1:.1f}')

with open(os.path.join(RD, 'R20_CHECK.txt'), 'w') as f:
    f.write('\n'.join(OUT) + '\n')
