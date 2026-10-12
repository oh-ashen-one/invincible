#!/usr/bin/env python3
"""Runs the live-fix scripts as nullrhi probes (one engine at a time) and tabulates the flip log lines + the end state.
usage: run_livefix.py <out_dir> [--only substr]"""
import json, re, subprocess, sys, csv, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else ''
names = [n for n in json.loads((ROOT / 'docs/night1/traversal/scripts/final/live/index.json').read_text()) if only in n]
rep = []
for n in names:
    q = '6.5' if n.startswith('air_') else '5.5'
    subprocess.run([sys.executable, str(ROOT / 'tools/final/swing/probe.py'), str(ROOT / 'docs/night1/traversal/scripts/final/live' / (n + '.json')), '--quit', q, '--out', str(out / 'cases')], capture_output=True, text=True)
    d = out / 'cases' / n
    log = (d / 'route.log').read_text(errors='ignore') if (d / 'route.log').exists() else ''
    picks = re.findall(r'WH_TRAV flip choice: .*?-> (\w+)', log); starts = re.findall(r'WH_TRAV air flip start (\w+) at h=([\d.]+)', log); refused = re.findall(r'WH_TRAV flip refused: [^\n\r]*', log)
    T = d / 'route_telemetry.csv'; minh = fin = '?'; webon = '?'; mtr = '-'
    if T.exists():
        R = list(csv.DictReader(T.open())); f = lambda r, k: float(r[k]) if r[k] not in ('', 'nan') else 0.0
        tr = [f(r, 'height_above_floor_m') for r in R if r['sub'] == 'trick']; mtr = '%.1f' % min(tr) if tr else '-'
        minh = '%.1f' % min(f(r, 'height_above_floor_m') for r in R); fin = '%s/%s h%.1f' % (R[-1]['mode'], R[-1]['sub'], f(R[-1], 'height_above_floor_m'))
        webon = '%.0f%%' % (100.0 * sum(1 for r in R if f(r, 'fw_s0_on') > 0.5 and f(r, 'fw_s0_rel', ) < 0) / len(R)) if 'fw_s0_on' in R[0] else '?'
    rep.append((n, picks, starts, refused, minh, mtr, fin, webon))
    print(n, 'picks', picks, 'start', starts, 'refused', refused, 'min_h', minh, 'min_h_in_trick', mtr, 'end', fin, 'web-on', webon, flush=True)
(out / 'LIVEFIX_REPORT.txt').write_text('\n'.join('%s | picks %s | air flip start %s | refused %s | min_h %s | min_h in trick %s | end %s | web-on %s' % r for r in rep) + '\n')
