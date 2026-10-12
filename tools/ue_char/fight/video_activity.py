#!/usr/bin/env python3
"""Round 09: pixel activity of a fight clip per 1 s window (mean % of pixels whose luma changed by > 12/255 between consecutive frames, 480 x 270 proxy).
Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.  The same number round 08's critic quoted ('frame-diff 1.2 - 2.0 % px' while everybody held guard).
  python3 tools/ue_char/fight/video_activity.py clip.mp4 [--t0 0] [--json out.json]"""
import sys, json, subprocess
import numpy as np
a = sys.argv[1:]
t0 = float(a[a.index('--t0') + 1]) if '--t0' in a else 0.0
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', a[0], '-vf', 'scale=480:270,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 270, 480).astype(np.int16)
d = (np.abs(np.diff(fr, axis=0)) > 12).mean(axis=(1, 2)) * 100
rows = [(round(t0 + i / 60.0, 2), round(float(d[i:i + 60].mean()), 2)) for i in range(0, len(d) - 59, 15)]
print('window start s -> mean frame-diff %:', ' '.join('%.2f:%.2f' % r for r in rows[::2]))
print('min %.2f  median %.2f  max %.2f' % (min(v for _, v in rows), float(np.median([v for _, v in rows])), max(v for _, v in rows)))
if '--json' in a: json.dump({'clip': a[0], 'windows': rows}, open(a[a.index('--json') + 1], 'w'), indent=1)
