# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Offline CPU views of a prepared street person's head / collar (round 08 mask + collar checks): view_prepared.py PREPARED_DIR NAME OUT_PREFIX [--yc 1.56]"""
import sys, os, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'suit8'))
import softrender as sr
d_, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
yc = float(sys.argv[sys.argv.index('--yc') + 1]) if '--yc' in sys.argv else 1.56
z = np.load('%s/Street%s_prepared.npz' % (d_, name)); P, N, UV, F = z['P'], z['N'], z['UV'], z['F']
keep = P[F][:, :, 1].mean(1) > yc - 0.2
im = cv2.imread('%s/Street%s_atlas.png' % (d_, name))[..., ::-1].astype(np.float32) / 255
im = cv2.resize(im, (2048, 2048), interpolation=cv2.INTER_AREA) ** 2.2
prim = sr.Prim(P, N, F[keep], UV=UV, tex=im, rough=0.7, spec=0.1)
views = {'front': ((0, yc, 1.0), (0, yc, 0.05)), 'side': ((0.9, yc, 0.4), (0, yc, 0.05)), 'q': ((0.5, yc, 0.9), (0, yc, 0.05)), 'back3': ((-0.6, yc - 0.03, -0.8), (0, yc - 0.03, 0.0))}
ims = []
for k in ('front', 'side', 'q'):
    eye, tgt = views[k]
    ims.append(sr.render([prim], sr.look_at(eye, tgt), 12, 900, 900, ssaa=2))
sr.save(np.concatenate(ims, 1), out + '.png')
