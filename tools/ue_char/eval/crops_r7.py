# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: 3x crops (Lanczos) of the regions the round-06 critic named, round 06 | round 07 side by side, on the flat key backdrop.

  python3 tools/ue_char/eval/crops_r7.py ROUND06_CAPTURES ROUND07_CAPTURES OUT_DIR

Each entry: name, (r06 still, box), (r07 still, box) in native 3840x2160 pixels.  The r06 boxes are the critic's coordinates (rear jeans leg of crowd_key_c_4k x3215-3345 y1745-1940; the floating
triangle x2225-2261 y1190-1216; black-tee / hoodie in crowd_key_a_4k; the ankle cuff / shoe gap of crowd_key_tracking_4k at 1625,1277).  The r07 boxes follow the SAME pedestrians to
wherever the new layout puts them (the people are the same 18 citizens, the lanes changed).  Also writes r6_<name>.jpg / r7_<name>.jpg singly (critic pack pairs)."""
import sys, os
from PIL import Image, ImageDraw
r6d, r7d, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
def load(d, n):
    for ext in ('.png', '.jpg'):
        f = os.path.join(d, n + ext)
        if os.path.exists(f): return Image.open(f).convert('RGB')
    raise SystemExit('missing ' + n + ' in ' + d)
ENT = [  # name, (r06 image, box), (r07 image, box)
    ('jeans-leg', ('crowd_key_c_4k', (3040, 1640, 3760, 2040)), ('crowd_key_c_4k', (620, 1580, 1340, 1980))),
    ('overlap-near', ('crowd_key_a_4k', (100, 800, 820, 1520)), ('crowd_key_a_4k', (1240, 800, 1960, 1520))),
    ('ankle-close', ('crowd_key_tracking_4k', (1475, 1150, 1775, 1350)), ('crowd_key_c_4k', (1090, 1100, 1390, 1300))),
    ('floating-shape', ('crowd_key_c_4k', (2090, 1100, 2390, 1300)), ('crowd_key_wide_4k', (2090, 1100, 2390, 1300))),   # same screen box; in the round-07 c / a stills a walker stands there, the wide still leaves it empty
]
for name, (i6, b6), (i7, b7) in ENT:
    a = load(r6d, i6).crop(b6); b = load(r7d, i7).crop(b7)
    a3 = a.resize((a.width * 3, a.height * 3), Image.LANCZOS); b3 = b.resize((b.width * 3, b.height * 3), Image.LANCZOS)
    a3.save(os.path.join(out, 'r6_%s.jpg' % name), quality=92); b3.save(os.path.join(out, 'r7_%s.jpg' % name), quality=92)
    h = max(a3.height, b3.height); s = Image.new('RGB', (a3.width + b3.width + 10, h), (255, 255, 255))
    s.paste(a3, (0, 0)); s.paste(b3, (a3.width + 10, 0))
    d = ImageDraw.Draw(s); d.text((6, 4), 'round 06  %s %s' % (i6, b6), fill=(255, 255, 255)); d.text((a3.width + 16, 4), 'round 07  %s %s' % (i7, b7), fill=(255, 255, 255))
    s.save(os.path.join(out, '%s_3x.jpg' % name), quality=90)
    print(name, s.size)
