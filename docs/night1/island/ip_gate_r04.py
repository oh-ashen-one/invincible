#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A) round 04 IP text gate (copy of ip_gate_r03.py with the round dir as a parameter) over the round's stills: OCR (tesseract; 4 quadrants x normal / inverted, 2x upscale) of every
# image against the denylist of tools/export/ip_ocr_check.py (docs/night1/city/spec_regions.json "ip_denylist") plus the island's own additions
# below (real bank / chain names that round-02 / round-03 frames showed). Writes round-03/ip_gate.json; exit 1 on any hit.
#   python3 docs/night1/island/ip_gate_r04.py [stills_dir ...]     (default: round-04/stills); env IP_GATE_OUT = output json (default round-04/ip_gate.json)
import glob, json, os, subprocess, sys, tempfile
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DENY = json.load(open(os.path.join(ROOT, 'docs', 'night1', 'city', 'spec_regions.json')))['ip_denylist']
DENY += ['CHASE BANK', 'DUANE READE', 'SUBWAY EATS', 'STARBUCKS', 'MCDONALD', 'WALGREENS', 'CVS PHARMACY']   # island additions (signs.png rows, real chains; 3-letter tokens like CVS hit OCR noise on roof grime: r4 t12)
tmp = tempfile.mkdtemp()


def ocr(img):
    txt = ''
    for inv in (False, True):
        v = ImageOps.invert(img.convert('RGB')).convert('L') if inv else img.convert('L')
        v = v.resize((v.width * 2, v.height * 2))
        p = os.path.join(tmp, 'c.png'); v.save(p)
        txt += ' ' + subprocess.run(['tesseract', p, '-', '--psm', '11'], capture_output=True, text=True).stdout.upper()
    return txt


dirs = sys.argv[1:] or [os.path.join(HERE, 'round-04', 'stills')]
out, bad = [], 0
for d in dirs:
    for f in sorted(glob.glob(os.path.join(d, '*.jpg'))):
        im = Image.open(f).convert('L'); W, H = im.size; hits = set()
        for (x0, y0) in [(0, 0), (W // 2, 0), (0, H // 2), (W // 2, H // 2)]:
            t = ocr(im.crop((x0, y0, x0 + W // 2, y0 + H // 2)))
            hits |= {w for w in DENY if w in t}
        print(os.path.basename(f), sorted(hits) or 'clean'); bad += len(hits)
        out.append({'file': os.path.basename(f), 'size': [W, H], 'hits': sorted(hits)})
json.dump({'denylist': DENY, 'images': len(out), 'hits_total': bad, 'results': out}, open(os.environ.get('IP_GATE_OUT', os.path.join(HERE, 'round-04', 'ip_gate.json')), 'w'), indent=1)
print('IP gate: %d images, %d hits' % (len(out), bad))
sys.exit(1 if bad else 0)
