# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: 3x crop montage of the enclosed key components of key_check_r7.py, so each one can be classified by eye (air between limbs / fingers, or a crack in a garment).
  python3 tools/ue_char/eval/key_components_r7.py STILL.png CHECK.json OUT.jpg [--min-px 40] [--pad 50]
One tile per component (3x Lanczos, component outlined in red on the right half of the tile, label: x,y,px,width)."""
import sys, json
import numpy as np
import cv2
a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return type(d)(v)
    return d
minpx = opt('--min-px', 40); pad = opt('--pad', 50)
still, chk, out = a[:3]
im = cv2.imread(still); H, W = im.shape[:2]
d = json.load(open(chk))
comps = [c for c in d['enclosed_key_top'] if c['px'] >= minpx]
tiles = []
key = np.array(d['key_bgr'])
for c in comps:
    x, y, w, h = c['bbox']; cx, cy = x + w // 2, y + h // 2
    x0 = int(np.clip(cx - pad, 0, W - 2 * pad)); y0 = int(np.clip(cy - pad, 0, H - 2 * pad))
    raw = im[y0:y0 + 2 * pad, x0:x0 + 2 * pad].copy()
    ov = raw.copy()
    m = (np.abs(raw.astype(int) - key[None, None, :]).max(axis=2) <= 8)
    # outline the component: key pixels inside its bbox that are enclosed = the bbox region's key pixels
    bx0, by0 = x - x0, y - y0
    sub = np.zeros(raw.shape[:2], bool); sub[max(0, by0):max(0, by0) + h, max(0, bx0):max(0, bx0) + w] = True
    cv2.rectangle(ov, (max(0, bx0) - 2, max(0, by0) - 2), (max(0, bx0) + w + 2, max(0, by0) + h + 2), (0, 0, 255), 1)
    t = np.hstack([cv2.resize(raw, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4), cv2.resize(ov, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)])
    cv2.putText(t, 'x%d y%d %dpx w%.0f' % (cx, cy, c['px'], c['width_px']), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    tiles.append(t)
if not tiles:
    print('no components >= %d px' % minpx); sys.exit(0)
cols = 2
rows = [np.hstack(tiles[i:i + cols] + [np.zeros_like(tiles[0])] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
print(out, len(tiles), 'tiles')
