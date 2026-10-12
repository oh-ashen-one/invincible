#!/usr/bin/env python3
"""(r10) coordinate search of the S4 far-band lighting INSIDE one gpu_slot hold (every Unreal launch is a nested pass-through of the caller's hold; strictly one engine at a time).
Objective = tools/export/s4_score.py (0 = T1 / T2 / C11-C15 all pass). Parameters:
  map level (scratch variant maps City_View_S4v<name>, made by ue/view_variants.py): fog density, fog colour scale kf (x the browser inscattering 0.76 / 0.78 / 0.80), aerial-perspective view distance scale
  MPC level (ue/set_mpc.py): FarGain FG, FarSunK FK, FarJit FJ
Round 1: one-at-a-time deltas around BASE; round 2: the combination of the winners + one extrapolation; the best of everything is written to <out>/best.json (and printed as shell assignments).
usage: s4_opt.py <out_dir> [deadline_s]   (deadline: seconds this script may run, default 1100; no new capture is started after it)"""
import sys, os, json, subprocess, time
WT = '/Users/midir/sm2-n1/city'; OUT = sys.argv[1]; DEADLINE = float(sys.argv[2]) if len(sys.argv) > 2 else 1100.0
os.makedirs(OUT, exist_ok=True); T0 = time.time()
BASE = dict(fog=0.0012, kf=1.0, aerial=0.34, FG=4.0, FK=0.22, FJ=1.3)
FOGC0 = (0.76, 0.78, 0.80)
MAPK = ('fog', 'kf', 'aerial'); MPCK = ('FG', 'FK', 'FJ')
def log(*a): print('[s4_opt %5.0fs]' % (time.time() - T0), *a, flush=True)
def sh(cmd, out=None):
    r = subprocess.run(cmd, shell=True, executable='/bin/zsh', stdout=open(out, 'w') if out else None, stderr=subprocess.STDOUT); return r.returncode
def waitengine():
    while subprocess.run("pgrep -f 'MacOS/UnrealEditor .*%s/unreal' >/dev/null" % WT, shell=True, executable='/bin/zsh').returncode == 0: time.sleep(3)
def sick():
    return subprocess.run("ps -axo stat=,comm= | awk '$1 ~ /[ZE]/ && $2 ~ /UnrealEditor/ && $2 !~ /Services/ {f=1} END {exit !f}'", shell=True, executable='/bin/zsh').returncode == 0
