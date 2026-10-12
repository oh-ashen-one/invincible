#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 11 IP guard for the ORIGINAL hero suits (first-pass piece G, hard rule: never an official suit, emblem, web-line pattern or recognisable official colour blocking).

  python3 tools/ue_char/suits/ip_guard.py palette MAPS_DIR OUT.json          # colour blocking rules on the generated base colour maps + structural uniqueness
  python3 tools/ue_char/suits/ip_guard.py ocr OUT.json IMG [IMG ...]          # tesseract (4 quadrants, normal + inverted) on atlases / 4K captures against the denylist

palette rules (all measured on the covered texels of the hero atlas, hue bands as in eval/suit_distinct_r8.py):
  P1 no red-and-blue colour blocking: NOT (red >= 6 % and blue >= 6 %)       P2 red <= 6 %       P3 blue <= 6 %
  P4 no near-black body with white or red: NOT (black >= 35 % and (white >= 5 % or red >= 3 %))
  P5 no white-dominant body: white <= 25 %
  P6 distinct from every other suit: structural key (net kind, sash kind, glyph kind) unique AND palette distance to every other suit >= 38 (RGB units, weighted nearest centroid of the 3 heaviest non-dark k-means clusters)
  P7 glyph kind is on the allowed list (abstract marks only: no animal, letter, star, shield, crescent, bolt)
