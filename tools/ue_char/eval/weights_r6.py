# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 06 (CH18): final skin weights of the refit citizens (welded vertices), measured on the crowd's own clips.

Input  <scratch>/eval/refit/NAME.npz         (refit.py: rest-pose mesh + transferred weights, seam duplicates share them)
Output <scratch>/eval/refit/NAME_final.npz   pos, nrm, uv, idx, dense (top-4, nv x 18), plus stats

Steps on the welded vertices (uv-seam duplicates are one vertex, so they can never diverge again):
  1. abutting-shell smoothing (underlayer.smooth_weights: pieces that touch move together)
  2. free-hanging skirt rig (underlayer.skirt_weights: coat tails / dress panels follow the thighs as one piece)
  3. stretch relaxation: any edge whose length grows more than STRETCH_REL x + STRETCH_ABS in a sampled frame of the crowd walk / idle clips gets
     its two vertices' weights pulled toward their neighbours' average (repeat until no edge is over the limit or ITERS is used up)
  4. keep the 4 strongest bones (the GPU limit) BEFORE measuring, and re-measure after the truncation.

  python3 tools/ue_char/eval/weights_r6.py NAME [NAME ...]
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from p2paths import scr  # noqa: E402
import underlayer as U   # noqa: E402
import cit_proxy as CP   # noqa: E402

OUT = scr('eval', 'refit')
REL = float(os.environ.get('STRETCH_REL', '0.30'))
ABS = float(os.environ.get('STRETCH_ABS', '0.010'))
ITERS = int(os.environ.get('STRETCH_ITERS', '60'))
ALPHA = float(os.environ.get('STRETCH_ALPHA', '0.5'))
SKIRT = os.environ.get('SKIRTW', '1') != '0'
SMOOTH = os.environ.get('SMOOTHW', '1') != '0'
ANKLE = os.environ.get('ANKLEW', '1') != '0'      # round 07: skin gradient across the ankle so trouser cuff and shoe collar move together
ANKLE_R = float(os.environ.get('ANKLE_R', '0.11'))     # radius (m) around the ankle joint that gets the gradient
ANKLE_LO = float(os.environ.get('ANKLE_LO', '-0.035'))  # gradient starts this far below the joint (all foot) ...
ANKLE_HI = float(os.environ.get('ANKLE_HI', '0.05'))    # ... and ends this far above it (all shin)
BONES_L = (12, 13, 0.097, 0.081, -0.03)    # shinL, footL, ankle joint (x, y, z) of the crowd rig (people.json)
BONES_R = (15, 16, -0.097, 0.081, -0.03)


def top4(d):
    top = np.argsort(-d, axis=1)[:, :4]
    tw = np.take_along_axis(d, top, 1); tw /= np.maximum(tw.sum(1, keepdims=True), 1e-9)
    out = np.zeros_like(d); np.put_along_axis(out, top, tw, 1)
    return out


def edges_of(F, n):
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e = np.sort(e, axis=1)
    e = e[e[:, 0] != e[:, 1]]
    return np.unique(e, axis=0)


def opposite_leg_flags(P, D, E, rings=3):
    """A triangle that joins a vertex of the left leg to one of the right leg below the crotch is a coat / dress / skirt panel (trouser legs are separate
    tubes): flag both ends and `rings` rings of neighbours so the whole panel gets the skirt rig."""
    Lw = D[:, [11, 12, 13]].sum(1); Rw = D[:, [14, 15, 16]].sum(1)
    a, b = E[:, 0], E[:, 1]
    bad = (((Lw[a] > 0.5) & (Rw[b] > 0.5)) | ((Rw[a] > 0.5) & (Lw[b] > 0.5))) & (P[a, 1] < 0.85) & (P[b, 1] < 0.85)
    fl = np.zeros(len(P), bool); fl[E[bad].ravel()] = True
    for _ in range(rings):
        nf = fl.copy(); nf[E[fl[E[:, 0]], 1]] = True; nf[E[fl[E[:, 1]], 0]] = True
        fl = nf & (P[:, 1] < 0.9)
    return fl


def ankle_blend(P, D):
    """Round 07 (ankle gaps): in the crowd rig the shin bone ends and the foot bone starts at ONE height (the ankle joint, y = 0.081), so a trouser cuff
    (100 % shin) and the shoe collar right below it (100 % foot) are two shells that touch at rest and separate as soon as the foot pitches
    (`crowd_key_tracking_4k`: a sliver between the cuff and the collar).  Every vertex of a leg within ANKLE_R of the joint gets a smooth shin <-> foot gradient over
    [joint + ANKLE_LO, joint + ANKLE_HI] (height only), so both shells carry the same weights at the same height and move together.  The total weight the vertex gives
    to the two bones is kept; other bones are untouched."""
    D = D.copy(); n = 0
    for sh, ft, jx, jy, jz in (BONES_L, BONES_R):
        leg = D[:, sh] + D[:, ft]
        d = np.linalg.norm(P - np.array([jx, jy, jz]), axis=1)
        sel = (leg > 0.5) & (d < ANKLE_R) & (P[:, 1] > jy + ANKLE_LO - 0.02)
        t = np.clip((P[:, 1] - (jy + ANKLE_LO)) / (ANKLE_HI - ANKLE_LO), 0.0, 1.0)
        t = t * t * (3 - 2 * t)                              # smoothstep: 0 = all foot, 1 = all shin
        blend = np.clip(t, 0.0, 1.0)
        # never move weight toward a bone the vertex did not use at all AND sits on the other side of the joint from it
        newS = leg * blend; newF = leg * (1 - blend)
        D[sel, sh] = newS[sel]; D[sel, ft] = newF[sel]
        n += int(sel.sum())
    return D, n


