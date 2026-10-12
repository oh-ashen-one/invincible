# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C round 1: fit the turn keys of the 60 s reel to the deterministic simulation (-nullrhi probes, run INSIDE one held GPU capture
# slot by the caller: gpu_slot.sh capture --label tricks -- python3 tools/tricks/auto_route.py ...).
# Route (layout.json streets, UE metres, north = -y): east along the y -560 edge street -> south (+y) down 5th Av (x 250) -> west along the
# y 80 street -> north (-y) up 8th Av (x -250). Each turn key is placed when the hero is LEAD m before the next street's centre line
# (r01 probe v2: a key 29-33 m before 5th Av at 42-52 m/s turned cleanly into it).
#   python3 tools/tricks/auto_route.py <base script.json> <out script.json> <work dir>
import csv, json, os, subprocess, sys

BASE, OUT, WORK = sys.argv[1], sys.argv[2], sys.argv[3]
WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN = os.path.join(WT, 'unreal', 'WebHomage', 'Scripts', 'run_game.sh')
LEAD = float(os.environ.get('LEAD', '32'))
# (heading after the turn, axis, coordinate of the next street, direction of travel before the turn along that axis)
# r01 fit 1: turning at the y 240 street failed -- at y ~170 (34 s) a swing threw him onto a 24 m roof east of 5th Av; the west leg now takes
# the y 80 street (76-84) at ~30 s, leaving 8th Av for the last ~15 s
TURNS = [(90, 'x_m', 250.0, +1), (180, 'y_m', 80.0, +1), (-90, 'x_m', -250.0, -1)]


def probe(script, tag, quit_s):
    d = os.path.join(WORK, tag); os.makedirs(d, exist_ok=True)
    tel = os.path.join(d, 'probe_telemetry.csv')
    subprocess.run([RUN, d, '-map', '/Game/Maps/Manhattan', '-res', '1920x1080', '-quit', str(quit_s), '-name', 'probe', '-timeout', '900', '--',
                    '-nullrhi', '-benchmark', '-fps=60', '-WHTravScript=' + script, '-WHTravPreroll=0.8', '-WHTravCsv=' + tel], check=False)
    return list(csv.DictReader(open(tel))) if os.path.exists(tel) else []


def summary(R, step=60):
    return ' | '.join('%.0fs (%.0f,%.0f,%.0f) %s' % (float(r['t']), float(r['x_m']), float(r['y_m']), float(r['z_m']), r['mode']) for r in R[::step])


j = json.load(open(BASE))
keys = [k for k in j['keys'] if 'heading' not in k or k['t'] == 0.0]
t_last = 0.0
# FIXED_KEYS="12.63:90,29.97:180": turn keys already fitted by an earlier probe (the sim is deterministic) -- only the rest are probed
fixed = [kv.split(':') for kv in os.environ.get('FIXED_KEYS', '').split(',') if kv]
for t, h in fixed:
    keys = keys + [{'t': float(t), 'heading': int(h)}]; t_last = float(t)
for i, (head, ax, coord, sgn) in enumerate(TURNS):
    if i < len(fixed): continue
    j['keys'] = keys
    path = os.path.join(WORK, 'route_%d.json' % i); json.dump(j, open(path, 'w'), indent=1)
    R = probe(path, 'turn%d' % i, 61.5)
    print('probe %d: %d rows; %s' % (i, len(R), summary(R)), flush=True)
    hit = None
    for r in R:
        t = float(r['t'])
        if t <= t_last + 2.0: continue
        if sgn * (float(r[ax]) - (coord - sgn * LEAD)) >= 0: hit = t; break
    g0 = next((float(r['t']) for r in R if r['mode'] in ('ground', 'land') and float(r['t']) > 1.0), None)
    if g0 is not None and (hit is None or g0 < hit):
        print('turn %d: WARNING ground contact at t %.2f before the turn' % (i, g0), flush=True)
    if hit is None:
        print('turn %d: the hero never came within %.0f m of %s %.0f -- stop' % (i, LEAD, ax, coord)); break
    print('turn %d: heading %d at t %.2f' % (i, head, hit), flush=True)
    keys = keys + [{'t': round(hit, 2), 'heading': head}]
    t_last = hit
j['keys'] = keys
json.dump(j, open(OUT, 'w'), indent=1)
R = probe(OUT, 'final', 61.5)
print('final: %d rows; %s' % (len(R), summary(R, 120)))
gr = sum(1 for r in R if r['mode'] in ('ground', 'land'))
wl = sum(1 for r in R if r['mode'] == 'wall')
print('final: ground/land rows %d, wall rows %d, tricks started %d' % (gr, wl, len(set((r['flip_prog'], r['trick']) for r in R if r['flip_prog']))))
