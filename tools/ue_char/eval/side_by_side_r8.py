# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: a labelled side-by-side figure of the same shot in two rounds.  python3 side_by_side_r8.py OUT.jpg WIDTH  LEFT.jpg "label"  RIGHT.jpg "label" [crop x0 y0 x1 y1 (applied to both)]"""
import sys
from PIL import Image, ImageDraw
out, W = sys.argv[1], int(sys.argv[2])
l, ll, r, rl = sys.argv[3:7]
box = [int(v) for v in sys.argv[7:11]] if len(sys.argv) >= 11 else None
def load(p):
    im = Image.open(p).convert('RGB')
    return im.crop(box) if box else im
a, b = load(l), load(r)
h = int(W * a.height / a.width)
a = a.resize((W, h), Image.LANCZOS); b = b.resize((W, h), Image.LANCZOS)
s = Image.new('RGB', (2 * W + 10, h), (255, 255, 255)); s.paste(a, (0, 0)); s.paste(b, (W + 10, 0))
d = ImageDraw.Draw(s)
for x, t in ((8, ll), (W + 18, rl)):
    d.rectangle((x - 4, 4, x + 7 * len(t) + 6, 22), fill=(0, 0, 0)); d.text((x, 7), t, fill=(255, 255, 255))
s.save(out, quality=90)
print(out, s.size)
