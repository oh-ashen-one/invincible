#!/usr/bin/env python3
"""Round 09: see-through holes in the mask of a close-up capture (CH18).

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

tee_face_4k (critic r08: 'the mask has 3 see-through holes: 198 px, 91 px and 24 px'): the cloth of the tee mask is saturated red; its outline is closed and filled; every pixel
INSIDE that outline that is not cloth is a hole (the game draws single-sided, a reversed triangle or a gap shows whatever is behind the head).  Light holes (luma > LIGHT) are
see-through pixels proper; dark ones are slivers.  Components >= MIN px are listed.
  python3 tools/ue_char/eval/seethrough_4k.py IMG [--min 4] [--light 110] [--out overlay.png]
"""
import sys, json
import numpy as np
import cv2
from scipy import ndimage as ndi


def main():
    a = sys.argv[1:]
    img = cv2.imread(a[0])[..., ::-1].astype(np.int16)
    mn = int(a[a.index('--min') + 1]) if '--min' in a else 4
    light = int(a[a.index('--light') + 1]) if '--light' in a else 110
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    cloth = (r > g + 28) & (r > b + 24) & (r > 50)
    cloth = ndi.binary_opening(cloth, np.ones((3, 3), bool))
    big = ndi.label(ndi.binary_closing(cloth, np.ones((9, 9), bool)))[0]
    sizes = np.bincount(big.ravel()); sizes[0] = 0
    mask_outline = ndi.binary_fill_holes(big == sizes.argmax())
    inside = mask_outline & ~cloth
    luma = (0.299 * r + 0.587 * g + 0.114 * b)
    res = {'image': a[0], 'mask_px': int(mask_outline.sum())}
    neutral = (np.abs(r - g) < 16) & (np.abs(g - b) < 18)           # the background behind the head is an even grey; cloth highlights and stitches keep a red cast
    for name, sel in (('light', inside & (luma > light) & neutral), ('dark', inside & (luma <= 70) & neutral)):
        sel = ndi.binary_opening(sel, np.ones((1, 1), bool))
        lab, n = ndi.label(sel, structure=np.ones((3, 3), bool))
        sz = np.bincount(lab.ravel())[1:]
        comps = []
        for k in np.argsort(-sz):
            if sz[k] < mn: break
            ys, xs = np.where(lab == k + 1)
            y0, y1, x0, x1 = max(0, ys.min() - 9), ys.max() + 10, max(0, xs.min() - 9), xs.max() + 10
            cm = lab[y0:y1, x0:x1] == k + 1
            ring = ndi.binary_dilation(cm, iterations=6) & ~ndi.binary_dilation(cm, iterations=1)
            frac = float(cloth[y0:y1, x0:x1][ring].mean()) if ring.any() else 0.0
            if frac < 0.85: continue                      # not enclosed by cloth: skin / hair / background at the mask edge, not a hole in it
            comps.append({'px': int(sz[k]), 'cx': int(xs.mean()), 'cy': int(ys.mean()), 'ring_cloth': round(frac, 2)})
        res[name] = comps
        res['%s_px_total' % name] = int(sum(c['px'] for c in comps))
    res['light_components_ge_20_px'] = sum(1 for c in res['light'] if c['px'] >= 20)
    print(json.dumps(res))
    if '--out' in a:
        ov = np.clip(img, 0, 255).astype(np.uint8)[..., ::-1].copy()
        m = ndi.binary_dilation(mask_outline, iterations=1) & ~ndi.binary_erosion(mask_outline, iterations=1)
        ov[m] = (255, 255, 0)
        for grp, col in (('light', (0, 255, 255)), ('dark', (255, 0, 255))):
            for c in res[grp]: cv2.circle(ov, (c['cx'], c['cy']), 28, col, 2)
        cv2.imwrite(a[a.index('--out') + 1], ov)


if __name__ == '__main__':
    main()
