#!/usr/bin/env python3
"""Skin/white patch test for the brute in captured 4K frames (fan homage project; not official Marvel/Sony/Insomniac).

Two deterministic `-movie` runs of the same shot: BEAUTY (Char_Lineup) and MASK (Char_Lineup_BruteMask: identical actors and
timing, the brute drawn unlit with T_Brute_Regions, R = face skin, G = hands, B = everything else, every other character unlit yellow,
black background).
Per frame pair: the mask gives the brute's pixels and their region; on the beauty frame, CLOTH pixels (mask B, eroded 6 px, at
least 14 px away from any hand/face pixel so motion blur cannot smear skin into cloth) are classified:
  skin-like  hue 8-38 deg, sat 0.22-0.65, value >= 0.42 (strict) / >= 0.30 (loose)
  white-like value >= 0.80, sat <= 0.18
The same detector is run on the hand/face pixels as a control (it must fire there).

usage: measure_frames.py BEAUTY_FRAMES_DIR MASK_FRAMES_DIR OUT.json [--step 3] [--from 30] [--overlay OUT.jpg]
"""
import sys, os, glob, json, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser()
ap.add_argument('beauty'); ap.add_argument('mask'); ap.add_argument('out')
ap.add_argument('--step', type=int, default=3)
ap.add_argument('--start', type=int, default=30, help='skip the first N frames (texture streaming, brute entering frame)')
ap.add_argument('--overlay', default=None)
A = ap.parse_args()

bf = sorted(glob.glob(os.path.join(A.beauty, '*.png')))
mf = sorted(glob.glob(os.path.join(A.mask, '*.png')))
n = min(len(bf), len(mf))
print('frames beauty %d mask %d -> pairs %d' % (len(bf), len(mf), n))


def hsv(a):
    a = a.astype(np.float32) / 255.0
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn + 1e-9
    h = np.where(mx == a[..., 0], ((a[..., 1] - a[..., 2]) / d) % 6, np.where(mx == a[..., 1], (a[..., 2] - a[..., 0]) / d + 2, (a[..., 0] - a[..., 1]) / d + 4)) * 60.0
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-9), 0.0)
    return h, s, mx


def skin(h, s, v, vmin):
    return (h >= 8) & (h <= 38) & (s >= 0.22) & (s <= 0.65) & (v >= vmin)


def white(h, s, v):
    return (v >= 0.80) & (s <= 0.18)


rows = []
worst = None
for i in range(A.start, n, A.step):
    b = np.array(Image.open(bf[i]).convert('RGB'))
    m = np.array(Image.open(mf[i]).convert('RGB')).astype(np.int16)
    if b.shape != m.shape:
        raise SystemExit('size mismatch %s %s' % (b.shape, m.shape))
    mx = m.max(-1)
    on = mx >= 60
    R, G, B = m[..., 0], m[..., 1], m[..., 2]
    # pure classes only: anything in between (edge blends, another character's blur mixing yellow into blue) is 'contaminated' and excluded
    cloth = on & (R < 70) & (G < 70) & (B > 120)
    face = on & (R > 150) & (G < 90) & (B < 120)
    hands = on & (G > 150) & (R < 90) & (B < 120)
    other = (R > 45) & (G > 45) & (B < 0.6 * np.minimum(R, G)) & (np.abs(R - G) < 0.45 * np.maximum(R, G))   # other characters (unlit yellow) incl. faint blur tails
    contam = (on & ~(cloth | face | hands)) | other
    if cloth.sum() < 2000:
        rows.append(dict(frame=i, brute_px=int(on.sum()), note='brute not in frame')); continue
    near_skin = ndi.binary_dilation(face | hands, iterations=14)
    near_other = ndi.binary_dilation(contam, iterations=30) if contam.any() else np.zeros_like(contam)
    cloth_e = ndi.binary_erosion(cloth, iterations=6) & ~near_skin & ~near_other
    hh, ss, vv = hsv(b)
    sk_s, sk_l, wh = skin(hh, ss, vv, 0.42), skin(hh, ss, vv, 0.30), white(hh, ss, vv)
    hf_e = ndi.binary_erosion(face | hands, iterations=3)
    fl = (sk_s | wh) & cloth_e
    lab, nl = ndi.label(fl)
    blob = int(np.bincount(lab.ravel())[1:].max()) if nl else 0      # largest connected flagged region (a 'patch' would be hundreds of px)
    r = dict(frame=i, brute_px=int(on.sum()), cloth_px=int(cloth_e.sum()), max_blob_px=blob,
             skin_strict=int((sk_s & cloth_e).sum()), skin_loose=int((sk_l & cloth_e).sum()), white=int((wh & cloth_e).sum()),
             ctrl_hand_face_px=int(hf_e.sum()), ctrl_skin_strict=int((sk_s & hf_e).sum()), ctrl_white=int((wh & hf_e).sum()))
    rows.append(r)
    sc = r['skin_strict'] + r['white']
    if worst is None or sc > worst[0]:
        worst = (sc, i, b, cloth_e, sk_s | wh)

ok = [r for r in rows if 'cloth_px' in r]
tot = lambda k: int(sum(r[k] for r in ok))
summ = dict(frames_analysed=len(ok), frames_skipped=len(rows) - len(ok), cloth_px=tot('cloth_px'),
            skin_strict=tot('skin_strict'), skin_loose=tot('skin_loose'), white=tot('white'),
            max_skin_strict_in_a_frame=max((r['skin_strict'] for r in ok), default=0), max_skin_loose_in_a_frame=max((r['skin_loose'] for r in ok), default=0),
            max_white_in_a_frame=max((r['white'] for r in ok), default=0), largest_flagged_blob_px=max((r['max_blob_px'] for r in ok), default=0),
            frames_with_any_skin_strict=sum(1 for r in ok if r['skin_strict'] > 0), frames_with_any_white=sum(1 for r in ok if r['white'] > 0),
            control_hand_face_px=tot('ctrl_hand_face_px'), control_skin_strict=tot('ctrl_skin_strict'),
            control_skin_strict_fraction=round(tot('ctrl_skin_strict') / max(1, tot('ctrl_hand_face_px')), 3))
summ['skin_strict_fraction_of_cloth'] = round(summ['skin_strict'] / max(1, summ['cloth_px']), 7)
summ['white_fraction_of_cloth'] = round(summ['white'] / max(1, summ['cloth_px']), 7)
json.dump(dict(summary=summ, frames=rows), open(A.out, 'w'), indent=1)
print(json.dumps(summ, indent=1))
if A.overlay and worst:
    _, i, b, cl, bad = worst
    o = b.copy()
    o[cl & ~bad] = (o[cl & ~bad] * 0.6 + np.array([0, 90, 0]) * 0.4).astype(np.uint8)    # green tint = evaluated cloth pixels
    o[cl & bad] = (255, 0, 255)                                                          # magenta = flagged
    Image.fromarray(o).resize((1920, 1080)).save(A.overlay, quality=88)
    print('overlay frame', i)
