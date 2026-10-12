"""Side-view stick figures of hero clip poses (numpy + cv2, no GPU). Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.
  python3 tools/ue_char/heroanim/skel_plot.py GLB OUT.png clip:t0,t1,... [clip:t...]      (times in seconds; forward = right)
Draws every bone parent->child, feet / hands / head marked, a ground line at the lowest foot of the first pose."""
import sys, os
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ganim import Doc

def draw(d, clip, t, W=260, H=360, sc=150.0, ox=None, oy=None, ground=None):
    tr = d.tracks(clip)
    Wd = d.world(d.sample(tr, t))
    img = np.full((H, W, 3), 245, np.uint8)
    hips = Wd[d.idx['hips']][:3, 3]
    ox = W / 2 - hips[2] * sc if ox is None else ox
    oy = H * 0.52 + hips[1] * sc if oy is None else oy
    P = lambda n: (int(ox + Wd[n][2, 3] * sc), int(oy - Wd[n][1, 3] * sc))
    js = set(d.joints)
    for n in d.joints:
        p = d.parent.get(n)
        if p in js:
            col = (60, 60, 60)
            nm = d.names[n]
            if nm.endswith('.L'): col = (200, 90, 40)
            if nm.endswith('.R'): col = (40, 90, 200)
            cv2.line(img, P(p), P(n), col, 2)
    for nm, c in (('head', (0, 0, 0)), ('foot.L', (200, 90, 40)), ('foot.R', (40, 90, 200)), ('hand.L', (200, 90, 40)), ('hand.R', (40, 90, 200))):
        if nm in d.idx: cv2.circle(img, P(d.idx[nm]), 4, c, -1)
    if ground is not None:
        cv2.line(img, (0, int(oy - ground * sc)), (W, int(oy - ground * sc)), (150, 150, 150), 1)
    cv2.putText(img, '%s %.2f' % (clip, t), (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    return img

if __name__ == '__main__':
    d = Doc(sys.argv[1]); out = sys.argv[2]
    tiles = []
    for spec in sys.argv[3:]:
        clip, ts = spec.split(':')
        for t in ts.split(','):
            tiles.append(draw(d, clip, float(t)))
    rows = [np.hstack(tiles[i:i + 8]) for i in range(0, len(tiles), 8)]
    w = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0)), constant_values=245) for r in rows]
    cv2.imwrite(out, np.vstack(rows)); print(out, tiles[0].shape, len(tiles))
