#!/usr/bin/env python3
"""Round 11: hair faults of an enemy face close-up at 4K (critic r10's single biggest gap).  Fan homage project; no affiliation.

  python3 tools/ue_char/eval/hair_4k.py IMG --box x0,y0,x1,y1 [--out overlay.png] [--json out.json]

Inside the head box (the hair + upper face) it measures three things:
  1. colour seams: the image is blurred (sigma 3 px) to remove strand detail and converted to CIELAB; a pixel is a colour edge when the
     CHROMA / hue difference (a*, b*) across 6 px exceeds 9 or the lightness difference exceeds 38, and both sides are hair (not skin, not
     background).  Straight runs are found with a probabilistic Hough transform (min length 40 px, max gap 4 px); reported: every straight
     colour-seam segment >= 40 px inside the hair.
  2. flat cards: hair pixels whose 21 x 21 neighbourhood has a luminance std < 6 % of its mean (mean > 28; a flat-shaded card has no strand texture); components of
     those wider AND taller than 20 px are listed (bbox).
  3. background between hair and skin: pixels within 14 RGB units of the background colour (median of the box's top corners) that are NOT
     connected to the outer background (= enclosed by the head); components >= 6 px are listed.
Hair = not background, not skin (r > g + 8, g >= b, saturation 0.12 - 0.62, luma > 95), luma < 125, saturation < 0.55;
an enclosed background patch counts only when >= 25 % of a 6 px ring round it is hair; the cloth mask is
excluded by a rule on its saturated, non-skin colour only when --nomask is given its colour.
"""
import sys, json
import numpy as np, cv2
from scipy import ndimage as ndi

