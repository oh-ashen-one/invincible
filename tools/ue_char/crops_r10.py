#!/usr/bin/env python3
"""Round 10: 3x Lanczos crops of the same region of two versions of a capture (this round vs round 09) for the critic pack and the spec check.

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.
  python3 tools/ue_char/crops_r10.py <round10 captures> <round09 captures> <out dir>
Writes <out>/r10_<name>.jpg and r9_<name>.jpg for: arm (3 frames of street_fight_34 at 1.30 / 1.40 / 1.50 s: the r09 'untextured grey arm' = the Brute's pipe through the hero's back),
thug-collar, beard-hair, hood-hair (4K face stills)."""
import os, sys, subprocess, tempfile
from PIL import Image, ImageDraw
cap, prev, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
S = 3
ARM_BOX = (700, 330, 1100, 630)                       # 1080p region of the r09 grey limb (about 860 - 930, 450 - 520 inside it)
ARM_T = (1.30, 1.40, 1.50)
STILLS = {'thug-collar': ('thug_face_4k.jpg', (1550, 1250, 1950, 1600)), 'beard-hair': ('beard_face_4k.jpg', (2330, 280, 2830, 680)), 'hood-hair': ('hood_face_4k.jpg', (1250, 0, 2250, 650))}


def frame(mp4, t):
    tmp = tempfile.mktemp(suffix='.png')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.4f' % t, '-i', mp4, '-frames:v', '1', tmp], check=True)
    im = Image.open(tmp).convert('RGB'); os.remove(tmp); return im


def up(im, box):
    c = im.crop(box); return c.resize((c.width * S, c.height * S), Image.LANCZOS)


for tag, d in (('r10', cap), ('r9', prev)):
    mp4 = os.path.join(d, 'street_fight_34.mp4')
    if os.path.exists(mp4):
        tiles = []
        for t in ARM_T:
            c = up(frame(mp4, t), ARM_BOX); ImageDraw.Draw(c).text((6, 4), '%s street_fight_34 t=%.2f s' % (tag, t), fill=(255, 255, 0)); tiles.append(c)
        sh = Image.new('RGB', (sum(t.width for t in tiles), tiles[0].height)); x = 0
        for t in tiles: sh.paste(t, (x, 0)); x += t.width
        sh.save(os.path.join(out, '%s_arm.jpg' % tag), quality=92)
    for name, (f, box) in STILLS.items():
        p = os.path.join(d, f)
        if os.path.exists(p): up(Image.open(p).convert('RGB'), box).save(os.path.join(out, '%s_%s.jpg' % (tag, name)), quality=92)


def hero_box(im, half=170):
    """Box (2*half square, 1080p) round the hero: the centroid of the teal suit pixels (hue 165 - 200 deg, saturation > 0.45) - the only teal in the street."""
    import numpy as np
    a = np.asarray(im.convert('HSV')).astype(np.float32); h = a[..., 0] * 360 / 255; sat = a[..., 1] / 255; v = a[..., 2] / 255
    m = (h > 165) & (h < 200) & (sat > 0.45) & (v > 0.25)
    ys, xs = np.nonzero(m)
    if len(xs) < 200: return None
    cx, cy = int(np.median(xs)), int(np.median(ys))
    cx = min(max(cx, half), im.width - half); cy = min(max(cy, half), im.height - half)
    return (cx - half, cy - half, cx + half, cy + half)


# the hero in every fight clip at 1.30 / 1.40 / 1.50 s (the frames of the r09 'grey arm'), hero-centred, 3x
for tag, d in (('r10', cap), ('r9', prev)):
    for clip in ('wide', '34', 'orbit'):
        mp4 = os.path.join(d, 'street_fight_%s.mp4' % clip)
        if not os.path.exists(mp4): continue
        tiles = []
        for t in ARM_T:
            im = frame(mp4, t); b = hero_box(im)
            if b is None: continue
            c = up(im, b); ImageDraw.Draw(c).text((6, 4), '%s %s t=%.2f s' % (tag, clip, t), fill=(255, 255, 0)); tiles.append(c)
        if tiles:
            sh = Image.new('RGB', (sum(t.width for t in tiles), tiles[0].height)); x = 0
            for t in tiles: sh.paste(t, (x, 0)); x += t.width
            sh.save(os.path.join(out, '%s_hero_%s.jpg' % (tag, clip)), quality=92)
print('crops ->', out)
