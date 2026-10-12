# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 16: the no-new-defect crop sheets.  Per suit one sheet, r15 (top) vs r16 (bottom), four crops of the 4K stills at the places the r15 critic looked:
chest (the image-left armpit side, 1100-1760 x 1050-1500, native pixels), back (the torso, 1500-2340 x 560-1400, native), head (headfront 1440-2400 x 120-1800 at 0.5x), front (full frame at 0.25x).
usage: python3 crop_sheets_r16.py <r16 stills> <r15 stills> <out dir>"""
import os, sys
from PIL import Image, ImageDraw

SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
CROPS = [('chest', (1100, 1050, 1760, 1500), 1.0), ('back', (1500, 560, 2340, 1400), 0.6), ('headfront', (1440, 120, 2400, 1800), 0.32), ('front', (0, 0, 3840, 2160), 0.14)]


def load(d, s, v):
    for ext in ('png', 'jpg'):
        p = os.path.join(d, 'skin_%s_%s_4k.%s' % (s, v, ext))
        if os.path.exists(p): return Image.open(p).convert('RGB')
    return None


def main():
    a, b, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    for s in SUITS:
        rows = []
        for d, tag in ((b, 'r15'), (a, 'r16')):
            tiles = []
            for v, box, sc in CROPS:
                im = load(d, s, v)
                if im is None: continue
                c = im.crop(box); c = c.resize((int(c.size[0] * sc), int(c.size[1] * sc)))
                ImageDraw.Draw(c).text((6, 6), '%s %s %s' % (tag, s, v), fill=(255, 255, 0))
                tiles.append(c)
            rows.append(tiles)
        W = max(sum(t.size[0] for t in r) for r in rows); H = sum(max(t.size[1] for t in r) for r in rows)
        sheet = Image.new('RGB', (W, H)); y = 0
        for r in rows:
            x = 0
            for t in r: sheet.paste(t, (x, y)); x += t.size[0]
            y += max(t.size[1] for t in r)
        sheet.save(os.path.join(out, 'crops_%s.jpg' % s), quality=88)
    print('crop sheets:', out)


if __name__ == '__main__':
    main()
