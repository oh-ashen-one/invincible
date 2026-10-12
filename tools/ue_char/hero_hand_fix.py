#!/usr/bin/env python3
"""UE-side fix of the hero base colour: the white emblem paint that covers the back of both hands (round-03 critic,
hero_run_34_4k: 'white emblem texture bleeds onto the back of the hand'). Texels covered ONLY by hand triangles (every vertex
dominated by a hand / finger bone) that are white are inpainted from the surrounding red glove (OpenCV Telea), so the web
lines partly continue. Texels shared with any non-hand triangle are left alone (the chest emblem is untouched).
Writes art/night1/characters/hero/tex/suit_basecolor_r4.png (derived, git-ignored); the browser texture is unchanged.
Fan homage project; not official Marvel/Sony/Insomniac.   python3 tools/ue_char/hero_hand_fix.py"""
import sys, os, json
import numpy as np
import cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skinfit')); sys.path.insert(0, os.path.join(HERE, 'people'))
import skinfit  # noqa
from prepare_person import raster_positions  # noqa
Image.MAX_IMAGE_PIXELS = None
WT = os.path.abspath(os.path.join(HERE, '../..'))
SRC = WT + '/art/night1/characters/hero/tex/suit_basecolor.png'
DST = WT + '/art/night1/characters/hero/tex/suit_basecolor_r4.png'


def main():
    j, b = skinfit.read_glb(WT + '/public/assets/spiderman.glb')
    nd = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan'); p = j['meshes'][nd['mesh']]['primitives'][0]
    acc = lambda k: skinfit.accessor(j, b, p['attributes'][k])
    P, UV = acc('POSITION'), acc('TEXCOORD_0'); J, W = acc('JOINTS_0'), acc('WEIGHTS_0')
    F = skinfit.accessor(j, b, p['indices']).reshape(-1, 3).astype(int)
    names = [j['nodes'][k]['name'] for k in j['skins'][0]['joints']]
    hand = [i for i, n in enumerate(names) if n.split('.')[0] in ('hand', 'index1', 'index2', 'index3', 'middle1', 'middle2', 'middle3', 'ring1', 'ring2', 'ring3', 'pinky1', 'pinky2', 'pinky3', 'thumb1', 'thumb2', 'thumb3')]
    dom = J[np.arange(len(J)), W.argmax(1)].astype(int)
    ht = np.isin(dom, hand)[F].all(1)
    im = np.asarray(Image.open(SRC).convert('RGB')); N = im.shape[0]
    ch, _ = raster_positions(P, UV, F[ht], N)
    co, _ = raster_positions(P, UV, F[~ht], N)
    a = im.astype(np.float32); lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    white = (lum > 150) & (a.max(-1) - a.min(-1) < 60)
    m = ch & ~co & white
    m = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) & (ch & ~co).astype(np.uint8)
    out = cv2.inpaint(im[..., ::-1].copy(), m * 255, 9, cv2.INPAINT_TELEA)[..., ::-1]
    Image.fromarray(out).save(DST)
    info = {'hand_texels': int(ch.sum()), 'hand_white_inpainted': int(m.sum()), 'shared_texels_kept': int((ch & co).sum())}
    print(json.dumps(info))


if __name__ == '__main__':
    main()
