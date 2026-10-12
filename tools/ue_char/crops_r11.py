#!/usr/bin/env python3
"""Round 11: 3x Lanczos crops of the hair / collar regions named by the round-10 critic, this round vs round 10 (same lineup close-up cameras).

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.
  python3 tools/ue_char/crops_r11.py <round11 captures> <round10 captures> <out dir>
Writes <out>/r11_<name>.jpg and r10_<name>.jpg (4K boxes, x 3): hood-hair (the r10 maroon / blond seam (1900,633) - (2350,283)), beard-hair (the r10 flat card at
(2480 - 2610, 380 - 600)), tee-hair (the side curls behind the ear), thug-collar (the r10 wedge at (1746 - 1817, 1358 - 1508))."""
import os, sys
from PIL import Image, ImageDraw
cap, prev, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
S = 3
BOX = {'hood-hair': ('hood_face_4k.jpg', (1800, 180, 2500, 700)), 'beard-hair': ('beard_face_4k.jpg', (2330, 250, 2830, 700)),
       'tee-hair': ('tee_face_4k.jpg', (1150, 250, 1750, 800)), 'thug-collar': ('thug_face_4k.jpg', (1550, 1250, 1950, 1600))}
for tag, d in (('r11', cap), ('r10', prev)):
    for name, (f, box) in BOX.items():
        p = os.path.join(d, f)
        if not os.path.exists(p): print('missing', p); continue
        c = Image.open(p).convert('RGB').crop(box); c = c.resize((c.width * S, c.height * S), Image.LANCZOS)
        ImageDraw.Draw(c).text((8, 6), '%s %s 4K box %s x3' % (tag, f, box), fill=(255, 255, 0))
        c.save(os.path.join(out, '%s_%s.jpg' % (tag, name)), quality=92)
print('crops ->', out)