Exit code 1 when any rule fails.
"""
import sys, os, json, subprocess, tempfile
import numpy as np
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'suit8')); sys.path.insert(0, os.path.join(HERE, '..'))
ALLOWED_GLYPHS = {'hexvane', 'orbit', 'tally', 'lattice', 'gate', 'keystone', 'ladder', 'chevrons'}
EXTRA_DENY = ['SPIDER', 'SPIDEY', 'MARVEL', 'SONY', 'INSOMNIAC', 'WEB-SLINGER', 'AVENGERS', 'STARK', 'OSCORP', 'DAILY BUGLE', 'PARKER', 'MILES', 'VENOM', 'GWEN']


def load_cov(n=1024):
    import meshio
    m = meshio.load_body()
    tri, _, _, _ = meshio.raster_tri(m['UV'], m['F'], n)
    return tri >= 0, n


def hue_stats(path, cov, n):
    im = cv2.imread(path)[..., ::-1]
    im = cv2.resize(im, (n, n), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    h = hsv[..., 0] / 255 * 360; s = hsv[..., 1] / 255; v = hsv[..., 2] / 255
    sat = (s > 0.30) & (v > 0.18)
    def share(m): return float((m & cov).sum() / cov.sum())
    r = dict(red=share(sat & ((h < 18) | (h > 340))), blue=share(sat & (h > 205) & (h < 265)), white=share((s < 0.16) & (v > 0.78)), black=share(v < 0.16))
    px = im[cov].astype(np.float32)
    rs = np.random.RandomState(0)
    sel = px[rs.choice(len(px), min(60000, len(px)), replace=False)]
    from scipy.cluster.vq import kmeans2
    cen, lab = kmeans2(sel, 6, seed=1, minit='++')
    cnt = np.bincount(lab, minlength=6) / len(lab)
    order = np.argsort(-cnt)
    r['palette'] = [dict(rgb=[int(x) for x in cen[i]], share=round(float(cnt[i]), 3)) for i in order]
    return r


def lit(p):
    """The palette without its near-black clusters (every dark suit has ~50 % ink / deep panels: they say nothing about the design); shares renormalised."""
    q = [c for c in p if max(c['rgb']) > 70]
    t = sum(c['share'] for c in q) or 1.0
    return [dict(rgb=c['rgb'], share=c['share'] / t) for c in q][:3]


def pal_dist(a, b):
    """Weighted nearest-centroid distance between the lit parts of two palettes (symmetric, RGB units)."""
    a, b = lit(a), lit(b)
    def one(p, q):
        qa = np.array([c['rgb'] for c in q], float)
        return sum(c['share'] * np.min(np.linalg.norm(qa - np.array(c['rgb'], float), axis=1)) for c in p)
    return 0.5 * (one(a, b) + one(b, a))


def palette_cmd(maps, out):
    cfg = json.load(open(os.path.join(HERE, 'suits.json')))
    cov, n = load_cov()
    res = {}; fails = []
    for e in cfg['suits']:
        sid = e['id']
        p = '%s/%s_basecolor.png' % (maps, sid)
        if not os.path.exists(p): p = '%s/suit_basecolor_r8.png' % maps if e.get('texture_set') == 'hero' and os.path.exists('%s/suit_basecolor_r8.png' % maps) else p
        if not os.path.exists(p): fails.append((sid, 'missing basecolor map')); continue
        st = hue_stats(p, cov, n)
        sty = e.get('style', {})
        st['key'] = '%s|%s|%s' % (sty.get('net', {}).get('kind', 'diamond'), sty.get('sash', {}).get('kind', 'slash'), sty.get('glyph', {}).get('kind', 'hexvane'))
        gk = sty.get('glyph', {}).get('kind', 'hexvane')
        rules = {
            'P1_no_red_and_blue': not (st['red'] >= 0.06 and st['blue'] >= 0.06), 'P2_red_le_6pct': st['red'] <= 0.06, 'P3_blue_le_6pct': st['blue'] <= 0.06,
            'P4_no_black_with_white_or_red': not (st['black'] >= 0.35 and (st['white'] >= 0.05 or st['red'] >= 0.03)), 'P5_white_le_25pct': st['white'] <= 0.25,
            'P7_glyph_allowed': gk in ALLOWED_GLYPHS}
        st['rules'] = rules
        res[sid] = st
        for k, v in rules.items():
            if not v: fails.append((sid, k))
    ids = list(res)
    keys = {}
    for i in ids: keys.setdefault(res[i]['key'], []).append(i)
    for k, v in keys.items():
        if len(v) > 1: fails.append((','.join(v), 'P6 structural key not unique: ' + k))
    pairs = {}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            d = pal_dist(res[a]['palette'], res[b]['palette'])
            pairs['%s|%s' % (a, b)] = round(d, 1)
            if d < 38: fails.append(('%s,%s' % (a, b), 'P6 palette distance %.1f < 38' % d))
    json.dump(dict(suits=res, palette_distance=pairs, fails=[list(f) for f in fails], n_suits=len(ids)), open(out, 'w'), indent=1)
    for i in ids:
        s = res[i]
        print('%-8s red %.3f blue %.3f white %.3f black %.3f  %s  %s' % (i, s['red'], s['blue'], s['white'], s['black'], s['key'], 'PASS' if all(s['rules'].values()) else 'FAIL'))
    print('min palette distance %.1f over %d pairs' % (min(pairs.values()) if pairs else 0, len(pairs)))
    print('FAILS:', fails or 'none')
    return 1 if fails else 0


def ocr_text(img):
    from PIL import Image, ImageOps
    tmp = tempfile.mkdtemp(); txt = ''
    for inv in (False, True):
        v = ImageOps.invert(img.convert('RGB')).convert('L') if inv else img.convert('L'); v = v.resize((v.width * 2, v.height * 2))
        p = os.path.join(tmp, 'c.png'); v.save(p)
        txt += ' ' + subprocess.run(['tesseract', p, '-', '--psm', '11'], capture_output=True, text=True).stdout.upper()
    return txt


def ocr_cmd(out, imgs):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    deny = list(json.load(open(os.path.join(HERE, '..', '..', '..', 'docs', 'night1', 'city', 'spec_regions.json')))['ip_denylist']) + EXTRA_DENY
    res = {}; bad = 0
    for f in imgs:
        im = Image.open(f); W, H = im.size
        hits = set(); words = set()
        step = 2 if W > 2000 else 1
        boxes = [(0, 0, W, H)] if step == 1 else [(x, y, x + W // 2, y + H // 2) for x in (0, W // 2) for y in (0, H // 2)]
        for b in boxes:
            t = ocr_text(im.crop(b))
            hits |= {d for d in deny if d in t}
            words |= {w for w in ''.join(c if c.isalpha() else ' ' for c in t).split() if len(w) >= 4}
        res[os.path.basename(f)] = dict(denylist_hits=sorted(hits), words_ge4=sorted(words)[:40])
        bad += len(hits)
        print(os.path.basename(f), 'HITS ' + str(sorted(hits)) if hits else 'clean', '| words>=4:', sorted(words)[:12])
    json.dump(dict(total_hits=bad, deny_terms=len(deny), images=res), open(out, 'w'), indent=1)
    print('TOTAL HITS', bad)
    return 1 if bad else 0


if __name__ == '__main__':
    if sys.argv[1] == 'palette': sys.exit(palette_cmd(sys.argv[2], sys.argv[3]))
    if sys.argv[1] == 'ocr': sys.exit(ocr_cmd(sys.argv[2], sys.argv[3:]))
    print(__doc__)