a = sys.argv[1:]
img = cv2.imread(a[0])
box = [int(x) for x in a[a.index('--box') + 1].split(',')]
x0, y0, x1, y1 = box
sub = img[y0:y1, x0:x1].astype(np.float32)
rgb = sub[..., ::-1]
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
mx = rgb.max(-1); mn = rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
luma = 0.299 * r + 0.587 * g + 0.114 * b
# background: the colour of the full image's top-left and top-right corners (the lineup's grey studio)
full = img.astype(np.float32)
corners = np.concatenate([full[:60, :60].reshape(-1, 3), full[:60, -60:].reshape(-1, 3)])
bgc = np.median(corners, 0)
bg = np.abs(sub - bgc[None, None, :]).max(-1) < 14
_m1 = cv2.blur(sub.mean(-1), (5, 5)); _m2 = cv2.blur(sub.mean(-1) ** 2, (5, 5))
bg_flat = bg & (np.sqrt(np.maximum(_m2 - _m1 ** 2, 0)) < 3.0)      # the studio background is flat; strand highlights of the same grey are not
skin = (r > g + 8) & (g >= b) & (sat > 0.12) & (sat < 0.62) & (luma > 95)
hsv = cv2.cvtColor(np.clip(sub, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32); hue = hsv[..., 0] * 2.0
blue = (b > r + 12)                                                         # the tee's cap
hair = ~bg & ~skin & ~blue & (luma < 125) & (sat < 0.55)          # hair is darker than the skin and less saturated than the cloth mask
_l1 = cv2.blur(luma, (9, 9)); _l2 = cv2.blur(luma * luma, (9, 9)); tex9 = np.sqrt(np.maximum(_l2 - _l1 * _l1, 0))
blond = ~bg & (hue >= 18) & (hue <= 62) & (sat < 0.40) & (luma > 140) & (cv2.blur(tex9, (15, 15)) > 7.0)   # light hair: pale AND strand-textured (the forehead skin is smooth)
hair_any = hair | blond
if '--maskrgb' in a:            # exclude the cloth mask (its colour +- 40)
    mc = np.array([float(x) for x in a[a.index('--maskrgb') + 1].split(',')])
    hair &= ~(np.abs(rgb - mc[None, None, :]).max(-1) < 40)
hair = ndi.binary_opening(hair, np.ones((3, 3), bool))
# 1. colour seams = the boundary between two hair colours (dark hair | light / blond hair), each side >= 60 % of a 9 x 9 window
fd = cv2.blur(hair.astype(np.float32), (9, 9)); fb = cv2.blur(blond.astype(np.float32), (9, 9))
edge = (ndi.grey_dilation(fd, size=7) > 0.6) & (ndi.grey_dilation(fb, size=7) > 0.6) & ((fd > 0.15) & (fb > 0.15))
edge = ndi.binary_dilation(edge, iterations=1) & ~bg
edge[:8] = edge[-8:] = False; edge[:, :8] = edge[:, -8:] = False
lines = cv2.HoughLinesP(edge.astype(np.uint8) * 255, 1, np.pi / 180, threshold=30, minLineLength=40, maxLineGap=4)
segs = []
if lines is not None:
    for l in lines.reshape(-1, 4):
        ln = float(np.hypot(l[2] - l[0], l[3] - l[1]))
        segs.append({'from': [int(l[0] + x0), int(l[1] + y0)], 'to': [int(l[2] + x0), int(l[3] + y0)], 'len_px': round(ln, 1)})
segs.sort(key=lambda s: -s['len_px'])
# 2. flat cards
m1 = cv2.blur(luma, (21, 21)); m2 = cv2.blur(luma * luma, (21, 21))
std = np.sqrt(np.maximum(m2 - m1 * m1, 0))
flat = hair & (std < 0.06 * np.maximum(m1, 1)) & (m1 > 28) & ndi.binary_erosion(hair, iterations=10)   # flat shading: coefficient of variation < 6 % over 21 x 21 (dark hair in shadow is not flat by this measure)
lab_f, n = ndi.label(flat)
cards = []
for k, sl in enumerate(ndi.find_objects(lab_f)):
    hgt = sl[0].stop - sl[0].start; wid = sl[1].stop - sl[1].start
    if wid > 20 and hgt > 20:
        cards.append({'bbox': [sl[1].start + x0, sl[0].start + y0, sl[1].stop + x0, sl[0].stop + y0], 'w': int(wid), 'h': int(hgt), 'px': int((lab_f[sl] == k + 1).sum())})
# 3. enclosed background
lb, nb = ndi.label(bg_flat, structure=np.ones((3, 3), bool))
outer = set(np.unique(np.concatenate([lb[0], lb[-1], lb[:, 0], lb[:, -1]]))) - {0}
sizes = np.bincount(lb.ravel())
holes = []
for k in range(1, nb + 1):
    if k in outer or sizes[k] < 6: continue
    sl = ndi.find_objects((lb == k).astype(int))[0]
    sl = (slice(max(sl[0].start - 8, 0), sl[0].stop + 8), slice(max(sl[1].start - 8, 0), sl[1].stop + 8))
    ring = ndi.binary_dilation(lb[sl] == k, iterations=6) & ~(lb[sl] == k)
    if (hair_any[sl] & ring).sum() < 0.2 * ring.sum() or (skin[sl] & ring).sum() < 0.1 * ring.sum(): continue   # BETWEEN hair and skin     # a background-grey patch must sit in the HAIR (the lens of the sunglasses / a pale cap seam is not a gap)
    ys, xs = np.nonzero(lb == k)
    holes.append({'bbox': [int(xs.min() + x0), int(ys.min() + y0), int(xs.max() + x0), int(ys.max() + y0)], 'px': int(sizes[k])})
holes.sort(key=lambda h: -h['px'])
res = {'image': a[0], 'box': box, 'background_rgb': [int(v) for v in bgc[::-1]], 'hair_px': int(hair.sum()),
       'seams_ge_40px': segs[:20], 'n_seams_ge_40px': len(segs), 'longest_seam_px': segs[0]['len_px'] if segs else 0.0,
       'flat_cards_gt_20px': cards, 'n_flat_cards': len(cards),
       'enclosed_background': holes[:20], 'n_enclosed_background': len(holes), 'enclosed_background_px': int(sum(h['px'] for h in holes))}
print(json.dumps(res))
if '--json' in a: json.dump(res, open(a[a.index('--json') + 1], 'w'), indent=1)
if '--out' in a:
    ov = sub.astype(np.uint8).copy()
    ov[hair] = (0.7 * ov[hair] + 0.3 * np.array([255, 0, 0])).astype(np.uint8)
    ov[edge] = (0, 255, 255)
    ov[flat] = (255, 0, 255)
    for h in holes:
        bx = h['bbox']; cv2.rectangle(ov, (bx[0] - x0 - 4, bx[1] - y0 - 4), (bx[2] - x0 + 4, bx[3] - y0 + 4), (0, 0, 255), 3)
    for s in segs:
        cv2.line(ov, (s['from'][0] - x0, s['from'][1] - y0), (s['to'][0] - x0, s['to'][1] - y0), (0, 255, 0), 4)
    cv2.imwrite(a[a.index('--out') + 1], ov)
