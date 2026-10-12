#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02 (r03: + hero blows and reaction misses): one table row per run dir (fight_summary.json + sim_metrics): pick the record run to freeze.
#   sweep_report.py <run_dir> [<run_dir> ...]
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import react_metrics as RM
print('%-34s %5s %4s %3s %3s %3s %4s %5s %5s %5s %5s %5s %5s %5s %5s' % ('run', 'hits', 'lnch', 'air', 'fin', 'web', 'kos', 'gap', 'en>=5', 'marg', 'occ%', 'occF', 'dmg', 'blow', 'miss'))
for d in sys.argv[1:]:
    try:
        S = json.load(open(os.path.join(d, 'fight_summary.json')))
        M = json.loads(subprocess.run([sys.executable, os.path.join(here, 'sim_metrics.py'), d], capture_output=True, text=True).stdout)
    except Exception as e:
        print('%-34s %s' % (os.path.basename(d), e)); continue
    print('%-34s %5d %4d %3d %3d %3d %4d %5.2f %5.2f %5.3f %5.1f %5d %5d %5d %4d' % (os.path.basename(d.rstrip('/')), S['hits'], S['launches'], S['air_hits'], S['finishers'], S['web_hits'], S['kos'],
          M['max_attack_gap'] or 0, M['enemies_ge5_frac'], M['hero_margin_min'], M['occluder_max_pct'], M['occluder_gt15_frames'], S['damage_taken'], RM.summarize(RM.analyse(*RM.load(d)))['hero_blows'], len(RM.summarize(RM.analyse(*RM.load(d)))['misses'])))
