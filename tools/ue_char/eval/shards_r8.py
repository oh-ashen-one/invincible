# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08 (critic r07: 'shoe shards of 29 and 19 px'): drop the tiny triangles that show up as DETACHED polygons in a citizen's silhouette during its own walk clip.

The skater's crumpled shoe collar (raw Tripo mesh) has 1-cm triangles whose shin / foot weight mix makes them drift away from the shoe in some frames: in the chroma-key still they are loose
dark leaf shapes of 19-31 px beside the heel.  For every citizen: pose the welded mesh with its own clip (top-4 skinning, like the GPU), draw the silhouette from 8 yaws, find the
connected components of the mask that are not the main body (<= --max-px), collect the triangles that draw them, and delete those of area <= --max-area-cm2 (repeat --rounds times).
The triangles are only removed from the index list (no vertex moves).  Rewrites <scratch>/eval/refit/NAME_final.npz in place; <scratch>/eval/refit/NAME_shards.json records what went.

  python3 tools/ue_char/eval/shards_r8.py [--ppm 700] [--yaws 8] [--step 2] [--max-px 160] [--max-area-cm2 2.5] [--rounds 3] [--cap 60] NAME [NAME ...]
"""
import os, sys, json
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from p2paths import scr  # noqa: E402
import cit_proxy as CP   # noqa: E402
import eval_r6 as E      # noqa: E402
a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return type(d)(v)
    return d
ppm = opt('--ppm', 700); yaws = opt('--yaws', 8); step = opt('--step', 2); maxpx = opt('--max-px', 160); maxarea = opt('--max-area-cm2', 2.5) * 1e-4; rounds = opt('--rounds', 3); cap = opt('--cap', 60)


def detached_tris(m, clip, step, ppm, yaws, maxpx):
    frames = [(clip, f) for f in range(0, CP.rig().clip_len(clip), step)]
    Pws = [m.posed(c, f) for c, f in frames]
    W, H, ox, oy = CP.frame_view(Pws, ppm)
    T = m.T; lo = np.arange(len(T)) & 255; hi = (np.arange(len(T)) >> 8) & 255
    hits = {}; events = 0
    for (c, f), Pw in zip(frames, Pws):
        for k in range(yaws):
            yaw = 360.0 * k / yaws
            _, mask, g1 = CP.raster(Pw, T, m.uv, None, yaw, ppm, W, H, ox, oy, colour=False, gid=lo)
            lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
            if n < 2: continue
            _, _, g2 = CP.raster(Pw, T, m.uv, None, yaw, ppm, W, H, ox, oy, colour=False, gid=hi)
            sizes = ndimage.sum(mask, lab, range(1, n + 1)); main = int(np.argmax(sizes)) + 1
            for i in range(1, n + 1):
                if i == main or sizes[i - 1] > maxpx: continue
                events += 1
                ys, xs = np.nonzero(lab == i)
                ids = g1[ys, xs].astype(int) | (g2[ys, xs].astype(int) << 8)
                for t in np.unique(ids): hits[int(t)] = hits.get(int(t), 0) + 1
    return hits, events


for name in a:
    path = os.path.join(scr('eval', 'refit'), name + '_final.npz')
    z = dict(np.load(path))
    m = E.load_r6(name)
    clip = E.CIT_WALK.get(name, 'walk')
    removed = []; log = []
    for r in range(rounds):
        hits, ev = detached_tris(m, clip, step, ppm, yaws, maxpx)
        area = np.linalg.norm(np.cross(m.P[m.T[:, 1]] - m.P[m.T[:, 0]], m.P[m.T[:, 2]] - m.P[m.T[:, 0]]), axis=1) / 2
        cand = [t for t, c in sorted(hits.items(), key=lambda kv: -kv[1]) if area[t] <= maxarea]
        log.append(dict(round=r, detached_events=ev, candidates=len(cand)))
        if not cand or len(removed) >= cap: break
        cand = cand[:max(0, cap - len(removed))]
        keep = np.ones(len(m.T), bool); keep[cand] = False
        removed += cand
        m.T = m.T[keep]; m.n_garment_tris = len(m.T)
    hits, ev = detached_tris(m, clip, step, ppm, yaws, maxpx)
    log.append(dict(round='final', detached_events=ev))
    z['idx'] = m.T
    np.savez_compressed(path, **z)
    json.dump(dict(name=name, removed=len(removed), log=log), open(os.path.join(scr('eval', 'refit'), name + '_shards.json'), 'w'))
    print(name, json.dumps(dict(removed=len(removed), log=log)))
