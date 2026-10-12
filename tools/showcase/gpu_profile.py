#!/usr/bin/env python3
"""Top GPU passes of a ProfileGPU dump in a game log (WH_EXEC ProfileGPU via -WHExecAt): exclusive ms per pass name (identical names summed), the top N.
usage: gpu_profile.py <log> [--top 12] [--json out.json]"""
import json, re, sys
from collections import defaultdict
log = open(sys.argv[1], errors='replace').read().splitlines()
top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 12
start = next((i for i, l in enumerate(log) if 'GPU Profile for Frame' in l), None)
if start is None: sys.exit('no ProfileGPU dump in ' + sys.argv[1])
frame_ms = None; ex = defaultdict(float); n = defaultdict(int)
for l in log[start:]:
    if 'LogRHI: Display:' not in l: 
        if ex and 'LogRHI' not in l: break
        continue
    m = re.search(r'Frame Time\s*:\s*([\d.]+)ms', l)
    if m and frame_ms is None: frame_ms = float(m.group(1))
    parts = l.split('┃')
    if len(parts) < 4: continue
    t = re.search(r'([\d.]+) ms', parts[1])
    name = re.sub(r'\s*\(.*$', '', parts[3]).strip().strip('"')
    if t and name and 'Percent' not in name:
        ex[re.sub(r'\d+', '#', name)] += float(t.group(1)); n[re.sub(r'\d+', '#', name)] += 1
rows = sorted(ex.items(), key=lambda kv: -kv[1])[:top]
out = {'gpu_frame_ms': frame_ms, 'top': [{'pass': k, 'ms': round(v, 3), 'events': n[k]} for k, v in rows]}
print('GPU frame %.2f ms' % (frame_ms or 0))
for r in out['top']: print('%7.3f ms  %3d  %s' % (r['ms'], r['events'], r['pass']))
if '--json' in sys.argv: open(sys.argv[sys.argv.index('--json') + 1], 'w').write(json.dumps(out, indent=1))