def fogc(kf): return ','.join('%.3f' % (c * kf) for c in FOGC0)
def mapkey(c): return tuple(c[k] for k in MAPK)
def mpckey(c): return tuple(c[k] for k in MPCK)
RES = {}   # tag -> dict(cfg, score line)
NMAP = [0]
def evaluate(plan):
    """plan: list of (tag, cfg). Makes the variant maps (one commandlet), then per MPC triple: set_mpc once + capture every config of that triple."""
    maps = {}
    for tag, c in plan:
        if mapkey(c) != mapkey(BASE) and mapkey(c) not in maps: NMAP[0] += 1; maps[mapkey(c)] = 'z%d' % NMAP[0]
    if maps:
        args = 'names=' + ','.join(maps.values()) + ' ' + ' '.join('fog_%s=%s fogc_%s=%s aerial_%s=%s' % (n, k[0], n, fogc(k[1]), n, k[2]) for k, n in maps.items())
        rc = sh('%s/tools/export/ue/run_commandlet.sh %s/tools/export/ue/view_variants.py %s' % (WT, WT, args), '%s/variants_%d.txt' % (OUT, len(RES))); waitengine(); log('variants rc', rc, args[:120])
        if rc != 0: return
    groups = {}
    for tag, c in plan: groups.setdefault(mpckey(c), []).append((tag, c))
    for trip, items in groups.items():
        if time.time() - T0 > DEADLINE: log('deadline: skip MPC group', trip); continue
        rc = sh('%s/tools/export/ue/run_commandlet.sh %s/tools/export/ue/set_mpc.py FarGain=%s FarSunK=%s FarJit=%s' % (WT, WT, *trip), '%s/set_mpc_%s.txt' % (OUT, '_'.join(map(str, trip)))); waitengine(); log('set_mpc', trip, 'rc', rc)
        if rc != 0: continue
        for tag, c in items:
            if time.time() - T0 > DEADLINE: log('deadline: skip', tag); continue
            if sick(): log('ABORT: engine stuck exiting'); sys.exit(7)
            mid = 'S4_perch_skyline' if mapkey(c) == mapkey(BASE) else 'S4v' + maps[mapkey(c)]
            d = os.path.join(OUT, tag); os.makedirs(d, exist_ok=True)
            rc = sh('%s/tools/export/capture_one.sh %s %s 1920x1080' % (WT, d, mid), os.path.join(d, 'cap.txt')); waitengine(); time.sleep(3)
            png = os.path.join(d, '%s_1920x1080_00_t028.0.png' % mid.split('_')[0])
            if rc != 0 or not os.path.exists(png): log('capture failed', tag, rc); continue
            r = subprocess.run(['python3', '%s/tools/export/s4_score.py' % WT, png], capture_output=True, text=True)
            try: j = json.loads(r.stdout.strip().splitlines()[-1])
            except Exception: log('score failed', tag, r.stderr[-200:]); continue
            RES[tag] = dict(cfg=c, **j); json.dump(RES, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
            log('%-8s score %.2f all_pass %s T1 %.1f T2 %.1f%% far %.1f (C13 %.1f) C14 %.1f C15 %.3f | %s' % (tag, j['score'], j['all_pass'], j['T1'], j['T2_pct'], j['far'], j['C13'], j['C14'], j['C15'], {k: c[k] for k in c if c[k] != BASE[k]}))
# ---- round 1
R1 = [('base', dict(BASE))]
for k, vals in (('aerial', (0.20, 0.10, 0.0)), ('kf', (0.82,)), ('fog', (0.0009, 0.0016)), ('FK', (0.15, 0.30)), ('FJ', (1.7,))):
    for v in vals: R1.append(('%s_%s' % (k, v), dict(BASE, **{k: v})))
evaluate(R1)
if 'base' not in RES: log('no base result: stop'); print('BEST none'); sys.exit(3)
# ---- round 2: the winners per dimension, then one extrapolation of the biggest winner
def winners():
    c = dict(BASE); gain = {}
    for k in ('aerial', 'kf', 'fog', 'FK', 'FJ'):
        cands = [(RES[t]['score'], t) for t in RES if t.startswith(k + '_')]
        if cands and min(cands)[0] < RES['base']['score']: s, t = min(cands); c[k] = RES[t]['cfg'][k]; gain[k] = RES['base']['score'] - s
    return c, gain
comb, gain = winners(); log('winners', {k: comb[k] for k in gain}, 'gain', {k: round(v, 2) for k, v in gain.items()})
plan2 = []
if comb != BASE: plan2.append(('comb', comb))
if gain:
    kbest = max(gain, key=gain.get); ext = dict(comb); v0, v1 = BASE[kbest], comb[kbest]; ext[kbest] = round(v1 + (v1 - v0) * 0.6, 5)
    if kbest == 'aerial': ext[kbest] = max(0.0, ext[kbest])
    if kbest == 'kf': ext[kbest] = max(0.3, ext[kbest])
    if ext != comb: plan2.append(('ext_' + kbest, ext))
evaluate(plan2)
best_tag = min(RES, key=lambda t: RES[t]['score']); best = RES[best_tag]['cfg']
json.dump(dict(tag=best_tag, cfg=best, fogc=fogc(best['kf']), score=RES[best_tag]['score'], all=RES), open(os.path.join(OUT, 'best.json'), 'w'), indent=1)
log('BEST', best_tag, best, RES[best_tag]['score'])
print('BEST_TAG=%s FOG=%s FOGC=%s AERIAL=%s FG=%s FK=%s FJ=%s' % (best_tag, best['fog'], fogc(best['kf']), best['aerial'], best['FG'], best['FK'], best['FJ']))
