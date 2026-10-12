#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 22 checker (director r22 target after critic r21 "the side run is a slither"):
#   U22  upright side run (w1 + w2 wallRunSide, steady rows): torso (hips -> head) within 30 deg of the wall's up axis, >= 60 deg above the
#        run line, chest along the run line; stride: a foot touches down every <= 0.18 s, along-run ankle separation peak >= 0.6 m and
#        >= 0.3 m for >= 70 % of the run
#   B22  rendered hero box (hero mask, px_*) height >= width in >= 80 % of the w1 + w2 side-run frames
#   L22  facade luma: mean BT.709 luma (0-255) of the facade ring around the hero box (box grown by its own size, hero box excluded)
#        >= 45 on every 12 fps side-run frame; mullion check: hero_occl (rendered depth occlusion of the hero) max, hero_vis_px min
#   F22  frame test: w2 3.1-3.85 s at 12 fps (10 frames): legs apart (along-run ankle sep >= 0.3 m) in >= 7 of 10, plus a sheet
#   C22  c vertical run kept: limbs (hands / toes) <= 0.3 m off the surface, touchdown gap, >= 82 % within 15 deg of wall-up (r21 numbers)
#   I22  flips untouched: f1 / f4 telemetry vs round 21, every common column, cell by cell
#   G22  ground blend (characters critic): r1 roof run, longest single-frame dominant-weight jump on ground rows
# usage: r22_checks.py <round dir> [--sheets <dir>] [--prev <round-21 dir>]
import csv, glob, os, subprocess, sys
import numpy as np
RD = sys.argv[1]
ARGS = sys.argv[2:]
SHEETS = ARGS[ARGS.index('--sheets') + 1] if '--sheets' in ARGS else None
PREV = ARGS[ARGS.index('--prev') + 1] if '--prev' in ARGS else os.path.join(os.path.dirname(os.path.abspath(RD)), 'round-21')
OUT = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)
def load(p):
    with open(p) as f: return list(csv.DictReader(f))
def fl(r, k, d=float('nan')):
    try: return float(r.get(k, ''))
    except (TypeError, ValueError): return d
