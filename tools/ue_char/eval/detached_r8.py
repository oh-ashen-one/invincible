# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: detached polygons in the silhouette of a posed citizen ('shoe shards', critic r07): connected components of the person mask that are NOT the main body, per frame of
the citizen's own walk clip and per view, with the triangles that draw them (two-channel id buffer) so the culprit geometry can be found in the rest pose.

  python3 tools/ue_char/eval/detached_r8.py [--ppm 700] [--yaws 8] [--step 2] [--max-px 120] [--json OUT] NAME [NAME ...]
"""
import os, sys, json
import numpy as np
import cv2
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import cit_proxy as CP   # noqa: E402
import eval_r6 as E      # noqa: E402
a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return type(d)(v)
    return d
ppm = opt('--ppm', 700); yaws = opt('--yaws', 8); step = opt('--step', 2); maxpx = opt('--max-px', 120); js = opt('--json', '')
out = {}
for name in a:
    m = E.load_r6(name)
    clip = E.CIT_WALK.get(name, 'walk')
    frames = [(clip, f) for f in range(0, CP.rig().clip_len(clip), step)]
    Pws = [m.posed(c, f) for c, f in frames]
    W, H, ox, oy = CP.frame_view(Pws, ppm)
    T = m.T
    lo = np.arange(len(T)) & 255; hi = (np.arange(len(T)) >> 8) & 255
    tri_hits = {}; events = []
    for (c, f), Pw in zip(frames, Pws):
        for k in range(yaws):
            yaw = 360.0 * k / yaws
            _, mask, g1 = CP.raster(Pw, T, m.uv, None, yaw, ppm, W, H, ox, oy, colour=False, gid=lo)
            _, _, g2 = CP.raster(Pw, T, m.uv, None, yaw, ppm, W, H, ox, oy, colour=False, gid=hi)
            lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
            if n < 2: continue
            sizes = ndimage.sum(mask, lab, range(1, n + 1))
            main = int(np.argmax(sizes)) + 1
            for i in range(1, n + 1):
                if i == main or sizes[i - 1] > maxpx: continue
                ys, xs = np.nonzero(lab == i)
                ids = g1[ys, xs].astype(int) | (g2[ys, xs].astype(int) << 8)
                u, cnt = np.unique(ids, return_counts=True)
                for t, cc in zip(u, cnt): tri_hits[int(t)] = tri_hits.get(int(t), 0) + int(cc)
                events.append(dict(frame=f, yaw=yaw, px=int(sizes[i - 1]), tris=[int(t) for t in u[:6]], y_m=float((oy - ys.mean()) / ppm)))
    top = sorted(tri_hits.items(), key=lambda kv: -kv[1])[:12]
    info = []
    for t, cc in top:
        v = m.T[t]; P = m.P[v]
        info.append(dict(tri=t, hits_px=cc, centre=[round(float(x), 3) for x in P.mean(0)], edge_cm=round(float(max(np.linalg.norm(P[0] - P[1]), np.linalg.norm(P[1] - P[2]), np.linalg.norm(P[2] - P[0])) * 100), 2),
                         weights=[[int(b) for b in np.argsort(-m.dense[q])[:2]] for q in v]))
    out[name] = dict(detached_events=len(events), frames_affected=len({e['frame'] for e in events}), max_px=max([e['px'] for e in events], default=0), worst_tris=info, sample=events[:6])
    print(name, json.dumps(dict(events=len(events), frames=len({e['frame'] for e in events}), max_px=out[name]['max_px'], worst=info[:4])))
if js: json.dump(out, open(js, 'w'), indent=1)
