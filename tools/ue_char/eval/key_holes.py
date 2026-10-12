# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""CH18 in the real engine (round 05): see-through cracks in character meshes, measured on a chroma-key capture.

  python3 key_holes.py KEY_IMAGE [OUT_OVERLAY.png] [--min-person 3000] [--thin 7]

The key image comes from Char_CrowdKey (capture_r5.sh gK): the street and facades are unlit pure green, no fog, no sky.  Every green pixel that is
ENCLOSED by a person (holes of the person mask after removing small specks) is background seen through the character mesh.  Holes are split into
  thin  = removed by nothing but a `thin` px opening (a crack / sliver: width <= thin px)  -> the CH18 count
  wide  = the rest (gaps between arm and torso, between the legs: natural pose gaps, listed for reference).
Silhouette-edge gaps are not enclosed and not counted (same for every version of the meshes, so the numbers compare across rounds).
Prints one JSON line."""
import sys, json
import numpy as np
import cv2
from scipy import ndimage

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
im = cv2.imread(args[0]); H, W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
b, g, r = [im[..., k].astype(int) for k in range(3)]
key = (hsv[..., 0] > 45) & (hsv[..., 0] < 85) & (hsv[..., 1] > 140) & (g > 90) & (g - np.maximum(r, b) > 60)
person = ~key
# ignore what is not a person: remove small specks of non-key pixels (JPEG noise on the key), keep components >= min_person px
minp = int(opt.get('--min-person', 3000)); thin = int(opt.get('--thin', 7))
lab, n = ndimage.label(person)
sz = np.bincount(lab.ravel())
person = (sz[lab] >= minp) & (lab > 0)
person = ndimage.binary_closing(person, structure=np.ones((3, 3), bool))          # anti-aliased edge pixels between person and key
filled = ndimage.binary_fill_holes(person)
holes = filled & ~person
# thin part = holes minus their opening
op = ndimage.binary_opening(holes, structure=np.ones((thin, thin), bool))
thin_m = holes & ~op
lt, nt = ndimage.label(thin_m)
st = np.bincount(lt.ravel())[1:] if nt else np.array([])
keep = np.where(st >= 4)[0] + 1
thin_final = np.isin(lt, keep)
lw, nw = ndimage.label(op)
out = dict(image=args[0].split('/')[-1], person_px=int(person.sum()), holes_px=int(holes.sum()), thin_components=int(len(keep)), thin_px=int(thin_final.sum()),
           wide_components=int(nw), wide_px=int(op.sum()))
# per person (connected people masks)
lp, npers = ndimage.label(person)
per = []
for k in range(1, npers + 1):
    m = lp == k
    if m.sum() < 8000: continue
    ys, xs = np.where(m)
    tl = thin_final & ndimage.binary_dilation(m, iterations=2)
    ln, nn = ndimage.label(tl)
    per.append(dict(bbox=[int(xs.min()), int(ys.min()), int(xs.max() - xs.min()), int(ys.max() - ys.min())], thin_components=int(nn), thin_px=int(tl.sum())))
out['per_person'] = sorted(per, key=lambda q: -q['thin_components'])[:12]
print(json.dumps(out))
if len(args) > 1:
    vis = im.copy()
    vis[thin_final] = (0, 0, 255)
    vis[op] = (255, 0, 255)
    cv2.imwrite(args[1], vis)
