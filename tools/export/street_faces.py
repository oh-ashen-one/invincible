"""Street-face records for the street-level kit: every ground-floor face (tier 0, with storefront zone) of the exported facade meshes.
Face frame (browser metres): point(u, y) = O + T * u + (0, y, 0) + N * n. Also: gH (storefront zone height), W (face width), style
(1 punched / 2 curtain / 3 ribbon / 4 deco), seed, kind (footprint kind: loft / walkup / glass / deco ...), h (building height)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import read_glb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from citypaths import EXPORT as _EXPORT
EXPORT = _EXPORT.rstrip('/') + '/'

def load_faces(export=EXPORT):
    man = json.load(open(export + 'manifest.json')); lay = json.load(open(export + 'layout.json'))
    foot = lay['footprints']
    faces = []
    for rec in man['meshes']:
        if rec['name'] != 'facade': continue
        g = read_glb(export + rec['file']); A = g['attrs']
        P = A['POSITION'] + np.array([rec['center'][0], 0.0, rec['center'][2]])
        N = A['NORMAL']; U = A['TEXCOORD_0']; S = A['TEXCOORD_3']; S2 = A['TEXCOORD_4']; Wv = A['TEXCOORD_5']; W2 = A['TEXCOORD_6']
        tri = g['index'].reshape(-1, 3)
        # one record per (seed, tier, plane): vertices of the quad(s) that touch y = 0
        groups = {}
        for t in tri:
            if not (P[t, 1].min() < 0.05 and abs(N[t[0], 1]) < 0.3): continue
            a = t[0]
            if int(S[a, 0] // 256) != 0: continue
            key = (round(S[a, 1], 4), round(float(N[a, 0]), 2), round(float(N[a, 2]), 2), round(float(P[a, 0] * N[a, 0] + P[a, 2] * N[a, 2]), 1))
            groups.setdefault(key, []).append(t)
        for key, ts in groups.items():
            vi = np.unique(np.concatenate(ts)); a = vi[0]
            if S2[a, 0] <= 0.0 or S2[a, 1] < 0.5: continue  # no storefront zone / no window style
            # tangent: from two vertices with different u
            u = U[vi, 0]; i0, i1 = vi[np.argmin(u)], vi[np.argmax(u)]
            if u.max() - u.min() < 1.0: continue
            T = (P[i1] - P[i0]) / (U[i1, 0] - U[i0, 0]); T[1] = 0.0; T /= np.linalg.norm(T)
            O = P[i0] - T * U[i0, 0]; O[1] = 0.0
            n = np.array([N[a, 0], 0.0, N[a, 2]]); n /= np.linalg.norm(n)
            cx, cz = P[vi, 0].mean(), P[vi, 2].mean()
            kind, h = 'other', 0.0
            best = 1e9
            for f in foot:  # footprint whose boundary contains this face
                if f['x0'] - 1.0 <= cx <= f['x1'] + 1.0 and f['z0'] - 1.0 <= cz <= f['z1'] + 1.0:
                    d = min(abs(cx - f['x0']), abs(cx - f['x1']), abs(cz - f['z0']), abs(cz - f['z1']))
                    if d < best: best, kind, h = d, f.get('kind', 'other'), f['h']
            faces.append({'tile': rec['tile'], 'O': [float(O[0]), float(O[2])], 'T': [float(T[0]), float(T[2])], 'N': [float(n[0]), float(n[2])],
                          'u0': float(u.min()), 'u1': float(u.max()), 'W': float(Wv[a, 0]), 'gH': float(S2[a, 0]), 'style': float(S2[a, 1]), 'seed': float(S[a, 1]),
                          'Lw': float(S[a, 0]), 'topY': float(Wv[a, 1]), 'kind': kind, 'h': float(h), 'wz': float(W2[a, 0])})
    return faces

if __name__ == '__main__':
    F = load_faces()
    json.dump(F, open(os.path.join(EXPORT, 'street_faces.json'), 'w'))
    import collections
    print(len(F), 'faces', collections.Counter(f['kind'] for f in F), collections.Counter(int(f['style']) for f in F))
    print(collections.Counter((round(f['N'][0]), round(f['N'][1])) for f in F))
    av = [f for f in F if abs(f['N'][0]) > 0.9 and (abs(f['O'][0] - 234) < 1 or abs(f['O'][0] - 266) < 1)]
    for f in sorted(av, key=lambda f: (f['N'][0], -f['O'][1])): print(' ', round(f['N'][0]), 'z', round(f['O'][1] + f['T'][1] * f['u0'], 1), '..', round(f['O'][1] + f['T'][1] * f['u1'], 1), 'W', round(f['W'], 1), 'gH', f['gH'], 'style', f['style'], f['kind'], f['h'])