def sample_frames(clips=CP.CLIPS_USED, every=2):
    r = CP.rig(); out = []
    for cn in clips:
        if cn not in r.p['clips']: continue
        for f in range(0, r.clip_len(cn), every): out.append(r.mats(cn, f))
    return np.array(out)                                  # (nf, nb, 3, 4)


def worst_edge_growth(P, E, dense, Ms):
    """(len(E),) max over frames of posed length - rest length; dense is truncated to 4 influences like the GPU."""
    d4 = top4(dense)
    Ph = np.c_[P, np.ones(len(P))]
    rest = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
    idx = np.argsort(-d4, axis=1)[:, :4]; w = np.take_along_axis(d4, idx, 1)
    worst = np.full(len(E), -1e9)
    for M in Ms:
        Q = np.zeros((len(P), 3))
        for k in range(4): Q += w[:, k:k + 1] * np.einsum('nij,nj->ni', M[idx[:, k]], Ph)
        ln = np.linalg.norm(Q[E[:, 0]] - Q[E[:, 1]], axis=1)
        worst = np.maximum(worst, ln - rest)
    return worst, rest


def relax(P, E, dense, Ms, log=print):
    n = len(P)
    A = np.zeros(n); nb_ = [[] for _ in range(n)]
    for a, b in E: nb_[a].append(b); nb_[b].append(a)
    nbs = [np.array(x, int) for x in nb_]
    hist = []
    for it in range(ITERS):
        worst, rest = worst_edge_growth(P, E, dense, Ms)
        bad = worst > REL * rest + ABS
        hist.append(int(bad.sum()))
        if not bad.any(): break
        bv = np.unique(E[bad].ravel())
        new = dense.copy()
        for v in bv:
            if len(nbs[v]): new[v] = (1 - ALPHA) * dense[v] + ALPHA * dense[nbs[v]].mean(0)
        dense = top4(new / new.sum(1, keepdims=True))
    worst, rest = worst_edge_growth(P, E, dense, Ms)
    hist.append(int((worst > REL * rest + ABS).sum()))
    return dense, hist


def process(name, log=print):
    z = np.load(os.path.join(OUT, name + '.npz'))
    pos, nrm, uv, idx, dense, welded = z['pos'], z['nrm'], z['uv'], z['idx'], z['dense'], z['welded']
    nu = welded.max() + 1
    first = np.zeros(nu, int); first[welded[::-1]] = np.arange(len(welded))[::-1]      # a representative vertex per welded id
    Pu = pos[first]; Du = dense[first]
    Nu = np.zeros((nu, 3)); np.add.at(Nu, welded, nrm); Nu /= np.linalg.norm(Nu, axis=1, keepdims=True) + 1e-12
    Fu = welded[idx]
    ok = (Fu[:, 0] != Fu[:, 1]) & (Fu[:, 1] != Fu[:, 2]) & (Fu[:, 0] != Fu[:, 2])
    Fu = Fu[ok]
    E = edges_of(Fu, nu)
    Ms = sample_frames()
    w0, r0 = worst_edge_growth(Pu, E, Du, Ms)
    st = dict(name=name, verts=int(len(pos)), welded=int(nu), tris=int(len(idx)), edges=int(len(E)),
              bad_before=int((w0 > REL * r0 + ABS).sum()), over_10cm_before=int((w0 > 0.10).sum()), max_growth_cm_before=float(w0.max() * 100))
    D = Du
    if SMOOTH: D = U.smooth_weights(Pu, Nu, D)
    fl = None
    if SKIRT: D, fl = U.skirt_weights(Pu, Nu, Fu, D, extra=opposite_leg_flags(Pu, D, E) if os.environ.get('SKIRT_TOPO', '1') == '1' else None)
    an = 0
    if ANKLE: D, an = ankle_blend(Pu, D)
    D = top4(D)
    w1, r1 = worst_edge_growth(Pu, E, D, Ms)
    st.update(bad_after_skirt=int((w1 > REL * r1 + ABS).sum()), skirt_verts=int(fl.sum()) if fl is not None else 0, ankle_verts=an)
    D, hist = relax(Pu, E, D, Ms)
    w2, r2 = worst_edge_growth(Pu, E, D, Ms)
    st.update(relax_hist=hist, bad_after=int((w2 > REL * r2 + ABS).sum()), over_5cm_after=int((w2 > 0.05).sum()), over_10cm_after=int((w2 > 0.10).sum()),
              max_growth_cm_after=float(w2.max() * 100))
    dense_out = D[welded]
    np.savez_compressed(os.path.join(OUT, name + '_final.npz'), pos=pos, nrm=nrm, uv=uv, idx=idx, dense=dense_out, welded=welded)
    log(json.dumps(st))
    return st


if __name__ == '__main__':
    allst = {}
    for n in sys.argv[1:]:
        allst[n] = process(n)
