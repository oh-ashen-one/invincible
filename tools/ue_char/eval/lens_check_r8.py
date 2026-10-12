# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: eye checks on the hero key stills (Char_HeroKey: the hero writes custom-depth stencil, the post-process key paints every non-hero pixel one flat colour,
bloom / vignette off; needs r.CustomDepth 3).  The hero keeps its real materials, so the eye classes are read from colour inside an eye ROI:

  python3 tools/ue_char/eval/lens_check_r8.py hero_key_face_4k.png --out DIR [--flat] --eye NAME x0 y0 x1 y1 [--eye NAME2 ...]

--flat: the still was rendered with -WHFlatClasses (tools/ue_char/capture_r5.sh gHK): every slot of the hero is an unlit class colour (lens magenta, bezel yellow, suit blue), so the classes are exact
(nearest channel pattern) and the bezel / hood question below is answered without colour heuristics.  Without --flat the classes are read from the real colours (amber lens, neutral bezel).

Per eye ROI (native pixels; must contain the whole eye, bezel included, and nothing else amber):
  exterior key      pixels equal to the key colour (the modal colour of the image corners) that are connected to the image border
  lens              the largest connected amber / yellow region in the ROI (R > 170, G > 110, B < 0.6 G)
  bezel             near-neutral dark-to-mid pixels (max - min < 28) in the ROI
  hood              teal / ink-teal suit pixels (B or G exceeds R by > 10, not amber)
Numbers (round target): enclosed_key_px       key pixels NOT connected to the border within the ROI (= background seen through a gap between rim and lens, or through the rim): 0 required
                        lens_touch_key_px     lens pixels with an exterior key pixel within 2 px (a lens at the silhouette): 0 required
                        lens_min_dist_exterior_px  smallest distance from any lens pixel to the exterior key region
                        lens_outline_hood_px  lens outline pixels whose 3-px neighbourhood holds hood-coloured pixels but no bezel pixel (a rim missing between lens and mask)
