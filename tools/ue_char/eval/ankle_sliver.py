# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: thin background slivers at the ankles (open or enclosed) of the crowd citizens in their own walk clips, offline.

Side views (yaw 90 / 270, two-sided) at 1500 px/m of every 2nd frame of the citizen's walk + idle.  A sliver = background pixels that a 5x5 closing of the
person mask fills but that are not part of a wide gap (an opening of 9 px removes wide gaps), inside the ankle box (y 0.02 .. 0.22 m above the ground of the
posed mesh's lowest vertex).  Prints components / px per citizen.

  python3 tools/ue_char/eval/ankle_sliver.py [--dir DIR] [--imgs DIR] NAME [NAME ...]
"""
import os, sys, json
import numpy as np
import cv2
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from p2paths import scr  # noqa: E402
import cit_proxy as CP   # noqa: E402
from eval_r6 import CIT_WALK  # noqa: E402
from PIL import Image  # noqa: E402

a = sys.argv[1:]; d = scr('eval', 'refit'); imgs = None
for k in ('--dir', '--imgs'):
    if k in a:
        i = a.index(k); v = a[i + 1]; a = a[:i] + a[i + 2:]
        if k == '--dir': d = v
        else: imgs = v; os.makedirs(v, exist_ok=True)
PPM = 1500
tot_c = tot_px = 0
for name in a:
    z = np.load(os.path.join(d, name + '_final.npz'))
    m = CP.Mesh(z['pos'], z['idx'], z['uv'], z['dense'], None, name)
    clip = CIT_WALK.get(name, 'walk')
    frames = [(clip, f) for f in range(0, CP.rig().clip_len(clip), 2)] + [('idle', 0)]
    Pws = [m.posed(c, f) for c, f in frames]
    # one fixed frame for all views: ankle box only
    W_, H_ = 900, 420
    ncomp = npx = 0; worst = []
    for (c, f), Pw in zip(frames, Pws):
        for yaw in (90.0, 270.0):
            ground = Pw[:, 1].min()
            xs = Pw[:, 2] if False else None
            R = CP.view_matrix(yaw); Q = Pw @ R.T
            cx = float(np.median(Q[(Pw[:, 1] < ground + 0.25), 0]))
            ox = W_ / 2 - cx * PPM; oy = H_ - 0.02 * PPM + ground * PPM * 0 - ground * PPM * 0
            oy = H_ + ground * PPM - 0.30 * PPM * 0 - 40      # ground line 40 px above the crop bottom
            _, mask = CP.raster(Pw, m.T, m.uv, None, yaw, PPM, W_, H_, ox, oy - (-ground * PPM) * 0, colour=False, cull=False)
            mk = ndimage.binary_closing(mask, structure=np.ones((5, 5), bool))
            slit = mk & ~mask
            wide = ndimage.binary_opening(~mask, structure=np.ones((9, 9), bool))
            slit &= ~ndimage.binary_dilation(wide, iterations=2)
            lab, n = ndimage.label(slit)
            if n:
                sz = np.bincount(lab.ravel())[1:]; keep = np.where(sz >= 6)[0] + 1
                slit = np.isin(lab, keep); n = len(keep)
            if n:
                ncomp += n; npx += int(slit.sum()); worst.append((int(slit.sum()), c, f, yaw))
                if imgs and len(worst) <= 5:
                    vis = np.zeros((H_, W_, 3), np.uint8); vis[mask] = (150, 150, 150); vis[slit] = (0, 0, 255)
                    cv2.imwrite(os.path.join(imgs, '%s_%s_f%d_y%d.png' % (name, c, f, yaw)), vis)
    r = dict(name=name, views=len(frames) * 2, sliver_components=int(ncomp), sliver_px=int(npx), views_with=len(worst))
    print(json.dumps(r)); tot_c += ncomp; tot_px += npx
print('TOTAL sliver_components', tot_c, 'sliver_px', tot_px)
