#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life: PERF_TABLE.md from the run_game perf JSONs + the gpu_slot.sh perf sidecars in a round directory (round 02: 4K output, r.ScreenPercentage 67 = TSR 67 %).
#   python3 tools/life/perf_table.py docs/night1/life/round-02
import json, os, sys
R = sys.argv[1]
def load(n):
    p = os.path.join(R, n)
    return json.load(open(p)) if os.path.exists(p) else None
ROWS = [('life off (`-WHLifeOff`: no traffic, no crowd, no signal lenses)', '4k_off'), ('life ON (default: traffic 2.3 x browser density, ~1460 camera-centred walkers of which about 500 are live skinned meshes, 100 looks, lit signal lenses)', '4k_on'),
        ('crowd only (`-WHTrafficOff`)', '4k_crowd_only'), ('traffic only (`-WHCrowdOff`)', '4k_traffic_only')]
out = ['# P6 City life round 02: GPU-locked perf (S1 street view, Life_View_S1, game t = 22-52 s)\n',
       '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.\n',
       'Every run: `gpu_slot.sh perf` (exclusive, waited for GPU < 15 % for 10 s, `contaminated=false`), Mac Studio M3 Ultra, Metal SM6, golden-hour rig, **3840x2160 output, `r.ScreenPercentage 67` (TSR, internal 2573x1447)**. '
       'Frame times include everything else in the P1 / P4 scene (Lumen, VSM, ...); read the DIFFERENCE between rows. Run-to-run spread of the scene itself is a few ms (round 01 measured up to 9 ms between two identical 4K runs), so the difference of single runs is indicative, not exact. Budget from the brief: <= 3 ms GPU.\n',
       '| variant | frames | avg ms | p95 | p99 | GPU avg ms | GPU util before / during avg | valid |\n|---|---|---|---|---|---|---|---|']
res = {}
for label, key in ROWS:
    p = load('perf_%s.json' % key); g = load('perf_gpu_%s.json' % key)
    if not p: continue
    res[key] = p
    out.append('| %s | %d | %.2f | %.2f | %.2f | %.2f | %s / %s | %s |' % (label, p['frames'], p['avg_ms'], p['p95_ms'], p['p99_ms'], p['gpu_avg_ms'],
               '%.0f %%' % g['util_before'] if g else 'n/a', '%.0f %%' % g['util_during']['avg'] if g else 'n/a', 'perf_valid' if g and g.get('perf_valid') else 'CONTAMINATED'))
if '4k_off' in res and '4k_on' in res:
    a, b = res['4k_off'], res['4k_on']
    out.append('\nLife ON minus OFF: **%+.2f ms GPU**, %+.2f ms frame (avg), %+.2f ms p95 frame.' % (b['gpu_avg_ms'] - a['gpu_avg_ms'], b['avg_ms'] - a['avg_ms'], b['p95_ms'] - a['p95_ms']))
out.append('')
open(os.path.join(R, 'PERF_TABLE.md'), 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
