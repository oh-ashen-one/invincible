#!/usr/bin/env python3
"""Round 09: skin-coloured components in the collar box of thug_face_4k (CH18 'collar skin wedge 100 x 180 px').  Fan homage project; no affiliation.
  python3 tools/ue_char/eval/wedge_4k.py IMG [--box x0,y0,x1,y1] [--out overlay.png]
Skin = r > g + 8, g >= b, saturation 0.15 - 0.65, luma > 85.  Every 8-connected component >= 40 px is listed with its bounding box; the neck itself is the biggest one (it is natural skin), the
'wedge' of rounds 07 / 08 was the second-biggest, a separate component 100 x 180 px inside the dark collar."""
import sys, json
import numpy as np, cv2
from scipy import ndimage as ndi
a = sys.argv[1:]
img = cv2.imread(a[0])[..., ::-1].astype(np.int16)
box = [int(x) for x in a[a.index('--box') + 1].split(',')] if '--box' in a else [1450, 1100, 2100, 1750]
x0, y0, x1, y1 = box
sub = img[y0:y1, x0:x1]
r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
mx = sub.max(-1); mn = sub.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
luma = 0.299 * r + 0.587 * g + 0.114 * b
skin = (r > g + 8) & (g >= b) & (sat > 0.15) & (sat < 0.65) & (luma > 85)
skin = ndi.binary_opening(skin, np.ones((3, 3), bool))
lab, n = ndi.label(skin, structure=np.ones((3, 3), bool))
sz = np.bincount(lab.ravel())[1:]
comps = []
for k in np.argsort(-sz):
    if sz[k] < 40: break
    ys, xs = np.where(lab == k + 1)
    comps.append({'px': int(sz[k]), 'bbox': [int(xs.min() + x0), int(ys.min() + y0), int(xs.max() + x0), int(ys.max() + y0)], 'w': int(xs.max() - xs.min() + 1), 'h': int(ys.max() - ys.min() + 1)})
print(json.dumps({'image': a[0], 'box': box, 'components_ge_40_px': comps[:10], 'n': len(comps)}))
if '--out' in a:
    ov = np.clip(sub, 0, 255).astype(np.uint8)[..., ::-1].copy(); ov[skin] = (0.5 * ov[skin] + 0.5 * np.array([0, 255, 255])).astype(np.uint8)
    cv2.imwrite(a[a.index('--out') + 1], ov)
