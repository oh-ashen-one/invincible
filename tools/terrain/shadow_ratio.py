#!/usr/bin/env python3
"""Tree-shadow depth on the lawn (r05 target 4: every isolated tree in p4 casts a lawn shadow <= 0.6 x the lit lawn luma), CPU only.
For each hand-picked pair of boxes on a still (shadow = lawn inside one isolated tree's cast shadow, lit = sunlit lawn right beside it, same lawn type, no path / crown / trunk)
the ratio median luma(shadow) / median luma(lit) is reported (luma Y = 0.299 R + 0.587 G + 0.114 B, display values 0-255).
usage: shadow_ratio.py <stills dir> <boxes.json> <out.json>   boxes.json: {"<image>": [{"id": "...", "shadow": [x, y, w, h], "lit": [x, y, w, h]}, ...]}
Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation."""
import sys, json, os
import numpy as np
from PIL import Image
d, bj, out = sys.argv[1:4]
B = json.load(open(bj)); res = {'pairs': []}
for img, pairs in B.items():
    if img.startswith('_'): continue
    a = np.asarray(Image.open(os.path.join(d, img)).convert('RGB')).astype(np.float32); Y = a @ np.array([0.299, 0.587, 0.114], np.float32)
    for p in pairs:
        (sx, sy, sw, sh), (lx, ly, lw, lh) = p['shadow'], p['lit']
        s = float(np.median(Y[sy:sy + sh, sx:sx + sw])); l = float(np.median(Y[ly:ly + lh, lx:lx + lw]))
        res['pairs'].append({'image': img, 'id': p.get('id', ''), 'shadow_box': p['shadow'], 'lit_box': p['lit'], 'shadow_luma': round(s, 1), 'lit_luma': round(l, 1), 'ratio': round(s / max(l, 1e-3), 3)})
r = [p['ratio'] for p in res['pairs']]
res['summary'] = {'n': len(r), 'max_ratio': max(r) if r else None, 'median_ratio': round(float(np.median(r)), 3) if r else None, 'pass_all_le_0.6': bool(r) and max(r) <= 0.6}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps(res['summary']))
for p in res['pairs']: print('%-20s %-10s shadow %5.1f lit %5.1f ratio %.3f' % (p['image'], p['id'], p['shadow_luma'], p['lit_luma'], p['ratio']))
