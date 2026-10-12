# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Silhouette spikes (vertex spikes / shards outside the cloth hull) on a chroma-key capture, round 06.

  python3 spike_key.py KEY_IMAGE [KEY_IMAGE ...] [--r 3] [--min-len 6] [--out DIR]

person mask = non-key pixels (same key definition as key_report.py).  A spike is a part of the mask that a morphological opening with a disc of
radius r (default 3 px, i.e. features narrower than 2r+1 = 7 px) removes and that reaches more than --min-len px (default 6) beyond the opened
mask (geodesic distance from the opened mask, measured along the spike).  Round-05 vertex spikes on the olive coat / trousers were 20-150 px
long at native 4K; a healthy silhouette (fingertips, hair strands, shoelaces) has few and short ones.  Prints one JSON line per image:
spike components, spike px, max spike length, and the same per 100k person pixels.  With --out writes DIR/<image>_spikes.png (red = spikes)."""
import sys, os, json
import numpy as np
import cv2
from scipy import ndimage

a = sys.argv[1:]
opt = {'--r': '3', '--min-len': '6', '--out': None}
for k in list(opt):
    if k in a:
        i = a.index(k); opt[k] = a[i + 1]; a = a[:i] + a[i + 2:]
R = int(opt['--r']); MINLEN = int(opt['--min-len']); out = opt['--out']
if out: os.makedirs(out, exist_ok=True)
disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * R + 1, 2 * R + 1))
for f in a:
    im = cv2.imread(f)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
    b, g, r = [im[..., k].astype(int) for k in range(3)]
    key = (hsv[..., 0] > 45) & (hsv[..., 0] < 85) & (hsv[..., 1] > 140) & (g > 90) & (g - np.maximum(r, b) > 60)
    person = ~key
    lab, n = ndimage.label(person); sz = np.bincount(lab.ravel())
    person = (sz[lab] >= 3000) & (lab > 0)
    person = ndimage.binary_closing(person, structure=np.ones((3, 3), bool))
    opened = cv2.morphologyEx(person.astype(np.uint8), cv2.MORPH_OPEN, disc).astype(bool)
    rest = person & ~opened
    lab2, n2 = ndimage.label(rest, structure=np.ones((3, 3), bool))
    dist = ndimage.distance_transform_edt(~opened)        # distance of a spike pixel to the body it hangs on
    comps = []
    for i, sl in enumerate(ndimage.find_objects(lab2), 1):
        m = lab2[sl] == i
        L = float(dist[sl][m].max())
        if L > MINLEN:
            comps.append((int(m.sum()), round(L, 1), [int(sl[1].start), int(sl[0].start), int(sl[1].stop - sl[1].start), int(sl[0].stop - sl[0].start)]))
    comps.sort(key=lambda c: -c[1])
    px = int(person.sum())
    res = dict(image=os.path.basename(f), person_px=px, spikes=len(comps), spike_px=int(sum(c[0] for c in comps)), max_len_px=(comps[0][1] if comps else 0),
               spikes_over_20px=int(sum(c[1] > 20 for c in comps)), spikes_per_100k_person_px=round(1e5 * len(comps) / max(px, 1), 2), top=comps[:6])
    print(json.dumps(res))
    if out:
        ov = im.copy(); keep = np.zeros_like(person)
        for i, sl in enumerate(ndimage.find_objects(lab2), 1):
            if float(dist[sl][lab2[sl] == i].max()) > MINLEN: keep[sl] |= (lab2[sl] == i)
        ov[keep] = (0, 0, 255)
        cv2.imwrite(os.path.join(out, os.path.splitext(os.path.basename(f))[0] + '_spikes.png'), cv2.resize(ov, None, fx=0.5, fy=0.5))
