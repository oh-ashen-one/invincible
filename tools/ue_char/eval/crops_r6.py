# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""3x native crops of the regions the round-05 critic named (CH18 / garment integrity), from a capture directory.

  python3 tools/ue_char/eval/crops_r6.py CAPTURES_DIR OUT_DIR [--r5 ROUND05_CAPTURES_DIR]

Regions (native 3840x2160 pixels, x0 y0 x1 y1):
  coat_tracking       crowd_tracking_4k   2950 1300 3350 1750   (olive coat, trousers; the critic's box)
  hand_tracking       crowd_tracking_4k   3300 1280 3560 1480   (near-lane hand / fingers)
  trousers_tracking   crowd_tracking_4k   3560 1300 3840 1800   (near-lane trousers)
  armpit_key_a        crowd_key_a_4k       300 1050  560 1300   (black-tee armpit, the 244 px hole)
  collar_thug         thug_face_4k        1100 1250 2100 2160   (hoodie collar)
With --r5 the round-05 crop of the same box goes next to it (left = round 05, right = round 06).  Nearest-neighbour is NOT used: 3x Lanczos, so the
crop reads like a zoomed screenshot; the raw pixels are in the source stills."""
import sys, os
from PIL import Image

REG = [('coat_tracking', 'crowd_tracking_4k', (2950, 1300, 3350, 1750)), ('hand_tracking', 'crowd_tracking_4k', (3300, 1280, 3560, 1480)),
       ('trousers_tracking', 'crowd_tracking_4k', (3560, 1300, 3840, 1800)), ('armpit_key_a', 'crowd_key_a_4k', (300, 1050, 560, 1300)),
       ('collar_thug', 'thug_face_4k', (1100, 1250, 2100, 2160))]
a = sys.argv[1:]
r5 = None
if '--r5' in a:
    k = a.index('--r5'); r5 = a[k + 1]; a = a[:k] + a[k + 2:]
cap, out = a[0], a[1]
os.makedirs(out, exist_ok=True)
for name, img, box in REG:
    f = os.path.join(cap, img + '.jpg')
    if not os.path.exists(f): print('missing', f); continue
    w, h = box[2] - box[0], box[3] - box[1]
    new = Image.open(f).convert('RGB').crop(box).resize((3 * w, 3 * h), Image.LANCZOS)
    tiles = [new]
    if r5 and os.path.exists(os.path.join(r5, img + '.jpg')):
        old = Image.open(os.path.join(r5, img + '.jpg')).convert('RGB').crop(box).resize((3 * w, 3 * h), Image.LANCZOS)
        tiles = [old, new]
    sheet = Image.new('RGB', (sum(t.width for t in tiles) + 8 * (len(tiles) - 1), tiles[0].height), (255, 255, 255))
    x = 0
    for t in tiles: sheet.paste(t, (x, 0)); x += t.width + 8
    sheet.save(os.path.join(out, name + '_3x.jpg'), quality=90)
    print(name, sheet.size)
