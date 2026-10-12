#!/usr/bin/env python3
"""-nullrhi sim probe of a clip script on an island map (fixed 1/60 s): writes <out>/<script>/{route_telemetry.csv, route.log} and prints a one-line mode timeline.
usage: probe.py <script.json> [--map island|island-night] [--out DIR] [--quit S]"""
import argparse, csv, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ap = argparse.ArgumentParser()
ap.add_argument('script'); ap.add_argument('--map', default='island'); ap.add_argument('--out', default=str(Path.home() / 'sm2-n1/_scratch/final/swing/probe')); ap.add_argument('--quit', type=float); ap.add_argument('--game-arg', action='append', default=[]); ap.add_argument('--no-preroll', action='store_true')
a = ap.parse_args()
s = Path(a.script).resolve(); name = s.stem
q = a.quit or json.loads((ROOT / 'docs/night1/traversal/scripts/final/clips.json').read_text()).get('_q', {}).get(name, 6.0)
if a.no_preroll and not a.quit: q = 20.5   # the baseline run (final-before binary) was 20.5 s
PRE = 0.0 if a.no_preroll else 1.5
q += PRE   # the capture pre-roll renders the start pose first; -WHQuitAt counts it
out = Path(a.out) / name
subprocess.run(['rm', '-rf', str(out)])
cmd = [str(ROOT / 'tools/showcase/with_holder.sh'), 'python3', str(ROOT / 'tools/showcase/play.py'), '--map', a.map, '--profile', 'playable', '--res-scale', '100', '--res', '1920x1080',
       '--capture', str(out), '--name', 'route', '--script', str(s), '--quit', str(q), '--timeout', '900', '--game-arg=-benchmark', '--game-arg=-fps=60', '--game-arg=-nullrhi', '--launch'] + ['--game-arg=' + g for g in a.game_arg] + ([] if a.no_preroll else ['--game-arg=-WHTravPreroll=1.5'])
subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
rows = list((csv.DictReader((out / 'route_telemetry.csv').open()))) if (out / 'route_telemetry.csv').exists() else []
if not rows: sys.exit('%s: no telemetry (see %s)' % (name, out))
tl = []; prev = None
for r in rows:
    k = r['mode'] + ('/' + r['sub'] if r['mode'] in ('air', 'wall') else '')
    if k != prev: tl.append('%.2f %s h%.0f' % (float(r['t']), k, float(r['height_above_floor_m']))); prev = k
print(name, 'rows', len(rows), 'spawn (%.1f %.1f %.1f)' % (float(rows[0]['x_m']), float(rows[0]['y_m']), float(rows[0]['z_m'])), 'end (%.0f %.0f %.0f)' % (float(rows[-1]['x_m']), float(rows[-1]['y_m']), float(rows[-1]['z_m'])), 'min_h %.1f' % min(float(r['height_above_floor_m']) for r in rows))
print('  ' + ' | '.join(tl[:40]))
