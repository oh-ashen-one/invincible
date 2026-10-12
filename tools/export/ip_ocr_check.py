#!/usr/bin/env python3
"""IP text check for a capture set: OCR (tesseract, 4 quadrants x normal / inverted) of every 4K frame against the denylist of names that must not appear
(Marvel-universe / real-game brands and real-place evocations flagged in critic rounds, see docs/night1/city/IP_EXCLUSIONS.md), plus an atlas scan:
the sanitised atlas PNGs (as imported into Unreal) are OCR'd cell by cell.  usage: ip_ocr_check.py <round_dir> [atlas_png_dir]"""
import glob, os, subprocess, sys, tempfile
from PIL import Image, ImageOps
import json
DENY = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'docs', 'night1', 'city', 'spec_regions.json')))['ip_denylist']  # single source, shared with city_spec_check.py
tmp = tempfile.mkdtemp()
def ocr(img):
    txt = ''
    for inv in (False, True):
        v = ImageOps.invert(img.convert('RGB')).convert('L') if inv else img.convert('L'); v = v.resize((v.width * 2, v.height * 2)); p = os.path.join(tmp, 'c.png'); v.save(p)
        txt += ' ' + subprocess.run(['tesseract', p, '-', '--psm', '11'], capture_output=True, text=True).stdout.upper()
    return txt
bad = 0
for f in sorted(glob.glob(os.path.join(sys.argv[1], 'S*_3840x2160.jpg'))):
    im = Image.open(f).convert('L'); W, H = im.size; hits = set()
    for (x0, y0) in [(0, 0), (W // 2, 0), (0, H // 2), (W // 2, H // 2)]:
        t = ocr(im.crop((x0, y0, x0 + W // 2, y0 + H // 2)))
        hits |= {d for d in DENY if d in t}
    print(os.path.basename(f), sorted(hits) or 'clean'); bad += len(hits)
if len(sys.argv) > 2:
    ads = Image.open(os.path.join(sys.argv[2], 'maps', 'assets_city_tex_ts_ads.png')).convert('RGB'); sg = Image.open(os.path.join(sys.argv[2], 'maps', 'assets_city_tex_ts_signs.png')).convert('RGB')
    for i in range(64):
        for name, box in ((f'ads L{i}', ((i % 8) * 512, (i // 8) * 256, (i % 8) * 512 + 512, (i // 8) * 256 + 256)), (f'ads P{i}', ((i % 16) * 256, 2048 + (i // 16) * 512, (i % 16) * 256 + 256, 2048 + (i // 16) * 512 + 512)),
                          (f'signs S{i}', ((i % 4) * 512, (i // 4) * 128, (i % 4) * 512 + 512, (i // 4) * 128 + 128))):
            src = sg if name.startswith('signs') else ads
            t = ocr(src.crop(box)); h = {d for d in DENY if d in t}
            if h: print('ATLAS HIT', name, sorted(h)); bad += 1
    print('atlas scan done')
print('TOTAL HITS', bad)
