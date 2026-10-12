#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A), round 02: split the exported meshes that traversal r20 would de-collide as "giant" into <= 256 m pieces.

WebTravWorld.cpp (round 20, SolidMode 2) switches collision OFF for any component wider than 400 m whose top is above 20 m (far-skyline
rule). The exporter cuts far-layer meshes into 2,048 m tiles, so the bridges (bridgeDeck / Steel / Stone / Truss / Cables) and the
river seawalls (seawall_parkwall) came out as 1.4 km components: drawn, inside M1 (the Queensboro approach starts at x 261 m, the
west seawall runs along the M1 edge), and pass-through for the hero. This script cuts each such mesh into pieces on a 256 m grid
(long triangles are subdivided first so no piece exceeds its cell by more than ~64 m), keeps the record's centre (positions stay
relative to it), and replaces the record in manifest.json by its pieces (`<base>_p<k>`, `split_from`). Idempotent: split records and
far-prefixed meshes (SM_far*: scenery by name) are skipped; the original manifest is kept as manifest.pre_split.json.

    python3 tools/export/split_giants.py <export_dir>"""
import json, math, os, shutil, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glbio import read_glb, write_glb

GIANT_W, GIANT_Z, CELL, MAX_EDGE = 400.0, 20.0, 256.0, 64.0
EXCL = ('sign', 'screen', 'tsframes', 'tsticker', 'tsneon', 'tslights', 'tsvinyl', 'tshalo', 'tsbands', 'tstkts', 'billboard', 'neon', 'glow',
        'streetkit', 'streetprop', '_prop', 'prop_', 'trees', 'tree_', '_tree', 'crown', 'clump', 'leaf', 'leaves', 'foliage', 'canopy', 'bush',
        'traffic', 'crowd', 'vehicle', 'hydrant', 'lamp', 'decal', 'halo', 'spill', 'grime', 'wear', 'dust', 'markings')


def subdivide(A, I):
    """split every triangle whose longest horizontal edge > MAX_EDGE at that edge's midpoint (all attributes interpolated linearly)"""
    A = {k: [v] for k, v in A.items()}; n = len(A['POSITION'][0]); T = [tuple(t) for t in I.reshape(-1, 3)]
    P = A['POSITION'][0]
    get = lambda k, i: (A[k][0][i] if i < len(A[k][0]) else extra[k][i - len(A[k][0])])
    extra = {k: [] for k in A}
    out = []
    while T:
        a, b, c = T.pop()
        pa, pb, pc = get('POSITION', a), get('POSITION', b), get('POSITION', c)
        e = [(np.hypot(*(pa - pb)[[0, 2]]), a, b, c), (np.hypot(*(pb - pc)[[0, 2]]), b, c, a), (np.hypot(*(pc - pa)[[0, 2]]), c, a, b)]
        L, u, v, w = max(e, key=lambda q: q[0])
        if L <= MAX_EDGE: out.append((a, b, c)); continue
        m = n + len(extra['POSITION'])
        for k in A: extra[k].append((get(k, u) + get(k, v)) / 2.0)
        # keep the winding: (u, v, w) is a rotation of (a, b, c)
        T.append((u, m, w)); T.append((m, v, w))
    for k in A:
        if extra[k]: A[k] = np.concatenate([A[k][0], np.array(extra[k])])
        else: A[k] = A[k][0]
    return A, np.array(out, np.int64)


def trav_excluded(name): n = name.lower(); return any(k in n for k in EXCL)


def main():
    E = sys.argv[1]
    mp = os.path.join(E, 'manifest.json'); M = json.load(open(mp))
    if not os.path.exists(os.path.join(E, 'manifest.pre_split.json')): shutil.copy(mp, os.path.join(E, 'manifest.pre_split.json'))
    out, rep = [], []
    for r in M['meshes']:
        base = os.path.basename(r['file'])[:-4]
        if r.get('split_from') or r['name'].startswith('far') or r['kind'] in ('signage', 'markings') or trav_excluded('SM_' + base):
            out.append(r); continue
        g = read_glb(os.path.join(E, r['file'])); A = g['attrs']; P = A['POSITION']
        c = r.get('center') or [0, 0, 0]
        w = max(P[:, 0].max() - P[:, 0].min(), P[:, 2].max() - P[:, 2].min())
        if not (w > GIANT_W and P[:, 1].max() > GIANT_Z):
            out.append(r); continue
        A, T = subdivide(A, g['index'])
        P = A['POSITION']; C = P[T].mean(1)
        key = np.floor((C[:, 0] + c[0]) / CELL).astype(int) * 100000 + np.floor((C[:, 2] + c[2]) / CELL).astype(int)
        pieces = []
        for k, kv in enumerate(np.unique(key)):
            TT = T[key == kv]; used = np.unique(TT); remap = -np.ones(len(P), np.int64); remap[used] = np.arange(len(used))
            sub = {n: v[used] for n, v in A.items()}
            pb = f'{base}_p{k}'; pf = os.path.join(os.path.dirname(r['file']), pb + '.glb')
            write_glb(os.path.join(E, pf), sub, remap[TT].reshape(-1), pb)
            Q = sub['POSITION']; pw = max(Q[:, 0].max() - Q[:, 0].min(), Q[:, 2].max() - Q[:, 2].min())
            nr = dict(r); nr.update({'file': pf, 'split_from': r['file'], 'verts': int(len(used)), 'tris': int(len(TT))})
            out.append(nr); pieces.append(round(float(pw), 1))
        rep.append({'file': r['file'], 'width_m': round(float(w), 1), 'top_m': round(float(P[:, 1].max()), 1), 'pieces': len(pieces), 'max_piece_width_m': max(pieces),
                    'giant_pieces_left': sum(1 for p in pieces if p > GIANT_W)})
    M['meshes'] = out
    json.dump(M, open(mp, 'w'))
    json.dump(rep, open(os.path.join(E, 'split_giants.json'), 'w'), indent=1)
    for x in rep: print(x)
    print('split', len(rep), 'meshes')


if __name__ == '__main__':
    main()