def sh(rows, k, i): return fl(rows[min(i + 1, len(rows) - 1)], k)   # pose / pixel columns are sampled one row late
def med(v): v = sorted(v); return v[len(v) // 2] if v else float('nan')
def mx(v): return max(v) if v else float('nan')
def mn(v): return min(v) if v else float('nan')
def pct(n, d): return 100.0 * n / max(d, 1)
def at(rows, t): return min(range(len(rows)), key=lambda k: abs(fl(rows[k], 't') - t))
def clip(name):
    p = os.path.join(RD, name + '_telemetry.csv')
    return load(p) if os.path.exists(p) else None
def side_rows(rows):
    ix = [i for i, r in enumerate(rows) if r['mode'] == 'wall' and r['sub'] == 'wallRunSide']
    segs, cur = [], []
    for i in ix:
        if cur and i != cur[-1] + 1: segs.append(cur); cur = []
        cur.append(i)
    if cur: segs.append(cur)
    return [i for s in segs for i in s if fl(rows[i], 't') >= fl(rows[s[0]], 't') + 0.1], ix

def frames(mp4, t0, t1, fps, scale=960):
    """decode [t0, t1) at fps -> list of HxWx3 uint8 (scaled to `scale` wide)"""
    h = scale * 1080 // 1920
    cmd = ['ffmpeg', '-loglevel', 'error', '-ss', f'{t0:.4f}', '-t', f'{t1 - t0:.4f}', '-i', mp4, '-vf', f'fps={fps},scale={scale}:{h}',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (scale * h * 3)
    return [np.frombuffer(raw[k * scale * h * 3:(k + 1) * scale * h * 3], np.uint8).reshape(h, scale, 3) for k in range(n)]

P('== U22  upright side run (steady rows >= 0.1 s into each wallRunSide segment)')
P('         target: torso <= 30 deg off wall-up, >= 60 deg above the run line, chest along the run line; touchdown every <= .18 s;')
P('         along-run ankle separation peak >= .6 m and >= .3 m for >= 70 % of the run')
side_all = {}
for name in ('w1_wallrun_tall_zip', 'w2_wallrun_side_zip', 'x2_rmb_cancel_wall'):
    rows = clip(name)
    if not rows: continue
    ix, raw = side_rows(rows)
    side_all[name] = (rows, raw)
    if not ix: P(f'  {name}: no steady side-run rows (side rows {len(raw)})'); continue
    tw = [sh(rows, 'torso_wallup_deg', i) for i in ix]; tw = [x for x in tw if x >= 0]
    el = [sh(rows, 'body_run_elev_deg', i) for i in ix]; el = [x for x in el if x > -900]
    ch = [sh(rows, 'chest_run_deg', i) for i in ix]; ch = [x for x in ch if x >= 0]
    sep = [sh(rows, 'foot_sep_run_m', i) for i in ix]
    sp = [sh(rows, 'ankle_sep_plane_m', i) for i in ix]
    tds = []
    for s in ('l', 'r'):
        prev = None
        for i in ix:
            on = sh(rows, 'foot_wall_' + s, i) <= 0.08
            if prev is False and on: tds.append(fl(rows[i], 't'))
            prev = on
    tds.sort(); gaps = [b - a for a, b in zip(tds, tds[1:]) if b - a < 0.6]
    t0, t1 = fl(rows[raw[0]], 't'), fl(rows[raw[-1]], 't')
    P(f'  {name}: side run {t0:.2f}-{t1:.2f} s ({len(ix)} steady rows) | torso-to-wall-up <= 30 deg {pct(sum(x <= 30 for x in tw), len(tw)):.0f} % '
      f'(med {med(tw):.1f}, max {mx(tw):.1f}) | above run line >= 60 deg {pct(sum(x >= 60 for x in el), len(el)):.0f} % (med {med(el):.1f}, min {mn(el):.1f})'
      f' | chest-to-run line med {med(ch):.1f} deg (max {max(ch) if ch else float("nan"):.1f})')
    P(f'      stride: along-run ankle sep peak {mx(sep):.2f} m, >= .3 m {pct(sum(x >= 0.3 for x in sep), len(sep)):.0f} % (med {med(sep):.2f}) | '
      f'in-plane ankle sep >= .3 m {pct(sum(x >= 0.3 for x in sp), len(sp)):.0f} % | touchdowns {len(tds)}, longest gap '
      f'{max(gaps) if gaps else float("nan"):.3f} s (med {med(gaps):.3f})')

P('\n== B22  rendered hero box (hero mask px_*, one row late) height >= width in >= 80 % of the w1 + w2 side-run frames (all side rows)')
tot = okc = 0
for name in ('w1_wallrun_tall_zip', 'w2_wallrun_side_zip'):
    if name not in side_all: continue
    rows, raw = side_all[name]
    hw = []
    for i in raw:
        t, b, l, r = sh(rows, 'px_top', i), sh(rows, 'px_bottom', i), sh(rows, 'px_left', i), sh(rows, 'px_right', i)
        if min(t, b, l, r) < 0 or b <= t: continue
        hw.append((b - t, r - l))
    n_ok = sum(1 for h, w in hw if h >= w)
    tot += len(hw); okc += n_ok
    P(f'  {name}: {n_ok}/{len(hw)} frames tall ({pct(n_ok, len(hw)):.0f} %), h/w med {med([h / max(w, 1) for h, w in hw]):.2f}')
P(f'  w1 + w2: {okc}/{tot} = {pct(okc, tot):.0f} % -> ' + ('PASS' if tot and okc >= 0.8 * tot else 'FAIL'))

P('\n== L22  facade luma around the hero on side-run frames (12 fps; ring = hero box grown by its size, box excluded) >= 45; mullions')
for name in ('w1_wallrun_tall_zip', 'w2_wallrun_side_zip'):
    if name not in side_all: continue
    rows, raw = side_all[name]
    mp4 = os.path.join(RD, name + '.mp4')
    if not raw or not os.path.exists(mp4): continue
    t0, t1 = fl(rows[raw[0]], 't'), fl(rows[raw[-1]], 't') + 1 / 60
    fr = frames(mp4, t0, t1, 12)
    lum = []
    for k, img in enumerate(fr):
        i = at(rows, t0 + k / 12)
        t, b, l, r = [sh(rows, c, i) / 2 for c in ('px_top', 'px_bottom', 'px_left', 'px_right')]   # 960-wide decode
        if min(t, b, l, r) < 0: continue
        H, W = img.shape[:2]; bh, bw = b - t, r - l
        y0, y1, x0, x1 = int(max(0, t - bh)), int(min(H, b + bh)), int(max(0, l - bw)), int(min(W, r + bw))
        Y = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
        m = np.zeros((H, W), bool); m[y0:y1, x0:x1] = True; m[int(t):int(b), int(l):int(r)] = False
        lum.append(float(Y[m].mean()))
    occ = [sh(rows, 'hero_occl', i) for i in raw]; vis = [sh(rows, 'hero_vis_px', i) for i in raw]
    P(f'  {name}: {len(lum)} frames, facade luma min {min(lum) if lum else float("nan"):.1f} med {med(lum):.1f} max {max(lum) if lum else float("nan"):.1f}'
      f' -> {"PASS" if lum and min(lum) >= 45 else "FAIL"} ({sum(x >= 45 for x in lum)}/{len(lum)} >= 45) | hero_occl max {mx(occ):.3f}'
      f' (frames > .10: {sum(x > 0.10 for x in occ)}) | hero visible px min {mn(vis):.0f}')

P('\n== F22  w2 3.1-3.85 s at 12 fps: legs apart (along-run ankle sep >= .3 m) in >= 7 of 10 frames')
rows = clip('w2_wallrun_side_zip')
if rows:
    v = []
    for k in range(10):
        t = 3.1 + k / 12; i = at(rows, t)
        v.append((t, rows[i]['sub'], sh(rows, 'foot_sep_run_m', i), sh(rows, 'ankle_sep_plane_m', i)))
    ok = sum(1 for _, s, x, _p in v if s == 'wallRunSide' and x >= 0.3)
    P('  ' + ', '.join(f'{t:.3f}:{s}:{x:.2f}/{p:.2f}' for t, s, x, p in v) + f'  (along-run / in-plane m) -> {ok}/10 apart -> ' + ('PASS' if ok >= 7 else 'FAIL'))
    mp4 = os.path.join(RD, 'w2_wallrun_side_zip.mp4')
    if SHEETS and os.path.exists(mp4):
        os.makedirs(SHEETS, exist_ok=True)
        out = os.path.join(SHEETS, 'w2_wallrun_side_zip_3.1-3.9_12fps.png')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '3.1', '-t', f'{10 / 12:.4f}', '-i', mp4, '-vf',
                        'fps=12,crop=iw/2:ih*0.75:iw/4:ih/8,scale=400:-1,tile=5x2', '-frames:v', '1', out])
        P(f'     sheet {out}')
    for nm, a, b in (('w1_wallrun_tall_zip', None, None),):
        r1 = clip(nm)
        mp4 = os.path.join(RD, nm + '.mp4')
        if SHEETS and r1 and os.path.exists(mp4):
            _, raw = side_rows(r1)
            if raw:
                t0 = fl(r1[raw[0]], 't'); n = min(10, max(1, int((fl(r1[raw[-1]], 't') - t0) * 12)))
                out = os.path.join(SHEETS, f'{nm}_side_12fps.png')
                subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{t0:.3f}', '-t', f'{n / 12:.4f}', '-i', mp4, '-vf',
                                'fps=12,crop=iw/2:ih*0.75:iw/4:ih/8,scale=400:-1,tile=5x2', '-frames:v', '1', out])
                P(f'     sheet {out} ({t0:.2f} s, {n} frames)')

