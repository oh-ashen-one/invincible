"""Quick numpy clay/texture head renders of a prepared person (no GPU): Lambert shading + optional atlas texture, several yaw angles.
Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.
  python3 tools/ue_char/people/clay.py PREPARED.npz OUT.png [--atlas ATLAS.png] [--yaws -45,0,45,90] [--y0 1.45 --y1 1.75] [--px 1400]
Coordinates: metres, +z forward, +x = the character's left. Camera looks at the head from yaw degrees around +y (0 = in front).
"""
import sys, argparse
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def render(P, N, UV, F, tex, yaw, y0, y1, px, cx=0.0, cz=-0.02, light=(0.35, 0.55, 0.75), span=0.5):
    th = np.radians(yaw)
    R = np.array([[np.cos(th), 0, -np.sin(th)], [0, 1, 0], [np.sin(th), 0, np.cos(th)]])   # rotate the model so the camera (at +z) sees it from `yaw`
    Q = (P - [cx, 0, cz]) @ R.T; Nn = N @ R.T
    W = px; Hh = int(px * (y1 - y0) / span)
    sc = W / span
    U = Q[:, 0] * sc + W / 2; V = (y1 - Q[:, 1]) * sc; D = Q[:, 2]
    img = np.zeros((Hh, W, 3), np.float32) + 30; zb = np.full((Hh, W), -1e9)
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    for f in F:
        a, b, c = f
        xs = U[[a, b, c]]; ys = V[[a, b, c]]
        x0, x1 = int(max(0, np.floor(xs.min()))), int(min(W - 1, np.ceil(xs.max())))
        y0_, y1_ = int(max(0, np.floor(ys.min()))), int(min(Hh - 1, np.ceil(ys.max())))
        if x1 < x0 or y1_ < y0_: continue
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0_, y1_ + 1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any(): continue
        z = w0 * D[a] + w1 * D[b] + w2 * D[c]
        sub = zb[y0_:y1_ + 1, x0:x1 + 1]
        vis = m & (z > sub)
        if not vis.any(): continue
        nrm = w0[..., None] * Nn[a] + w1[..., None] * Nn[b] + w2[..., None] * Nn[c]
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9
        lam = np.clip(nrm @ L, 0, 1) * 0.75 + 0.25
        if tex is not None:
            u = w0 * UV[a, 0] + w1 * UV[b, 0] + w2 * UV[c, 0]; v = w0 * UV[a, 1] + w1 * UV[b, 1] + w2 * UV[c, 1]
            T = tex; col = T[np.clip((v * T.shape[0]).astype(int), 0, T.shape[0] - 1), np.clip((u * T.shape[1]).astype(int), 0, T.shape[1] - 1)].astype(np.float32)
        else:
            col = np.full(z.shape + (3,), 190, np.float32)
        sub[vis] = z[vis]
        img[y0_:y1_ + 1, x0:x1 + 1][vis] = (col * lam[..., None])[vis]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('npz'); ap.add_argument('out'); ap.add_argument('--atlas'); ap.add_argument('--yaws', default='-40,0,40,90')
    ap.add_argument('--y0', type=float, default=1.44); ap.add_argument('--y1', type=float, default=1.74); ap.add_argument('--px', type=int, default=700)
    a = ap.parse_args()
    z = np.load(a.npz)
    P, N, UV, F = z['P'], z['N'], z['UV'], z['F']
    tex = None
    if a.atlas:
        im = Image.open(a.atlas).convert('RGB'); im = im.resize((2048, 2048), Image.LANCZOS); tex = np.asarray(im)
    tiles = [render(P, N, UV, F, tex, float(y), a.y0, a.y1, a.px) for y in a.yaws.split(',')]
    W = sum(t.size[0] for t in tiles); H = tiles[0].size[1]
    out = Image.new('RGB', (W, H))
    x = 0
    for t in tiles: out.paste(t, (x, 0)); x += t.size[0]
    out.save(a.out)
    print(a.out, out.size)
