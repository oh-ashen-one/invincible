#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 10 engine-side check of TRAVERSAL-SPEC T1 / T2 / T3 / T4 / T7 from a capture's telemetry:
#   swings (attach -> release, held s, low point over the floor), web-less phases (duration, peak / low height, peak -> low s,
#   share of 0.1 s samples whose pose_sig changed), per-8 s window web_on share and attach count, and the roof heights beside
#   the path (city layout footprints, lit city only).
# usage: rhythm_check.py <telemetry.csv> [layout.json] [t0 t1]
import csv, json, sys
import numpy as np
R = list(csv.DictReader(open(sys.argv[1])))
LAY = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].endswith('.json') else None
rest = [a for a in sys.argv[2:] if not a.endswith('.json') and not a.startswith('--')]
T0 = float(rest[0]) if rest else 0.0; T1 = float(rest[1]) if len(rest) > 1 else 1e9
f = lambda r, k: float(r[k]) if r.get(k) not in (None, '') else 0.0
R = [r for r in R if T0 - 1e-6 <= f(r, 't') <= T1 + 1e-6]
t = np.array([f(r, 't') for r in R]); web = np.array([f(r, 'web_on') > 0.5 for r in R])
swing = np.array([r['mode'].lower() == 'swing' for r in R]); hf = np.array([f(r, 'height_above_floor_m') for r in R])
# round 10: heights are FEET OVER THE STREET (z - 0.95 m; the city street is z = 0) - height_above_floor_m also counts trees,
# awnings and vehicle roofs below him as floor. --floor keeps the old measure.
if '--floor' not in sys.argv: hf = np.array([f(r, 'z_m') - 0.95 for r in R])
sig = [r.get('pose_sig', '') for r in R]; sub = [r['sub'] for r in R]
FP = json.load(open(LAY))['footprints'] if LAY else []
def roof_beside(x, y):   # tallest footprint within 45 m of (x, y) in UE metres (browser x, z)
    hs = [p['h'] for p in FP if p['x0'] - 45 < x < p['x1'] + 45 and p['z0'] - 45 < y < p['z1'] + 45]
    lo = [p['h'] for p in FP if p['x0'] - 25 < x < p['x1'] + 25 and p['z0'] - 25 < y < p['z1'] + 25]
    return (min(lo) if lo else None, max(hs) if hs else None)
# swings
sw = []; i = 0
while i < len(R):
    if swing[i]:
        j = i
        while j + 1 < len(R) and swing[j + 1]: j += 1
        sw.append((i, j)); i = j + 1
    else: i += 1
print(f'{sys.argv[1]}  window {t[0]:.2f}-{t[-1]:.2f} s')
print(' swings (T1 held 0.5-1.6 s): ' + '  '.join(f'{t[a]:.2f}-{t[b]:.2f} ({t[b]-t[a]:.2f}s, low {hf[a:b+1].min():.1f} m, rel {hf[b]:.1f} m)' for a, b in sw))
# web-less phases between swings
print(' web-less phases (T4: > 0.6 s needs a changing silhouette at every 0.1 s; T7: peak at roofline -> 3-13 m low within 4 s):')
for k in range(len(sw) - 1):
    a, b = sw[k][1] + 1, sw[k + 1][0] - 1
    if b <= a: continue
    d = t[b] - t[a]
    ps = [sig[q] for q in range(a, b + 1, 6)]
    ch = np.mean([ps[q] != ps[q - 1] for q in range(1, len(ps))]) if len(ps) > 1 else 1.0
    pk = a + int(np.argmax(hf[a:b + 1])); nxt = sw[k + 1]; lo = nxt[0] + int(np.argmin(hf[nxt[0]:nxt[1] + 1]))
    rb = roof_beside(f(R[pk], 'x_m'), f(R[pk], 'y_m')) if FP else (None, None)
    subs = []
    for q in range(a, b + 1):
        if not subs or subs[-1] != sub[q] + (':' + R[q]['trick'] if R[q].get('trick') else ''): subs.append(sub[q] + (':' + R[q]['trick'] if R[q].get('trick') else ''))
    print(f'   {t[a]:.2f}-{t[b]:.2f} {d:.2f}s  peak {hf[pk]:.1f} m @{t[pk]:.2f}  next low {hf[lo]:.1f} m @{t[lo]:.2f} (peak->low {t[lo]-t[pk]:.2f}s)'
          f'  pose changes {ch:.2f}  roofs beside low/high {rb[0]}/{rb[1]}  [{" > ".join(subs)}]')
# windows
att = [t[a] for a, b in sw]
print(' 8 s windows (start: web_on share, attaches) [T2 2-4 attaches, T3 video 25-45 %]:')
ws = []
for w0 in np.arange(t[0], max(t[0] + 0.01, t[-1] - 8 + 0.01), 0.5):
    m = (t >= w0) & (t < w0 + 8)
    ws.append(f'{w0:.1f}:{web[m].mean():.2f}/{sum(1 for x in att if w0 <= x < w0 + 8)}')
print('   ' + ' '.join(ws))
print(f' web_on whole window {web.mean():.2f}; max height {hf.max():.1f} m, min in air {hf[~swing].min() if (~swing).any() else 0:.1f} m')
