# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: how far do neighbouring shells (trouser cuff / shoe collar) drift apart at the ankle in the crowd's own walk clips?

For every pair of welded vertices within 2 cm of each other at rest inside the ankle zone (y 0.03 .. 0.20 m, the pairs across shells included) the
posed distance minus the rest distance is measured on every sampled frame of the citizen's own walk style and idle (GPU skinning: top-4 influences).
Prints per citizen: pairs, worst opening (mm), 95th percentile of the worst opening (mm), pairs that open more than 5 mm.

  python3 tools/ue_char/eval/ankle_gap.py [--dir DIR_WITH_final_npz] NAME [NAME ...]      (default dir: <scratch>/eval/refit; needs $P2_SCRATCH)
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
import weights_r6 as W   # noqa: E402
from eval_r6 import CIT_WALK  # noqa: E402

a = sys.argv[1:]; d = scr('eval', 'refit')
if '--dir' in a:
    i = a.index('--dir'); d = a[i + 1]; a = a[:i] + a[i + 2:]
tot = {}
for name in a:
    z = np.load(os.path.join(d, name + '_final.npz'))
    pos, dense, welded = z['pos'], z['dense'], z['welded']
    nu = welded.max() + 1
    first = np.zeros(nu, int); first[welded[::-1]] = np.arange(len(welded))[::-1]
    Pu = pos[first]; Du = dense[first]
    idx = z['idx']; Fu = welded[idx]
    rows = np.concatenate([Fu[:, 0], Fu[:, 1], Fu[:, 2]]); cols = np.concatenate([Fu[:, 1], Fu[:, 2], Fu[:, 0]])
    _, comp = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(nu, nu)), directed=False)
    zone = np.where((Pu[:, 1] > 0.03) & (Pu[:, 1] < 0.20))[0]
    tr = cKDTree(Pu[zone]); pr = np.array(sorted(tr.query_pairs(0.02)))
    if len(pr): pr = pr[comp[zone[pr[:, 0]]] != comp[zone[pr[:, 1]]]]      # only pairs ACROSS shells (cuff vs collar), not stretched cloth inside one shell
    if len(pr) == 0: print(name, 'no cross-shell pairs'); continue
    I = zone[pr[:, 0]]; J = zone[pr[:, 1]]
    rest = np.linalg.norm(Pu[I] - Pu[J], axis=1)
    clip = CIT_WALK.get(name, 'walk')
    Ms = [CP.rig().mats(clip, f) for f in range(0, CP.rig().clip_len(clip), 2)] + [CP.rig().mats('idle', 0)]
    top = np.argsort(-Du, axis=1)[:, :4]; w = np.take_along_axis(Du, top, 1); w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    Ph = np.c_[Pu, np.ones(len(Pu))]
    worst = np.full(len(I), -1e9)
    for M in Ms:
        Q = np.zeros((len(Pu), 3))
        for k in range(4): Q += w[:, k:k + 1] * np.einsum('nij,nj->ni', M[top[:, k]], Ph)
        worst = np.maximum(worst, np.linalg.norm(Q[I] - Q[J], axis=1) - rest)
    r = dict(name=name, pairs=int(len(I)), worst_mm=round(float(worst.max() * 1000), 1), p95_mm=round(float(np.percentile(worst, 95) * 1000), 1), over_5mm=int((worst > 0.005).sum()), over_10mm=int((worst > 0.010).sum()))
    print(json.dumps(r)); tot[name] = r
print('TOTAL over_5mm', sum(r['over_5mm'] for r in tot.values()), 'over_10mm', sum(r['over_10mm'] for r in tot.values()), 'worst_mm', max(r['worst_mm'] for r in tot.values()))
