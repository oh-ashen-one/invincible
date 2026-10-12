#!/usr/bin/env python3
"""Front view of the fitted thug and brute side by side at the SAME scale with the lineup actor scale applied (numpy rasteriser).

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
python3 tools/ue_char/people/compare_front.py OUT.png     - rest pose (A-pose), metres ruler; shoulder-width lines from measure_build.py
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit, ortho, measure_build
SCR = _scr('r3')
SZ = json.load(open(os.path.join(HERE, 'people.json')))['brute']

def load(fit, atlas):
    j, b = skinfit.read_glb(fit)
    p = j['meshes'][0]['primitives'][0]
    P = skinfit.accessor(j, b, p['attributes']['POSITION']); N = skinfit.accessor(j, b, p['attributes']['NORMAL'])
    UV = skinfit.accessor(j, b, p['attributes']['TEXCOORD_0']); F = skinfit.accessor(j, b, p['indices']).reshape(-1, 3).astype(int)
    Image.MAX_IMAGE_PIXELS = None
    return P, N, UV, F, Image.open(atlas).convert('RGB')

out = sys.argv[1]
t = load(SCR + '/fit/StreetThug.glb', SCR + '/people/StreetThug_atlas.png')
r = load(SCR + '/fit/StreetBrute.glb', SCR + '/people/StreetBrute_atlas.png')
s, g = SZ['scale'], SZ['girth']
Pb = r[0] * np.array([s * g, s, s * g])
span, W = 1.9, 1000
tw = measure_build.measure(SCR + '/fit/StreetThug.glb'); rw = measure_build.measure(SCR + '/fit/StreetBrute.glb')
imgs = []
for name, (P, N, UV, F, im), sw in (('thug', (t[0], t[1], t[2], t[3], t[4]), tw['shoulder_width']), ('brute', (Pb, r[1], r[2], r[3], r[4]), rw['shoulder_width'] * s * g)):
    pil = ortho.render(P, N, UV, F, im, 'front', 0.0, 2.1, 0.0, W=W, tex=2048, span=span, grid=False)
    d = ImageDraw.Draw(pil); sc = W / span
    Y = (2.1 - 1.43) * sc
    for sgn in (-1, 1):
        X = W / 2 + sgn * sw / 2 * sc
        d.line((X, Y - 60, X, Y + 60), fill=(255, 60, 60), width=3)
    d.line((W / 2 - sw / 2 * sc, Y, W / 2 + sw / 2 * sc, Y), fill=(255, 60, 60), width=3)
    d.text((W / 2 - 120, Y - 80), '%s shoulder width %.2f m' % (name, sw), fill=(255, 255, 255))
    for k in range(0, 22):                                   # 10 cm ruler on the left edge, 1 m marks longer
        yy = (2.1 - k * 0.1) * sc; d.line((0, yy, 30 if k % 10 == 0 else 14, yy), fill=(255, 255, 0), width=2)
        if k % 5 == 0: d.text((36, yy - 6), '%.1f m' % (k * 0.1), fill=(255, 255, 0))
    imgs.append(pil)
canvas = Image.new('RGB', (imgs[0].width * 2, imgs[0].height))
for i, im in enumerate(imgs): canvas.paste(im, (i * im.width, 0))
canvas.save(out)
print('ratio (brute world / thug):', round(rw['shoulder_width'] * s * g / tw['shoulder_width'], 3))
