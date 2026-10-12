# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C r01 (resume after the traversal r25/r26 merge): probe the 60 s reel script in the REAL game with -nullrhi (deterministic fixed
# 60 Hz step, telemetry + rendered-bone log), score the route (rows swinging / airborne vs ground / wall-run / landing) and run
# tricks_check.py on it. If the base route breaks, candidate turn keys are probed in order and the first clean one wins (else the best).
# Run INSIDE one held capture slot (the caller: gpu_slot.sh capture --label tricks -- ...).
#   python3 tools/tricks/probe_reel.py <base script.json> <out script.json> <work dir>     -> prints the check, writes <work>/VERDICT
import copy, csv, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tricks_check as TC

BASE, OUT, WORK = sys.argv[1:4]
WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN = os.path.join(WT, 'unreal', 'WebHomage', 'Scripts', 'run_game.sh')
MAXN = int(os.environ.get('MAXPROBES', '5'))
# a C++ change made while the hold's content build ran: compile it first (no engine of this worktree runs between the steps)
FLAG = '/Users/midir/sm2-n1/_scratch/tricks/REBUILD_CPP'
if os.path.exists(FLAG):
    r = subprocess.run([os.path.join(WT, 'unreal', 'WebHomage', 'Scripts', 'build_editor.sh')], capture_output=True, text=True)
    print('C++ rebuild rc %d: %s' % (r.returncode, (r.stdout.strip().splitlines() or [''])[-1]), flush=True)
    if r.returncode == 0: os.remove(FLAG)
    else: print(r.stdout[-2000:]); sys.exit(3)


def probe(script, tag):
    d = os.path.join(WORK, tag); os.makedirs(d, exist_ok=True)
    tel, pose = os.path.join(d, 'probe_telemetry.csv'), os.path.join(d, 'probe_pose.csv')
    for p in (tel, pose):
        if os.path.exists(p): os.remove(p)
    t0 = time.time()
    subprocess.run([RUN, d, '-map', '/Game/Maps/Manhattan', '-res', '1920x1080', '-quit', '61.5', '-name', 'probe', '-timeout', '900', '--',
                    '-nullrhi', '-benchmark', '-fps=60', '-WHTravScript=' + script, '-WHTravPreroll=0.8', '-WHTravCsv=' + tel,
                    '-WHTrickPose=' + pose], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    R = list(csv.DictReader(open(tel))) if os.path.exists(tel) else []
    print('probe %s: %d rows in %.0f s' % (tag, len(R), time.time() - t0), flush=True)
    return R, tel, pose


def score(R):
    n = {'air': 0, 'swing': 0, 'wall': 0, 'ground': 0, 'land': 0, 'other': 0}
    for r in R:
        if float(r['t']) < 1.0: continue
        n[r['mode'] if r['mode'] in n else 'other'] += 1
    tricks = len(TC.instances(R))
    bad = n['wall'] + n['ground'] + n['land']
    end = R[-1] if R else None
    return dict(n, tricks=tricks, bad=bad, t_end=float(end['t']) if end else 0, xy_end=(round(float(end['x_m'])), round(float(end['y_m']))) if end else None)


def with_keys(j, extra, drop_after=None):
    k = copy.deepcopy(j)
    keys = [x for x in k['keys'] if not ('heading' in x and x['t'] > 0 and drop_after is not None and x['t'] >= drop_after)]
    k['keys'] = sorted(keys + extra, key=lambda x: x['t'])
    return k


def first_cross(R, ax, coord, sgn, after):
    for r in R:
        if float(r['t']) > after and sgn * (float(r[ax]) - coord) >= 0: return float(r['t'])
    return None


j0 = json.load(open(BASE))
cands = [('base', j0)]
tried = []
best = None
i = 0
while i < len(cands) and i < MAXN:
    tag, j = cands[i]; i += 1
    path = os.path.join(WORK, 'cand_%s.json' % tag); json.dump(j, open(path, 'w'), indent=1)
    R, tel, pose = probe(path, tag)
    if not R:
        print('  %s: no telemetry' % tag); continue
    s = score(R)
    print('  %s: %s' % (tag, s), flush=True)
    tried.append((tag, s))
    if best is None or (s['bad'], -s['tricks']) < (best[1]['bad'], -best[1]['tricks']): best = (tag, s, j, tel, pose, R)
    if s['bad'] == 0 and s['t_end'] >= 60.4: break
    if tag == 'base':
        # refit the 5th Av turn on this physics: heading 90 when the hero is LEAD m before x 250, then the south leg's 92 key 15.4 s later
        for lead in (32, 26, 38):
            t = first_cross(R, 'x_m', 250.0 - lead, +1, 2.0)
            if t is not None:
                cands.append(('lead%d' % lead, with_keys(j0, [{'t': round(t, 2), 'heading': 90}, {'t': round(t + 15.4, 2), 'heading': 92}], drop_after=1.0)))
tag, s, j, tel, pose, R = best
json.dump(j, open(OUT, 'w'), indent=1)
print('BEST %s %s' % (tag, s))
rep = TC.main(tel, pose)
print(rep)
ok = s['bad'] == 0 and s['t_end'] >= 60.4
lines = {l.split()[0]: l for l in rep.splitlines() if l[:2].strip() in ('P', 'V1', 'V2', 'K', 'L', 'G1', 'G2', 'G3', 'G4') and not l.startswith('   ')}
fails = [k for k, l in lines.items() if 'FAIL' in l]
open(os.path.join(WORK, 'VERDICT'), 'w').write('route %s %s\nfails %s\n' % ('OK' if ok else 'BROKEN', tag, ' '.join(fails) or 'none'))
print('VERDICT route %s (%s); failing lines: %s' % ('OK' if ok else 'BROKEN', tag, ' '.join(fails) or 'none'))
