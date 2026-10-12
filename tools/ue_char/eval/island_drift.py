# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: detached polygons.  A citizen mesh is a set of connected pieces (main shell + small islands: eyes, teeth, buckles, hem patches).  A piece that is
skinned away from the body in some frame of a clip is a polygon floating in the air.  For every non-main piece the distance from its posed centroid to the nearest posed vertex of
the main shell is measured on every frame of every clip the crowd uses (top-4 skinning, like the GPU) and compared with the rest-pose distance.

  python3 tools/ue_char/eval/island_drift.py [--min-drift-cm 3] NAME [NAME ...]        prints one line per island that drifts more than the threshold
"""
import os, sys, json
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from p2paths import scr  # noqa: E402
import cit_proxy as CP   # noqa: E402

a = sys.argv[1:]; thr = 3.0
if '--min-drift-cm' in a:
    i = a.index('--min-drift-cm'); thr = float(a[i + 1]); a = a[:i] + a[i + 2:]
bad = 0
for name in a:
    z = np.load(os.path.join(scr('eval', 'refit'), name + '_final.npz'))
    pos, idx, dense, welded = z['pos'], z['idx'], z['dense'], z['welded']
    nu = welded.max() + 1; first = np.zeros(nu, int); first[welded[::-1]] = np.arange(len(welded))[::-1]
    Pu, Du = pos[first], dense[first]; Fu = welded[idx]
    rows = np.concatenate([Fu[:, 0], Fu[:, 1], Fu[:, 2]]); cols = np.concatenate([Fu[:, 1], Fu[:, 2], Fu[:, 0]])
    _, comp = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(nu, nu)), directed=False)
    used = np.unique(Fu); cnt = np.bincount(comp[used]); main = int(np.argmax(cnt))
    main_v = np.where((comp == main))[0]
    top = np.argsort(-Du, axis=1)[:, :4]; w = np.take_along_axis(Du, top, 1); w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    Ph = np.c_[Pu, np.ones(len(Pu))]
    islands = [c for c in range(len(cnt)) if cnt[c] > 0 and c != main]
    drift = {c: 0.0 for c in islands}; where = {c: None for c in islands}
    rest_d = {}
    tree0 = cKDTree(Pu[main_v])
    for c in islands:
        v = np.where(comp == c)[0]; rest_d[c] = float(tree0.query(Pu[v].mean(0))[0])
    R = CP.rig()
    for clip in CP.CLIPS_USED:
        for f in range(R.clip_len(clip)):
            M = R.mats(clip, f); Q = np.zeros((len(Pu), 3))
            for k in range(4): Q += w[:, k:k + 1] * np.einsum('nij,nj->ni', M[top[:, k]], Ph)
            tr = cKDTree(Q[main_v])
            for c in islands:
                v = np.where(comp == c)[0]; d = float(tr.query(Q[v].mean(0))[0])
                if d - rest_d[c] > drift[c]: drift[c] = d - rest_d[c]; where[c] = (clip, f)
    for c in islands:
        if drift[c] * 100 > thr:
            bad += 1
            v = np.where(comp == c)[0]
            print(json.dumps(dict(name=name, tris=int(cnt[c]), centre_rest=[round(float(x), 3) for x in Pu[v].mean(0)], rest_dist_cm=round(rest_d[c] * 100, 1),
                                  max_drift_cm=round(drift[c] * 100, 1), at=where[c], bones=[int(b) for b in np.unique(np.argmax(Du[v], 1))])))
print('islands drifting more than %.0f cm: %d' % (thr, bad))
