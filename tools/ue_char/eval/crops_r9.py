# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 09 (labels from argv): 3x crops (Lanczos) of the regions the last critic named, previous round | this round side by side (native 3840x2160 pixels, same shot in both rounds).

  python3 tools/ue_char/eval/crops_r9.py SPEC.json PREV_CAPTURES THIS_CAPTURES OUT_DIR [PREV_LABEL=r8] [THIS_LABEL=r9]

SPEC.json = [{"name": "hero-eye", "r7": ["hero_face_lens_4k.jpg", [x0, y0, x1, y1]], "r8": ["hero_face_lens_4k.jpg", [x0, y0, x1, y1]]}, ...]
Writes <name>_3x.jpg (both side by side, labelled) plus <PREV_LABEL>_<name>.jpg / <THIS_LABEL>_<name>.jpg singly (critic pack pairs)."""
import sys, os, json
from PIL import Image, ImageDraw
spec, r7d, r8d, out = sys.argv[1:5]
L7 = sys.argv[5] if len(sys.argv) > 5 else 'r8'; L8 = sys.argv[6] if len(sys.argv) > 6 else 'r9'
os.makedirs(out, exist_ok=True)
def load(d, n):
    p = os.path.join(d, n)
    if os.path.exists(p): return Image.open(p).convert('RGB')
    for ext in ('.png', '.jpg'):
        q = os.path.join(d, os.path.splitext(n)[0] + ext)
        if os.path.exists(q): return Image.open(q).convert('RGB')
    raise SystemExit('missing ' + n + ' in ' + d)
for e in json.load(open(spec)):
    n = e['name']; (i7, b7), (i8, b8) = e['prev'], e['this']
    a = load(r7d, i7).crop(tuple(b7)); b = load(r8d, i8).crop(tuple(b8))
    a3 = a.resize((a.width * 3, a.height * 3), Image.LANCZOS); b3 = b.resize((b.width * 3, b.height * 3), Image.LANCZOS)
    a3.save(os.path.join(out, '%s_%s.jpg' % (L7, n)), quality=92); b3.save(os.path.join(out, '%s_%s.jpg' % (L8, n)), quality=92)
    h = max(a3.height, b3.height); s = Image.new('RGB', (a3.width + b3.width + 10, h), (255, 255, 255))
    s.paste(a3, (0, 0)); s.paste(b3, (a3.width + 10, 0))
    d = ImageDraw.Draw(s)
    d.rectangle((2, 2, 330, 18), fill=(0, 0, 0)); d.text((6, 4), '%s  %s %s' % (L7, i7, b7), fill=(255, 255, 255))
    d.rectangle((a3.width + 12, 2, a3.width + 340, 18), fill=(0, 0, 0)); d.text((a3.width + 16, 4), '%s  %s %s' % (L8, i8, b8), fill=(255, 255, 255))
    s.save(os.path.join(out, '%s_3x.jpg' % n), quality=90)
    print(n, s.size)
