# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: per-frame walker silhouettes of the crowd tracking shot from the id movie (tools/ue_char/crowd/id_movie.sh).

  python3 tools/ue_char/crowd/id_overlap.py FRAMES_DIR OUT.json [--first 36] [--count 444] [--min-px 120]

Id colour decode: each channel level 0 / ~.5 / 1 of the tonemapped output -> digit 0 / 1 / 2 (thresholds 90 / 200), id = r + 3 g + 9 b (1..18), black = background.
Per frame: visible walkers (distinct ids with >= --min-px pixels), and `contacts` = pairs of ids whose visible regions touch (within 2 px): two silhouettes that meet on the
screen, i.e. one person in front of another (depth occlusion) or side by side; it is NOT a 3D intersection (that is the telemetry: telemetry_check.py).
--touch N = how many px apart two silhouettes may be and still count as touching (default 2).  Frames default to 36 .. 479 of the run = the trimmed crowd_tracking.mp4 (0.6 s .. 8 s)."""
import sys, os, json, glob
import numpy as np
import cv2
from scipy import ndimage
a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return type(d)(v)
    return d
first = opt('--first', 36); count = opt('--count', 444); minpx = opt('--min-px', 120); touch = opt('--touch', 2)
fdir, out = a[:2]
per = []
for f in range(first, first + count):
    p = os.path.join(fdir, 'MovieFrame%05d.png' % f)
    if not os.path.exists(p): continue
    im = cv2.imread(p)[..., ::-1].astype(int)
    lev = np.where(im > 200, 2, np.where(im > 90, 1, 0))
    ids = lev[..., 0] + 3 * lev[..., 1] + 9 * lev[..., 2]
    ids[(im.max(axis=2) < 40)] = 0
    present = {}
    for i in np.unique(ids):
        if i == 0: continue
        n = int((ids == i).sum())
        if n >= minpx: present[int(i)] = n
    contacts = []
    keys = sorted(present)
    masks = {i: ids == i for i in keys}
    for x in range(len(keys)):
        for y in range(x + 1, len(keys)):
            if (ndimage.binary_dilation(masks[keys[x]], iterations=touch) & masks[keys[y]]).any():
                contacts.append((keys[x], keys[y]))
    per.append(dict(frame=f, visible=len(present), contacts=contacts, px=present))
res = dict(frames=len(per), first=first, visible_median=float(np.median([p['visible'] for p in per])), visible_min=int(min(p['visible'] for p in per)), visible_max=int(max(p['visible'] for p in per)),
           frames_with_contact=int(sum(1 for p in per if p['contacts'])), max_contacts=int(max(len(p['contacts']) for p in per)),
           median_contacts=float(np.median([len(p['contacts']) for p in per])))
res['per_frame'] = [dict(frame=p['frame'], visible=p['visible'], contacts=p['contacts']) for p in per]
json.dump(res, open(out, 'w'))
print(json.dumps({k: v for k, v in res.items() if k != 'per_frame'}))