P('\n== C22  c vertical run kept (r21: limbs <= .30 m, touchdown gap med .150 / longest .383 across the setback, 82 % within 15 deg of wall-up)')
for d, tag in ((RD, 'r22'), (PREV, 'r21')):
    p = os.path.join(d, 'c_wallrun_perch_telemetry.csv')
    if not os.path.exists(p): continue
    rows = load(p)
    ix = [i for i, r in enumerate(rows) if r['mode'] == 'wall' and r['sub'] == 'wallRun']
    ix = [i for i in ix if fl(rows[i], 't') >= fl(rows[ix[0]], 't') + 0.1] if ix else []
    if not ix: continue
    lim = [sh(rows, 'limb_wall_max_m', i) for i in ix]
    bw = [x for x in (sh(rows, 'body_wallup_deg', i) for i in ix) if x >= 0]
    tds = []
    for s in ('l', 'r'):
        prev = None
        for i in ix:
            on = sh(rows, 'foot_wall_' + s, i) <= 0.08
            if prev is False and on: tds.append(fl(rows[i], 't'))
            prev = on
    tds.sort(); gaps = [b - a for a, b in zip(tds, tds[1:]) if b - a < 0.6]
    P(f'  {tag} c wallRun: {len(ix)} rows | limbs off the surface max {max(lim):.2f} m (p90 {sorted(lim)[int(len(lim) * .9)]:.2f}) | touchdowns {len(tds)},'
      f' gap med {med(gaps):.3f} longest {max(gaps) if gaps else float("nan"):.3f} s | within 15 deg of wall-up {pct(sum(x <= 15 for x in bw), len(bw)):.0f} %')

