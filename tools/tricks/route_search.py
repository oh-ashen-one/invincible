# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C round 1: pick the continuation of the 60 s reel by probing variants (-nullrhi, deterministic) and scoring t >= FROM s:
# share of rows swinging / airborne, minus wall-run / ground / landing rows; the best variant's script is written to <out>.
# Run INSIDE one held capture slot:  gpu_slot.sh capture --label tricks -- python3 tools/tricks/route_search.py <base.json> <out.json> <work>
# (r01: auto_route's street turns failed -- the 5th Av leg landed on a 24 m roof at 35.8 s, a west turn mid-triple wall-ran a tower.)
import csv, json, os, subprocess, sys

BASE, OUT, WORK = sys.argv[1:4]
FROM = float(os.environ.get('FROM', '25'))
WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN = os.path.join(WT, 'unreal', 'WebHomage', 'Scripts', 'run_game.sh')
FIXED = [{'t': 12.63, 'heading': 90}]   # fitted: the turn into 5th Av (window 0 = 0-25 s is already rendered with it)
ROT = 'backPike,barani,backLayout,frontDouble,fullTwist,frontPikeSwan,backDouble,rudi,corkscrew,backTripleChain,backSingle,frontSingle'
VARIANTS = {
    'A': [],
    'B': [{'t': 28.0, 'heading': 88}],
    'C': [{'t': 28.0, 'heading': 92}],
    'D': [{'t': 26.0, 'heading': 84}, {'t': 29.0, 'heading': 90}],
    'E': [{'t': 31.0, 'heading': 86}],
    'F': [{'t': 25.2, 'flip': ROT}],
    'G': [{'t': 25.2, 'flip': ROT}, {'t': 28.0, 'heading': 88}],
    'H': [{'t': 32.5, 'heading': 80}],
}
only = os.environ.get('ONLY', '')


def probe(script, tag):
    d = os.path.join(WORK, tag); os.makedirs(d, exist_ok=True)
    tel = os.path.join(d, 'probe_telemetry.csv')
    subprocess.run([RUN, d, '-map', '/Game/Maps/Manhattan', '-res', '1920x1080', '-quit', '61.5', '-name', 'probe', '-timeout', '900', '--',
                    '-nullrhi', '-benchmark', '-fps=60', '-WHTravScript=' + script, '-WHTravPreroll=0.8', '-WHTravCsv=' + tel],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return list(csv.DictReader(open(tel))) if os.path.exists(tel) else []


def score(R):
    rows = [r for r in R if float(r['t']) >= FROM]
    if not rows: return -1e9, {}
    n = len(rows)
    c = {m: sum(1 for r in rows if r['mode'] == m) for m in ('air', 'swing', 'wall', 'ground', 'land', 'perch', 'zip')}
    tricks = len({(r['flip_prog'], r['t'][:4]) for r in rows if r['flip_prog'] and float(r['flip_t'] or -1) < 0.02})
    ys = [float(r['y_m']) for r in rows]
    s = (c['air'] + c['swing']) / n - 2.0 * (c['ground'] + c['land'] + c['perch']) / n - 1.0 * c['wall'] / n
    c.update(n=n, tricks=tricks, y_end=round(ys[-1]), t_end=float(rows[-1]['t']))
    return s, c


base = json.load(open(BASE))
k0 = [k for k in base['keys'] if 'heading' not in k or k['t'] == 0.0]
best = None
for name, extra in VARIANTS.items():
    if only and name not in only: continue
    j = json.loads(json.dumps(base))
    j['keys'] = k0 + FIXED + extra
    p = os.path.join(WORK, 'var_%s.json' % name); json.dump(j, open(p, 'w'), indent=1)
    R = probe(p, 'var_' + name)
    s, c = score(R)
    print('variant %s %s: score %.3f %s' % (name, json.dumps(extra), s, c), flush=True)
    if best is None or s > best[0]: best = (s, name, j)
print('BEST variant %s score %.3f' % (best[1], best[0]))
json.dump(best[2], open(OUT, 'w'), indent=1)
