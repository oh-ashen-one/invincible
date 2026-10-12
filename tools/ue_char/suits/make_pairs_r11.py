# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 11 (piece G, hero skins): pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private
~/spiderman-learnings/refs (never committed; the reference only shows what a 4K suit render of the real game looks like, our suits are original) or the previous round's capture.

  python3 tools/ue_char/suits/make_pairs_r11.py <round-11 dir> <out pairs.json>
"""
import json, os, sys
r11, out = sys.argv[1:3]
R = '/Users/midir/spiderman-learnings/refs/'
R8 = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-08/captures/'
S = os.path.join(r11, 'stills')
pairs = []
def have(p): return os.path.exists(p)
def add(i, x, y, note):
    if have(x) and have(y): pairs.append(dict(id=i, x=x, y=y, note=note))
    else: print('skipped (missing file)', i, x if not have(x) else y)
S4 = os.environ.get('STILLS_4K', '/Users/midir/sm2-n1/_scratch/characters/r11/chain4/stills_a')     # the 4K originals of the back / head stills (the repo keeps those two views at 1080p)
def st(s, v):
    for d, suffix in ((S, '4k'), (S4, '4k'), (S, '1080p')):
        p = os.path.join(d, 'skin_%s_%s_%s.jpg' % (s, v, suffix))
        if os.path.exists(p): return p
    return os.path.join(S, 'skin_%s_%s_4k.jpg' % (s, v))
refs = ['characters/hero-idle-street-og__og_0000.jpg', 'characters/hero-idle-crosswalk-night__nt_0945.jpg', 'characters/hero-rooftop-miles__gr_0202.jpg', 'characters/hero-run-street-dn__dn_1115.jpg']
for i, s in enumerate(('tessera', 'verdant', 'plum', 'glacier')):
    add('suit-full-%s' % s, st(s, 'front'), R + refs[i], 'masked acrobat hero in a fitted suit, full body, standing: judge the suit as a 4K render (fabric, seams, line work, shading, texture sharpness, any seam or smear). ALSO say whether the suit design resembles any existing licensed costume')
for s in ('ash', 'saffron', 'sage', 'cinder'):
    add('suit-back-%s' % s, st(s, 'back'), R + 'characters/hero-run-street-dn__dn_1115.jpg', 'masked hero seen from behind, in a fitted suit: judge suit texture quality, line work, seams, shading; any resemblance to an existing licensed costume?')
add('suit-chest-tessera', st('tessera', 'chest'), R + 'characters/press-suit-closeup-fire__psblog_14.jpg', 'suit chest close-up: weave, raised lines, stitching, emblem, shading')
add('suit-chest-plum', st('plum', 'chest'), R + 'characters/suits-duo-closeup__gr_1003.jpg', 'suit chest close-up: weave, raised lines, stitching, emblem, shading')
add('suit-chest-cinder', st('cinder', 'chest'), R + 'characters/suits-duo-closeup-2__gr_1010.jpg', 'suit chest close-up: line work, stitching, emblem, shading')
add('suit-head-tessera', st('tessera', 'head'), R + 'characters/miles-face-closeup__gr_0230.jpg', 'masked head close-up: hood, lens, vents, texture sharpness, seams')
add('suit-head-verdant', st('verdant', 'head'), R + 'characters/miles-closeup-trailer__st_0106.jpg', 'masked head close-up: hood, lens, vents, texture sharpness, seams')
add('swatch-sheet', os.path.join(r11, 'SWATCH_SHEET.jpg'), R + 'characters/suits-render-trailer__eny_0200.jpg', 'a set of hero suit designs shown side by side: judge variety and polish; is any design a copy of an existing licensed costume, emblem or colour scheme?')
add('suit-swap-clip', os.path.join(r11, 'swap_pawn_T_key.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'a masked hero running in a fitted suit (the suit may change colour scheme between cuts or mid-clip): judge suit render quality in motion and how clean any suit change looks')
add('orbit-all-suits', os.path.join(r11, 'orbit_all_suits.mp4'), R + 'animation/clips/run-toward-camera__dn_0418-0425.mp4', 'a masked hero in a fitted suit seen in 3D, the suit design changing every 1.5 s: judge render quality, sharpness, any streaming blur or stray objects in frame')
# previous round vs this round: the same Tessera suit (round 08 turntable vs the round-11 front still)
add('progress-tessera', st('tessera', 'front'), R8 + 'hero_turntable_4k.jpg', 'two renders of the same masked hero suit: judge any difference in texture sharpness, line work, seams, lighting')
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
