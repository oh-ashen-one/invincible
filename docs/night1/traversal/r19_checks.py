#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P3 round 19 checks (owner playtest 2026-10-01 + critic r18), from round telemetry CSVs and run logs.

usage: python3 r19_checks.py <round dir>            -> prints a report (also written to <round dir>/R19_CHECK.txt)
  W  wall-run IK stride   (w1 / w2 / c / r1): contact share of feet / hands on the facade, cadence, contralateral phase, head above hips
  Z  E from every mode     (w1 / w2 / r1 / c / b): each zip press -> what happened within 0.4 s (zip / perch / wallZip / dash), never "none"
  V  per-trick variation   (f*, a, b): same-type programs in a clip differ by >= 40 deg/s in at least one 0.1 s rate sample
  T  tight tuck            (f1 / f5 + any backDouble): wrists <= 0.15 m from the shins and knees <= 0.25 m apart, held >= 0.25 s per tuck
  I  live-input repro      (inputtest_*.log): presses -> swings, polled (r19) vs event-latched (r18)
  F  floor audit           (floor_on.csv / floor_off.csv): traversal floor with the solid filter on vs off
"""
import csv, glob, os, re, sys, math
from collections import defaultdict

R = sys.argv[1]
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); out.append(s); print(s)

def rows(path):
    import gzip
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        with gzip.open(path + '.gz', 'rt') as f: return list(csv.DictReader(f))
    with open(path) as f:
        return list(csv.DictReader(f))
def fl(r, k, d=float('nan')):
    try: return float(r.get(k, ''))
    except Exception: return d

clips = {os.path.basename(p)[:-len('_telemetry.csv')]: p for p in sorted(glob.glob(os.path.join(R, '*_telemetry.csv')))}

# ---------------- W: wall-run stride
P('== W  wall-run stride (rows in wall mode, sub wallRun / wallRunSide, IK weight >= 0.9)')
for name, p in clips.items():
    rs = rows(p)
    if 'wall_ik_w' not in rs[0]: continue
    W = [r for r in rs if r['mode'] == 'wall' and r['sub'] in ('wallRun', 'wallRunSide') and fl(r, 'wall_ik_w', 0) >= 0.9]
    if len(W) < 10: continue
    n = len(W)
    def share(col, lim): return sum(1 for r in W if 0 <= fl(r, col, 9) <= lim) / n
    fl_ = share('foot_wall_l', 0.15); fr_ = share('foot_wall_r', 0.15); hl = share('hand_wall_l', 0.15); hr = share('hand_wall_r', 0.15)
    # any-limb contact every frame + contralateral: left foot and right hand contact together
    both = sum(1 for r in W if (0 <= fl(r, 'foot_wall_l', 9) <= 0.15) and (0 <= fl(r, 'hand_wall_r', 9) <= 0.15)) / n
    anyc = sum(1 for r in W if min(fl(r, c, 9) for c in ('foot_wall_l', 'foot_wall_r', 'hand_wall_l', 'hand_wall_r')) <= 0.15) / n
    far = max(max(fl(r, c, 0) for c in ('foot_wall_l', 'foot_wall_r', 'hand_wall_l', 'hand_wall_r')) for r in W)
    # cadence: gait phase wraps
    dur = fl(W[-1], 't') - fl(W[0], 't')
    adv = 0.0; tt = 0.0
    for a_, b_ in zip(W, W[1:]):
        dt_ = fl(b_, 't') - fl(a_, 't')
        if 0 < dt_ < 0.05:
            d_ = (fl(b_, 'gait_ph', 0) - fl(a_, 'gait_ph', 0)) % 1.0; adv += d_; tt += dt_
    wraps = adv; dur = tt
    hh = [fl(r, 'head_hip_dz', 0) for r in W if r['sub'] == 'wallRun']
    spd = sum(fl(r, 'speed_mps', 0) for r in W) / n
    P(f'{name}: {n} rows {dur:.2f} s, speed {spd:.1f} m/s | contact share feet L {fl_:.2f} R {fr_:.2f}, hands L {hl:.2f} R {hr:.2f}; '
      f'>= 1 limb on the wall {anyc:.2f}; L-foot+R-hand together {both:.2f}; farthest limb {far:.2f} m | '
      f'cycles {wraps:.1f} -> {2 * wraps / max(dur, 1e-3):.1f} steps/s | head above hips (vertical rows) {sum(1 for v in hh if v > 0.3)}/{len(hh)}')

# ---------------- Z: E from every mode
P('\n== Z  zip presses (in_zip rising edge) -> mode 0.4 s later, zip_why')
for name, p in clips.items():
    rs = rows(p)
    prev = '0'
    for i, r in enumerate(rs):
        z = r.get('in_zip', '0')
        if z == '1' and prev != '1':
            t0 = fl(r, 't'); m0 = f"{r['mode']}/{r['sub']}"
            later = [x for x in rs[i:] if fl(x, 't') <= t0 + 0.4]
            modes = []
            for x in later:
                mm = f"{x['mode']}/{x['sub']}"
                if not modes or modes[-1] != mm: modes.append(mm)
            why = later[-1].get('zip_why', '?') if later else '?'
            ok = any(m.startswith(('zip', 'perch')) or 'wallZip' in m or 'zipPull' in m or 'pointLaunch' in m for m in modes[1:] + [modes[0]]) and why not in ('none', 'None')
            P(f'{name}: t {t0:.2f} from {m0} -> {" > ".join(modes[:5])}  why={why}  {"PASS" if ok else "FAIL"}')
        prev = z

# ---------------- V: per-trick variation (critic r18 test)
P('\n== V  same-type tricks differ by >= 40 deg/s in at least one 0.1 s rate sample')
allprog = defaultdict(list)
for name, p in clips.items():
    rs = rows(p)
    progs = []; cur = None
    for r in rs:
        fp = r.get('flip_prog', ''); ft = fl(r, 'flip_t', -1)
        if fp and ft >= 0:
            if cur is None or cur['name'] != fp or ft < cur['last'] - 0.05:
                cur = {'name': fp, 'samples': {}, 'last': ft, 'scale': fl(r, 'flip_scale', 0), 'clip': name}; progs.append(cur)
            k = int(round(ft / 0.1))
            cur['samples'].setdefault(k, fl(r, 'flip_rate_dps', 0)); cur['last'] = ft
        else: cur = None
    for pr in progs: allprog[pr['name']].append(pr)
    byname = defaultdict(list)
    for pr in progs: byname[pr['name']].append(pr)
    for nm, L in byname.items():
        if len(L) < 2: continue
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                ks = set(L[i]['samples']) & set(L[j]['samples'])
                d = max((abs(L[i]['samples'][k] - L[j]['samples'][k]) for k in ks), default=0)
                P(f'{name}: {nm} #{i+1} (x{L[i]["scale"]:.3f}) vs #{j+1} (x{L[j]["scale"]:.3f}): max |rate diff| {d:.0f} deg/s over {len(ks)} samples -> {"PASS" if d >= 40 else "FAIL"}')
P('across clips (same program type, first instance of each clip):')
for nm, L in allprog.items():
    if len(L) < 2: continue
    sc = sorted(set(round(x['scale'], 3) for x in L))
    durs = sorted(round(max(x['samples']) / 10, 1) for x in L)
    P(f'  {nm}: {len(L)} instances, scales {sc}, sampled spans {durs} s')

# ---------------- T: tight tuck
P('\n== T  tight tuck: wrists <= 0.15 m from the shins and knees <= 0.25 m apart, held >= 0.25 s (rows with flip_shape tuck)')
for name, p in clips.items():
    rs = rows(p)
    if 'tuck_wrist_shin_m' not in rs[0]: continue
    runs = []; cur = None
    for r in rs:
        tuck = r.get('flip_shape', '') == 'Tuck' or r.get('flip_shape', '') == 'tuck'
        if tuck:
            if cur is None: cur = []; runs.append(cur)
            cur.append(r)
        else: cur = None
    for k, run in enumerate(runs):
        if len(run) < 6: continue
        ok = [fl(r, 'tuck_wrist_shin_m', 9) <= 0.15 and fl(r, 'tuck_knee_gap_m', 9) <= 0.25 for r in run]
        best = cur_ = 0
        for o in ok:
            cur_ = cur_ + 1 if o else 0; best = max(best, cur_)
        dt = (fl(run[-1], 't') - fl(run[0], 't')) / max(1, len(run) - 1)
        ws = [fl(r, 'tuck_wrist_shin_m', 9) for r in run]; kg = [fl(r, 'tuck_knee_gap_m', 9) for r in run]
        P(f'{name}: tuck {k+1} at {fl(run[0],"t"):.2f}-{fl(run[-1],"t"):.2f} s ({run[0].get("flip_prog","")}): wrist-shin min {min(ws):.3f} med {sorted(ws)[len(ws)//2]:.3f}, '
          f'knee gap min {min(kg):.3f} med {sorted(kg)[len(kg)//2]:.3f}; longest closed hold {best * dt:.2f} s -> {"PASS" if best * dt >= 0.25 else "FAIL"}')

# ---------------- I: live input repro
P('\n== I  live-input repro (WH_INPUTTEST)')
for lg in sorted(glob.glob(os.path.join(R, 'inputtest_*.log'))):
    res = [l.strip() for l in open(lg, errors='ignore') if 'WH_INPUTTEST' in l and ('RESULT' in l or 'NO SWING' in l or '-> swing' in l)]
    P(os.path.basename(lg) + ':')
    for l in res: P('   ' + re.sub(r'^.*WH_INPUTTEST', 'WH_INPUTTEST', l))

# ---------------- F: floor audit
on, off = os.path.join(R, 'floor_on.csv'), os.path.join(R, 'floor_off.csv')
if (os.path.exists(on) or os.path.exists(on + '.gz')) and (os.path.exists(off) or os.path.exists(off + '.gz')):
    P('\n== F  floor audit (5 m grid, traversal floor = GroundHeight from 600 m): solid filter ON (r19) vs OFF (690dfa7)')
    A = {(r['x'], r['y']): r for r in rows(on)}; B = {(r['x'], r['y']): r for r in rows(off)}
    ks = set(A) & set(B)
    hi = [(k, fl(B[k], 'z') - fl(A[k], 'z')) for k in ks]
    big = [x for x in hi if x[1] > 1.0]
    src = defaultdict(int)
    for k in ks: src[A[k].get('src', '?')] += 1
    P(f'{len(ks)} cells; filter ON sources {dict(src)} (1 ground box, 2 ground mesh, 3 building box, 4 other); '
      f'{len(big)} cells where the OFF floor sits > 1 m above the ON floor (invisible / non-building solids removed), max {max([x[1] for x in hi] or [0]):.1f} m')
    for (k, d) in sorted(big, key=lambda x: -x[1])[:12]:
        P(f'   ({k[0]}, {k[1]}): off {fl(B[k],"z"):.1f} (src {B[k].get("src")}) on {fl(A[k],"z"):.1f} (src {A[k].get("src")})')
open(os.path.join(R, 'R19_CHECK.txt'), 'w').write('\n'.join(out) + '\n')
