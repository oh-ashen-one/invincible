#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17: crops of the chin / throat of the 8 headfront stills (r16 row over r17 row), centred on the tracked face seam (seam_track_r16.py json), so the seam through the chin and the free ends of the
cheek cords can be read by eye: python3 chin_crops_r17.py <r17 stills dir> <r17 seam_track.json> <r16 stills dir> <r16 seam_track.json> OUT.jpg"""
import sys, json, os, cv2, numpy as np
s17, j17, s16, j16, out = sys.argv[1:6]
J17, J16 = json.load(open(j17)), json.load(open(j16))
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
def crop(d, j, s):
    p = os.path.join(d, 'skin_%s_headfront_4k.png' % s)
    if not os.path.exists(p): p = p.replace('.png', '.jpg')
    im = cv2.imread(p); r = j.get(s) or {}
    cols = r.get('cols') or []
    x = int(np.median([c[1] for c in cols])) if cols else im.shape[1] // 2
    yb = int(r.get('y_bot') or 1750)
    y0 = max(0, min(im.shape[0] - 560, yb - 420)); x0 = max(0, min(im.shape[1] - 560, x - 280))
    c = im[y0:y0 + 560, x0:x0 + 560]
    cv2.putText(c, '%s %s' % (os.path.basename(d.rstrip('/')) if False else ('r17' if d == s17 else 'r16'), s), (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    return cv2.resize(c, (360, 360), interpolation=cv2.INTER_AREA)
top = np.hstack([crop(s16, J16, s) for s in SUITS]); bot = np.hstack([crop(s17, J17, s) for s in SUITS])
cv2.imwrite(out, np.vstack([top, bot]), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(out)
