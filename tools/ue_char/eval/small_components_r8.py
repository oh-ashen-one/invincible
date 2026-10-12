# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: small detached person components (shards) in chroma-key stills.  Person = every pixel that is not within --tol of the key colour (the modal corner colour);
components are 8-connected; a shard = a component of <= --max-px pixels that is not the largest one touching... (any component <= max-px is listed, with its owner id when an id still is given).

  python3 tools/ue_char/eval/small_components_r8.py KEY.png [KEY2.png ...] [--max-px 200] [--tol 14] [--json OUT]"""
import sys, json, os
import numpy as np, cv2
from scipy import ndimage as ndi
a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return type(d)(v)
    return d
maxpx = opt('--max-px', 200); tol = opt('--tol', 14); js = opt('--json', '')
out = {}
for f in a:
    im = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    rgb = (im[..., 2::-1] if im.shape[2] == 4 else im[..., ::-1]).astype(int)
    H, W = rgb.shape[:2]
    corners = np.concatenate([rgb[:20, :20].reshape(-1, 3), rgb[-20:, :20].reshape(-1, 3), rgb[:20, -20:].reshape(-1, 3), rgb[-20:, -20:].reshape(-1, 3)])
    vals, cnt = np.unique(corners, axis=0, return_counts=True); keyc = vals[np.argmax(cnt)]
    key = (np.abs(rgb - keyc) <= tol).all(-1)
    lab, n = ndi.label(~key, structure=np.ones((3, 3)))
    sizes = ndi.sum(~key, lab, range(1, n + 1)); objs = ndi.find_objects(lab)
    small = []
    for i in range(n):
        if sizes[i] <= maxpx:
            sl = objs[i]; small.append(dict(px=int(sizes[i]), x=int(sl[1].start), y=int(sl[0].start), w=int(sl[1].stop - sl[1].start), h=int(sl[0].stop - sl[0].start)))
    small.sort(key=lambda s: -s['px'])
    out[os.path.basename(f)] = dict(key_rgb=[int(v) for v in keyc], person_components=int(n), components_le_max=len(small), over_4px=sum(1 for s in small if s['px'] > 4), list=small[:30])
    print(os.path.basename(f), json.dumps(dict(components_le_max=len(small), over_4px=sum(1 for s in small if s['px'] > 4), largest_small=small[:4])))
if js: json.dump(out, open(js, 'w'), indent=1)