Writes <name>_classes.png (overlay) and <name>_lenscheck.json."""
import sys, os, json
import numpy as np
import cv2
from scipy import ndimage as ndi
a = sys.argv[1:]
img = a[0]
out = a[a.index('--out') + 1] if '--out' in a else '.'
eyes = []
i = 0
while i < len(a):
    if a[i] == '--eye': eyes.append((a[i + 1], [int(v) for v in a[i + 2:i + 6]])); i += 6
    else: i += 1
os.makedirs(out, exist_ok=True)
raw = cv2.imread(img, cv2.IMREAD_UNCHANGED)
rgb = raw[..., 2::-1].astype(np.int32) if raw.shape[2] == 4 else raw[..., ::-1].astype(np.int32)
H, W = rgb.shape[:2]
corners = np.concatenate([rgb[:20, :20].reshape(-1, 3), rgb[-20:, :20].reshape(-1, 3), rgb[:20, -20:].reshape(-1, 3), rgb[-20:, -20:].reshape(-1, 3)])
vals, cnt = np.unique(corners, axis=0, return_counts=True)
keyc = vals[np.argmax(cnt)]
KEY = (np.abs(rgb - keyc[None, None, :]) <= 3).all(-1)       # the key dithers between neighbouring levels (187 / 188): tolerance 3
lab, nl = ndi.label(KEY)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
EXT = np.isin(lab, list(border))
dist_ext = ndi.distance_transform_edt(~EXT)
R_, G_, B_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
AMB = (R_ > 170) & (G_ > 110) & (B_ < 0.6 * G_) & ~KEY
NEUT = ((rgb.max(-1) - rgb.min(-1)) < 28) & (rgb.max(-1) < 200) & ~KEY
HOOD = ((B_ > R_ + 10) | (G_ > R_ + 10)) & ~AMB & ~KEY & (rgb.max(-1) < 160)
FLAT = '--flat' in a
if FLAT:
    mxc = rgb.max(-1).astype(np.float32) + 1e-6
    nrm = rgb / mxc[..., None]
    dark = mxc < 40
    F_LENS = (nrm[..., 0] > 0.8) & (nrm[..., 2] > 0.7) & (nrm[..., 1] < 0.5) & ~dark & ~KEY
    F_BEZ = (nrm[..., 0] > 0.8) & (nrm[..., 1] > 0.8) & (nrm[..., 2] < 0.5) & ~dark & ~KEY
    F_SUIT = (nrm[..., 2] > 0.85) & (nrm[..., 0] < 0.45) & (nrm[..., 1] < 0.6) & ~dark & ~KEY
if '--auto' in a and FLAT:       # one ROI per magenta component (the two eyes), bbox + 140 px
    lab_m, nm = ndi.label(F_LENS)
    szs = ndi.sum(F_LENS, lab_m, range(1, nm + 1))
    boxes = []
    objs = ndi.find_objects(lab_m)
    for i in range(nm):
        if szs[i] < 3000: continue
        sl = objs[i]
        boxes.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
    boxes.sort()
    eyes = [(('L', 'R')[k] if len(boxes) == 2 else 'eye%d' % k, [max(b[0] - 140, 0), max(b[1] - 140, 0), min(b[2] + 140, W), min(b[3] + 140, H)]) for k, b in enumerate(boxes)]
res = dict(image=os.path.basename(img), size=[W, H], key_rgb=[int(v) for v in keyc], exterior_key_px=int(EXT.sum()), mode='flat' if FLAT else 'beauty', eyes={})
ov = np.zeros((H, W, 3), np.uint8); ov[EXT] = (0, 140, 0)
st4 = ndi.generate_binary_structure(2, 1)
for name, (x0, y0, x1, y1) in eyes:
    roi = np.zeros((H, W), bool); roi[y0:y1, x0:x1] = True
    if FLAT:
        LENS = F_LENS & roi
        if not LENS.any():
            res['eyes'][name] = dict(error='no lens pixels (magenta) in ROI'); continue
        enclosed = KEY & ~EXT & roi
        near_eye6 = ndi.binary_dilation(F_LENS | F_BEZ, iterations=6)
        enc_eye = enclosed & near_eye6
        outline = LENS & ~ndi.binary_erosion(LENS, structure=st4)
        nb4 = ndi.binary_dilation(outline, structure=st4) & ~LENS
        ys, xs = np.nonzero(outline)
        res['eyes'][name] = dict(roi=[x0, y0, x1, y1], lens_px=int(LENS.sum()), bezel_px=int((F_BEZ & roi).sum()), lens_bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                                 background_between_rim_and_lens_px=int(enc_eye.sum()), enclosed_key_px_in_roi=int(enclosed.sum()),
                                 lens_touch_key_px=int((LENS & ndi.binary_dilation(EXT, iterations=2)).sum()), lens_min_dist_exterior_px=round(float(dist_ext[LENS].min()), 1),
                                 lens_outline_px=int(outline.sum()), lens_outline_bezel_neighbours=int((nb4 & F_BEZ).sum()), lens_outline_suit_or_key_neighbours=int((nb4 & (F_SUIT | KEY)).sum()),
                                 lens_outline_unclassified_neighbours=int((nb4 & ~F_BEZ & ~F_SUIT & ~KEY & ~F_LENS).sum()),
                                 ring3_px=int((ndi.binary_dilation(LENS, iterations=3) & ~LENS).sum()),
                                 ring3_bezel_px=int((ndi.binary_dilation(LENS, iterations=3) & ~LENS & F_BEZ).sum()),
                                 ring3_suit_px=int((ndi.binary_dilation(LENS, iterations=3) & ~LENS & F_SUIT).sum()),
                                 ring3_key_px=int((ndi.binary_dilation(LENS, iterations=3) & ~LENS & KEY).sum()),
                                 ring3_blend_px=int((ndi.binary_dilation(LENS, iterations=3) & ~LENS & ~F_BEZ & ~F_SUIT & ~KEY & ~F_LENS).sum()),
                                 bezel_touch_key_px=int((F_BEZ & roi & ndi.binary_dilation(EXT, iterations=1)).sum()),
                                 bezel_min_dist_exterior_px=round(float(dist_ext[F_BEZ & roi].min()), 1) if (F_BEZ & roi).any() else None)
        ov[LENS] = (255, 0, 255); ov[F_BEZ & roi] = (255, 255, 0); ov[F_SUIT & roi] = (40, 60, 200); ov[enc_eye] = (255, 0, 0)
        continue
    la, na = ndi.label(AMB & roi)
    if na == 0:
        res['eyes'][name] = dict(error='no lens found in ROI'); continue
    sz = ndi.sum(AMB & roi, la, range(1, na + 1)); LENS = la == (int(np.argmax(sz)) + 1)
    LENS = ndi.binary_closing(LENS, iterations=2) | LENS           # specular highlights punch white holes into the lens: fill them
    LENS = ndi.binary_fill_holes(LENS)
    enclosed = KEY & ~EXT & roi
    touch = LENS & (ndi.binary_dilation(EXT, iterations=2))
    outline = LENS & ~ndi.binary_erosion(LENS, structure=st4)
    near = ndi.binary_dilation(outline, iterations=3)
    bez_near = (NEUT & roi & ~LENS) & near
    hood_near = (HOOD & roi) & near
    # outline pixels with hood close by and NO neutral (bezel) pixel within 3 px
    ys, xs = np.nonzero(outline)
    open_px = 0
    bz = ndi.binary_dilation(NEUT & roi & ~LENS, iterations=3); hd = ndi.binary_dilation(HOOD & roi, iterations=3)
    open_px = int((outline & hd & ~bz).sum())
    res['eyes'][name] = dict(roi=[x0, y0, x1, y1], lens_px=int(LENS.sum()), lens_bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
                             enclosed_key_px=int(enclosed.sum()), lens_touch_key_px=int(touch.sum()), lens_min_dist_exterior_px=round(float(dist_ext[LENS].min()), 1),
                             lens_outline_px=int(outline.sum()), lens_outline_hood_px=open_px, bezel_px_near_lens=int(bez_near.sum()))
    ov[LENS] = (255, 0, 255); ov[enclosed] = (255, 0, 0); ov[NEUT & roi & ~LENS] = (200, 200, 0)
base = os.path.splitext(os.path.basename(img))[0]
json.dump(res, open(os.path.join(out, base + '_lenscheck.json'), 'w'), indent=1)
cv2.imwrite(os.path.join(out, base + '_classes.png'), ov[..., ::-1])
print(json.dumps(res))