P('\n== I22  flip clips vs round 21 (every common column, cell by cell)')
for name in ('f1_flow_backDouble', 'f4_chain_flips', 'c_wallrun_perch', 'a_swing_chain'):
    a, b = os.path.join(PREV, name + '_telemetry.csv'), os.path.join(RD, name + '_telemetry.csv')
    if not (os.path.exists(a) and os.path.exists(b)): continue
    A, B = load(a), load(b)
    cols = [c for c in A[0].keys() if c in B[0]]
    diff = {}
    for ra, rb in zip(A, B):
        for c in cols:
            if ra[c] != rb[c]: diff[c] = diff.get(c, 0) + 1
    P(f'  {name}: rows r21 {len(A)} / r22 {len(B)}, {len(cols)} common columns, differing cells {sum(diff.values())}'
      + (f' in {sorted(diff.items(), key=lambda x: -x[1])[:8]}' if diff else ' -> BIT-IDENTICAL'))

P('\n== G22  ground locomotion blend (characters critic: idle -> run was a 1-frame weight pop). anim_weight is the TOTAL clip weight (always 1),')
P('         so the check is the largest single-frame pose_sig jump on ground rows (r1 roof run), r21 vs r22; no shot-list clip has a standing start')
for d, tag in ((PREV, 'r21'), (RD, 'r22')):
    p = os.path.join(d, 'r1_roofrun_zip_telemetry.csv')
    if not os.path.exists(p): continue
    rows = load(p)
    def ps(i):
        try: return [float(x) for x in rows[i]['pose_sig'].split()]
        except (ValueError, KeyError): return None
    js = []
    for i, r in enumerate(rows[:-2]):
        if r['mode'] != 'ground': continue
        a, b = ps(i + 1), ps(i + 2)
        if a and b: js.append((max(abs(x - y) for x, y in zip(a, b)), r['t'], r['sub']))
    js.sort(reverse=True)
    P(f'  {tag} r1: {len(js)} ground rows, largest pose_sig jumps ' + ', '.join(f'{x:.3f} at {t} s ({s})' for x, t, s in js[:3]))

with open(os.path.join(RD, 'R22_CHECK.txt'), 'w') as f: f.write('\n'.join(OUT) + '\n')
