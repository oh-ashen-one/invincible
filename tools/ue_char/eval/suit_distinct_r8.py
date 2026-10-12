# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: how different is the new hero suit from the old one, in numbers.  Compares the covered texels of the old (round 05-07, browser-derived) base colour with the new Tessera base colour:
hue-band shares (red, blue, white, teal, amber), the k-means palette, and the share of near-black thread pixels.  Writes JSON + a side-by-side atlas figure.

  python3 tools/ue_char/eval/suit_distinct_r8.py OLD_BASE.png NEW_BASE.png OUT_PREFIX
"""
import sys, os, json
import numpy as np
import cv2
from scipy.cluster.vq import kmeans2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'suit8'))
import meshio  # noqa: E402
old_p, new_p, out = sys.argv[1:4]
m = meshio.load_body()
N = 2048
tri, w0, w1, ins = meshio.raster_tri(m['UV'], m['F'], N)
cov = (tri >= 0)


def stats(path):
    im = cv2.imread(path)[..., ::-1]
    im = cv2.resize(im, (N, N), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    h = hsv[..., 0] / 255 * 360; s = hsv[..., 1] / 255; v = hsv[..., 2] / 255
    c = cov
    def share(mask): return round(float((mask & c).sum() / c.sum()), 4)
    sat = (s > 0.25) & (v > 0.18)
    res = dict(
        red=share(sat & ((h < 18) | (h > 340))), blue=share(sat & (h > 205) & (h < 265)), white=share((s < 0.18) & (v > 0.72)), teal=share(sat & (h > 165) & (h < 205)),
        amber=share(sat & (h > 22) & (h < 48)), near_black=share(v < 0.16))
    px = im[c].astype(np.float32)
    sel = px[np.random.RandomState(0).choice(len(px), 60000, replace=False)]
    cen, lab = kmeans2(sel, 6, seed=1, minit='++')
    cnt = np.bincount(lab, minlength=6) / len(lab)
    order = np.argsort(-cnt)
    res['palette'] = [dict(rgb=[int(x) for x in cen[i]], share=round(float(cnt[i]), 3)) for i in order]
    return res, im
a, ia = stats(old_p); b, ib = stats(new_p)
json.dump(dict(old=a, new=b), open(out + '.json', 'w'), indent=1)
W = 1024
fig = np.concatenate([cv2.resize(ia, (W, W), interpolation=cv2.INTER_AREA), np.full((W, 8, 3), 255, np.uint8), cv2.resize(ib, (W, W), interpolation=cv2.INTER_AREA)], 1)
cv2.imwrite(out + '_atlas.jpg', fig[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
print(json.dumps(dict(old=a, new=b)))
