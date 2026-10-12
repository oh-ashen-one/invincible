#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life IP text check: OCR (tesseract, normal + inverted) of the sanitised vehicle atlas (as imported into Unreal) cell by cell and of the
# 4K captures of a round against the denylist of Marvel-universe / real-game / real-agency names (docs/night1/city/IP_EXCLUSIONS.md + P6 additions).
#   python3 tools/life/ip_check.py <atlas_png> [capture.jpg|png ...]
import os, subprocess, sys, tempfile
from PIL import Image, ImageOps
DENY = ['OSCORP', 'OSBORN', 'ROXX', 'BUGLE', 'FROSTED', 'HALOS', 'BOTANICA', 'HYDRA', 'EMPIRE STATE', 'COLTEX', 'COLEX', 'HAUTE', 'ASTOR', 'MADISON', 'BOREAL',
        'STARK', 'WAYNE', 'MARVEL', 'SPIDER', 'DAILY BU', 'M15', 'SELECT BUS', 'NYC TRANSIT', 'MTA', 'SKYLINE SNEAK']
tmp = tempfile.mkdtemp()
def ocr(img):
    txt = ''
    for inv in (False, True):
        v = ImageOps.invert(img.convert('RGB')).convert('L') if inv else img.convert('L')
        v = v.resize((v.width * 2, v.height * 2)); p = os.path.join(tmp, 'c.png'); v.save(p)
        txt += ' ' + subprocess.run(['tesseract', p, '-', '--psm', '11'], capture_output=True, text=True).stdout.upper()
    return txt
bad = 0
atlas = Image.open(sys.argv[1]).convert('RGB'); W, H = atlas.size
n = 8; cw, ch = W // n, H // n
for gy in range(n):
    for gx in range(n):
        t = ocr(atlas.crop((gx * cw, gy * ch, gx * cw + cw, gy * ch + ch)))
        h = sorted(d for d in DENY if d in t)
        if h: print('ATLAS HIT cell (%d,%d)' % (gx, gy), h); bad += len(h)
# whole ad / sign strips at native scale (text spans cell borders)
for name, box in (('ad column', (W // 2, 0, W, H // 3 + 20)), ('bus + sign bands', (0, 1200, W // 2, 1330)), ('bus band 2', (W // 2, 1230, W, 1330))):
    t = ocr(atlas.crop(box)); h = sorted(d for d in DENY if d in t)
    if h: print('ATLAS HIT', name, h); bad += len(h)
print('atlas scan done')
for f in sys.argv[2:]:
    im = Image.open(f).convert('L'); w, h_ = im.size; hits = set()
    for (x0, y0) in [(0, 0), (w // 2, 0), (0, h_ // 2), (w // 2, h_ // 2)]:
        t = ocr(im.crop((x0, y0, x0 + w // 2, y0 + h_ // 2))); hits |= {d for d in DENY if d in t}
    print(os.path.basename(f), sorted(hits) or 'clean'); bad += len(hits)
print('TOTAL HITS', bad)
