"""Orthographic textured view of a person mesh with a metric ruler (numpy rasteriser). Fan homage; no affiliation.

python3 tools/ue_char/people/ortho.py IN.glb OUT.png --view side|front|back --y0 1.45 --y1 1.8 [--cx 0] [--tex 2048]
Coordinates: metres, y up, +z forward, +x = character's left. Draws horizontal lines every 2 cm (labelled every 10 cm)
and vertical lines every 2 cm.
"""
import sys, os, argparse
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gltfio

def render(P, N, UV, F, im, view='side', y0=1.45, y1=1.8, cx=0.0, W=1000, tex=2048, h0=None, span=0.4, grid=True):
    im = im.resize((tex, tex), Image.LANCZOS); T = np.asarray(im)
    H = int(W * (y1 - y0) / span) if h0 is None else h0
    sc = W / span                          # px per metre
    if view == 'side': hx = P[:, 2]; sign = 1.0
    elif view == 'front': hx = P[:, 0]; sign = 1.0     # camera at +z looking back at the face: character's left (+x) on the right
    else: hx = P[:, 0]; sign = -1.0                    # 'back': camera at -z
    U = (hx - cx) * sign * sc + W / 2
    V = (y1 - P[:, 1]) * sc
    depth = {'side': -P[:, 0], 'front': P[:, 2], 'back': -P[:, 2]}[view]  # larger = closer to camera
    img = np.zeros((int(H), W, 3), np.uint8) + 25; zb = np.full((int(H), W), -1e9)
    for f in F:
        a, b, c = f
        xs = U[[a, b, c]]; ys = V[[a, b, c]]
        x0, x1 = int(max(0, np.floor(xs.min()))), int(min(W - 1, np.ceil(xs.max())))
        yy0, yy1 = int(max(0, np.floor(ys.min()))), int(min(H - 1, np.ceil(ys.max())))
        if x1 < x0 or yy1 < yy0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(yy0, yy1 + 1) + 0.5)
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9: continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any(): continue
        z = w0 * depth[a] + w1 * depth[b] + w2 * depth[c]
        sub = zb[yy0:yy1 + 1, x0:x1 + 1]
        vis = m & (z > sub)
        if not vis.any(): continue
        u = w0 * UV[a, 0] + w1 * UV[b, 0] + w2 * UV[c, 0]; v = w0 * UV[a, 1] + w1 * UV[b, 1] + w2 * UV[c, 1]
        col = T[np.clip((v * tex).astype(int), 0, tex - 1), np.clip((u * tex).astype(int), 0, tex - 1)]
        sub[vis] = z[vis]; img[yy0:yy1 + 1, x0:x1 + 1][vis] = col[vis]
    pil = Image.fromarray(img)
    if not grid:
        return pil
    d = ImageDraw.Draw(pil)
    yy = np.ceil(y0 / 0.02) * 0.02
    while yy <= y1:
        Y = (y1 - yy) * sc; big = abs(round(yy / 0.1) * 0.1 - yy) < 1e-6
        d.line((0, Y, W, Y), fill=(255, 255, 0) if big else (90, 90, 150)); d.text((3, Y - 11), '%.2f' % yy, fill=(255, 255, 120))
        yy += 0.02
    xx = np.ceil((cx - span / 2) / 0.02) * 0.02
    while xx <= cx + span / 2:
        X = (xx - cx) * sign * sc + W / 2
        d.line((X, 0, X, H), fill=(70, 120, 70)); d.text((X + 2, H - 12), '%.2f' % xx, fill=(140, 255, 140))
        xx += 0.02
    return pil

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--view', default='side'); ap.add_argument('--y0', type=float, default=1.45); ap.add_argument('--y1', type=float, default=1.8)
    ap.add_argument('--cx', type=float, default=0.0); ap.add_argument('--tex', type=int, default=2048); ap.add_argument('--raw', action='store_true', help='src is a raw Tripo GLB (rotate + normalise first)')
    a = ap.parse_args()
    P, N, UV, F, im = gltfio.read_person(a.src)
    if a.raw:
        import skinfit
        R = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)
        game = skinfit.Game(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../public/assets/spiderman.glb'))
        P = skinfit.normalise_target(P @ R.T, game)
    render(P, N, UV, F, im, a.view, a.y0, a.y1, a.cx, tex=a.tex).save(a.out)
