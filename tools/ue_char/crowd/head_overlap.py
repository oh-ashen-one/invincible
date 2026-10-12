# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: per-frame HEAD contacts between walkers in the crowd tracking shot (critic r07: 'two heads are fused in crowd_tracking_4k').

  python3 tools/ue_char/crowd/head_overlap.py FRAMES_DIR OUT.json [--first 36] [--count 444] [--min-px 120] [--head 0.17] [--touch 3]

FRAMES_DIR = the per-walker id movie (id_movie.sh, id colours as in id_overlap.py).  The head of a walker = the top --head fraction of its silhouette height (of its
visible pixels; a walker cut by the frame edge is skipped).  Per frame:
  head_head  pairs whose head regions touch within --touch px (two heads fused / kissing on the screen),
  head_body  pairs where one head region touches ANY pixel of another walker (a head overlapping a shoulder / neck / hair of another person).
`clear` frames have no head_head and no head_body pair; stills are picked from the longest runs of clear frames.  Output per frame + the list of clear runs."""
import sys, os, json
import numpy as np
import cv2
from scipy import ndimage
a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return type(d)(v)
    return d
first = opt('--first', 36); count = opt('--count', 444); minpx = opt('--min-px', 120); hfrac = opt('--head', 0.17); touch = opt('--touch', 3)
fdir, out = a[:2]
per = []
st = ndimage.generate_binary_structure(2, 2)
for f in range(first, first + count):
    p = os.path.join(fdir, 'MovieFrame%05d.png' % f)
    if not os.path.exists(p): continue
    im = cv2.imread(p)[..., ::-1].astype(int)
    lev = np.where(im > 200, 2, np.where(im > 90, 1, 0))
    ids = lev[..., 0] + 3 * lev[..., 1] + 9 * lev[..., 2]
    ids[(im.max(axis=2) < 40)] = 0
    H, W = ids.shape
    masks, heads = {}, {}
    for i in np.unique(ids):
        if i == 0: continue
        m = ids == i
        if int(m.sum()) < minpx: continue
        ys, xs = np.nonzero(m)
        if ys.min() <= 0 or ys.max() >= H - 1: continue          # cut by the top / bottom of the frame
        if xs.min() <= 0 or xs.max() >= W - 1: continue          # cut by the side
        hh = ys.min() + hfrac * (ys.max() - ys.min())
        hd = m.copy(); hd[int(hh):] = False
        masks[int(i)] = m; heads[int(i)] = hd
    keys = sorted(masks)
    hh_pairs, hb_pairs = [], []
    for x in keys:
        dil = ndimage.binary_dilation(heads[x], structure=st, iterations=touch)
        for y in keys:
            if y == x: continue
            if (dil & masks[y]).any():
                hb_pairs.append((x, y))
                if y > x and (dil & heads[y]).any(): hh_pairs.append((x, y))
    per.append(dict(frame=f, walkers=len(keys), head_head=hh_pairs, head_body=hb_pairs, clear=(not hb_pairs)))
runs, cur = [], None
for p in per:
    if p['clear']:
        if cur is None: cur = [p['frame'], p['frame']]
        else: cur[1] = p['frame']
    elif cur is not None: runs.append(cur); cur = None
if cur is not None: runs.append(cur)
runs = sorted(runs, key=lambda r: -(r[1] - r[0]))
res = dict(frames=len(per), frames_clear=int(sum(p['clear'] for p in per)), frames_head_head=int(sum(1 for p in per if p['head_head'])), frames_head_body=int(sum(1 for p in per if p['head_body'])),
           median_head_body_pairs=float(np.median([len(p['head_body']) for p in per])) if per else 0.0, longest_clear_runs=runs[:8], head_fraction=hfrac, touch_px=touch)
res['per_frame'] = [dict(frame=p['frame'], walkers=p['walkers'], head_head=p['head_head'], head_body=p['head_body']) for p in per]
json.dump(res, open(out, 'w'))
print(json.dumps({k: v for k, v in res.items() if k != 'per_frame'}))
