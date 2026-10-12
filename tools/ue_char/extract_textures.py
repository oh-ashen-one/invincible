#!/usr/bin/env python3
"""Extract embedded GLB images to PNG for Unreal (UE can't read WebP). Derived files, git-ignored.
usage: extract_textures.py            -> hero/thug/suit/brute textures into art/night1/characters/<char>/tex/
Fan homage project; not official Marvel/Sony/Insomniac."""
import json, struct, os, subprocess, tempfile, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
WT = _P2WT
ART = WT + '/art/night1/characters'

def images(glb):
    b = open(glb, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + n]); off = 20 + n + 8
    for im in g.get('images', []):
        bv = g['bufferViews'][im['bufferView']]; s = off + bv.get('byteOffset', 0)
        yield im['name'], im.get('mimeType', ''), b[s:s + bv['byteLength']]

def to_png(data, dst, ext):
    if os.path.exists(dst):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=ext) as f:
        f.write(data); f.flush()
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f.name, '-frames:v', '1', dst], check=True)
    print(dst)

jobs = [('public/assets/spiderman.glb', 'hero'), ('public/assets/thug.glb', 'thug')]
jobs += [('public/assets/skins/%s.glb' % s, 'suits/' + s.capitalize()) for s in ('claude', 'codex', 'gemini', 'kimi', 'qwen')]
for glb, d in jobs:
    for name, mime, data in images(os.path.join(WT, glb)):
        to_png(data, '%s/%s/tex/%s.png' % (ART, d, name), '.webp' if 'webp' in mime else '.jpg')
for v in ('b', 'c'):
    to_png(open(WT + '/public/assets/tex/thug_basecolor_%s.webp' % v, 'rb').read(), '%s/thug/tex/thug_basecolor_%s.png' % (ART, v), '.webp')
to_png(open(WT + '/public/assets/enemies/brute_basecolor.webp', 'rb').read(), ART + '/thug/tex/brute_basecolor.png', '.webp')
# 4x4 white, imported linear/TC_MASKS as the M_Char_Suit ORM default (a masks sampler needs a masks texture)
_w = ART + '/shared/white.png'
if not os.path.exists(_w):
    os.makedirs(os.path.dirname(_w), exist_ok=True)
    from PIL import Image
    Image.new('RGB', (4, 4), (255, 255, 255)).save(_w)
