#!/usr/bin/env python3
"""playable-profile perf matrix, one engine at a time through with_holder.sh (waits for the owner's session / the coexisting resident), no screenshots in the window.
configs: island r5 night / golden (docs/night1/island/scripts/r5_m2_avenue_alt0.json, perf 5:35), midtown route_30s night (route_30s_warmup15, perf 15:45); internal 67 / 58 / 50 % (TSR, 4K output), t.MaxFPS 0.
usage: perf_matrix.py <tag> [--configs island-night,island,showcase-night] [--scales 67,58,50] [--exec CMD]... [--only-first N]
output: ~/sm2-n1/_scratch/showcase/runs/<tag>_<map>_<scale>/ + <tag>_matrix.json (stall_report per run)"""
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = Path.home() / 'sm2-n1/_scratch/showcase/runs'
ISL = Path.home() / 'sm2-n1/island/docs/night1/island/scripts/r5_m2_avenue_alt0.json'
MID = ROOT / 'docs/night1/manhattan/scripts/route_30s_warmup15.json'
CFG = {'island-night': (ISL, '5:35', 37), 'island': (ISL, '5:35', 37), 'showcase-night': (MID, '15:45', 47)}

ap = argparse.ArgumentParser()
ap.add_argument('tag'); ap.add_argument('--configs', default='island-night,island,showcase-night'); ap.add_argument('--scales', default='67,58,50')
ap.add_argument('--exec', action='append', default=[])
ap.add_argument('--game-arg', action='append', default=[])
ap.add_argument('--realtime', action='store_true', help='no -benchmark -fps=60: the route follows the real frame rate (sim lag, differs run to run); default = fixed 60 Hz steps, a deterministic route')
a = ap.parse_args()
out = {}
for m in a.configs.split(','):
    script, perf, quit_ = CFG[m]
    for sc in a.scales.split(','):
        name = f'{a.tag}_{m}_{sc}'; d = RUNS / name
        if (d / 'route_frames.csv').exists(): print('skip', name); continue
        d.mkdir(parents=True, exist_ok=True)
        cmd = [str(ROOT / 'tools/showcase/with_holder.sh'), 'python3', str(ROOT / 'tools/showcase/play.py'), '--map', m, '--profile', 'playable', '--res-scale', sc, '--capture', str(d), '--name', 'route',
               '--script', str(script), '--perf', perf, '--quit', str(quit_), '--timeout', '1500', '--launch'] + sum([['--exec', e] for e in a.exec], []) + [f'--game-arg={g}' for g in a.game_arg + ([] if a.realtime else ['-benchmark', '-fps=60'])]
        (RUNS / (name + '.out')).write_text(subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout[-3000:])
        try:
            r = subprocess.run([sys.executable, str(ROOT / 'tools/showcase/stall_report.py'), str(d)], capture_output=True, text=True).stdout.strip()
            out[name] = json.loads(r); print(r, flush=True)
        except Exception as ex:
            print(name, 'FAILED', ex, flush=True)
(RUNS / f'{a.tag}_matrix.json').write_text(json.dumps(out, indent=1))
