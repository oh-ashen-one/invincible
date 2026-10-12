#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 12 (piece G, hero skins): pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private
~/spiderman-learnings/refs (never committed) or the previous round's capture.  Every axis of the merged round-08 [5,5,5,5,5] gets fresh evidence: suit stills
(CH1-framed fronts, backs, chest, head), the stage-hero run / chase clips, the swap movie, the 7-enemy lineup still, the fight clip and the crowd clip.

  python3 tools/ue_char/suits/make_pairs_r12.py <round-12 dir> <out pairs.json>
"""
import json, os, sys
r12, out = sys.argv[1:3]
R = '/Users/midir/spiderman-learnings/refs/'
R11 = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-11/stills/'
S = os.path.join(r12, 'stills')
S4 = os.environ.get('STILLS_4K', '/Users/midir/sm2-n1/_scratch/characters/r12/chainA/stills')
pairs = []
def have(p): return os.path.exists(p)
def add(i, x, y, note):
    if have(x) and have(y): pairs.append(dict(id=i, x=x, y=y, note=note))
    else: print('skipped (missing file)', i, x if not have(x) else y)
def st(s, v):
    for d, suffix, ext in ((S, '4k', 'jpg'), (S4, '4k', 'png'), (S, '1080p', 'jpg')):
        p = os.path.join(d, 'skin_%s_%s_%s.%s' % (s, v, suffix, ext))
        if os.path.exists(p): return p
    return os.path.join(S, 'skin_%s_%s_4k.jpg' % (s, v))
SUIT_NOTE = 'masked acrobat hero in a fitted suit, full body, standing: judge the suit as a 4K render (fabric, raised piping / seams, line work, shading, texture sharpness, any seam, fold or smear) and the hero\'s size in frame. ALSO say whether the suit design resembles any existing licensed costume'
refs = ['characters/hero-idle-street-og__og_0000.jpg', 'characters/hero-idle-crosswalk-night__nt_0945.jpg', 'characters/hero-rooftop-miles__gr_0202.jpg', 'characters/hero-run-street-dn__dn_1115.jpg']
for i, s in enumerate(('tessera', 'verdant', 'saffron', 'ash')):
    add('suit-full-%s' % s, st(s, 'front'), R + refs[i], SUIT_NOTE)
for s in ('plum', 'glacier', 'sage', 'cinder'):
    add('suit-back-%s' % s, st(s, 'back'), R + 'characters/hero-run-street-dn__dn_1115.jpg', 'masked hero seen from behind, in a fitted suit: judge suit texture quality, raised line work, seams, shading; any resemblance to an existing licensed costume?')
CH = 'suit chest close-up at 4K: is the line work RAISED (lit edge + shadow edge on every line) or flat print; do any lines show through the sash / chevron panels; any faceted shading patches, folds or stair-stepped edges near the armpit; weave continuity'
add('suit-chest-tessera', st('tessera', 'chest'), R + 'characters/press-suit-closeup-fire__psblog_14.jpg', CH)
add('suit-chest-ash', st('ash', 'chest'), R + 'characters/suits-duo-closeup__gr_1003.jpg', CH)
add('suit-chest-verdant', st('verdant', 'chest'), R + 'characters/suits-duo-closeup-2__gr_1010.jpg', CH)
add('suit-head-tessera', st('tessera', 'head'), R + 'characters/miles-face-closeup__gr_0230.jpg', 'masked head close-up: hood, lens, vents, texture sharpness, seams')
add('swatch-sheet', os.path.join(r12, 'SWATCH_SHEET.jpg'), R + 'characters/suits-render-trailer__eny_0200.jpg', 'a set of hero suit designs shown side by side: judge variety and polish; is any design a copy of an existing licensed costume, emblem or colour scheme?')
add('suit-swap-clip', os.path.join(r12, 'swap_pawn_T_key.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'the PLAYABLE hero running, its suit changed by key presses: judge suit render quality in motion, how clean each change looks, the run cadence and any pose pop at the start')
add('hero-run-side', os.path.join(r12, 'hero_run_side.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'a masked hero running past a side-tracking camera: judge step cadence, torso lean, arm swing, foot planting, transitions, suit quality in motion')
add('hero-run-chase', os.path.join(r12, 'hero_run_chase.mp4'), R + 'animation/clips/run-toward-camera__dn_0418-0425.mp4', 'a masked hero running, gameplay chase camera: judge cadence, lean, framing (hero size in frame), blends, suit in motion')
add('orbit-all-suits', os.path.join(r12, 'orbit_all_suits.mp4'), R + 'streets/clips/street-life-pedestrians__dn_0712-0721.mp4', 'a masked hero in a fitted suit seen in 3D, the suit design changing every 1.5 s: judge render quality, sharpness, raised line work, folds at the armpit, stray objects')
add('enemy-lineup', os.path.join(r12, 'enemy_lineup_4k.jpg'), R + 'characters/thugs-close-nm__nm_0947.jpg', 'a lineup of street enemies: judge variety of outfits / silhouettes / weapons, modelled faces, hands, cloth, shoes, image quality at 4K')
add('fight-clip', os.path.join(r12, 'street_fight_wide.mp4'), R + 'combat/clips/plaza-fight__dn_0818-0828.mp4', 'a staged street fight, hero vs a group: judge enemy count / size in frame, hit reactions, knockdowns, choreography readability, animation quality')
add('crowd-clip', os.path.join(r12, 'crowd_tracking.mp4'), R + 'streets/clips/street-life-pedestrians__dn_0712-0721.mp4', 'pedestrians on a sidewalk, tracking camera: judge density, variety of people, gait (no gliding / lockstep), clothing, faces')
# previous round vs this round: the same Tessera chest view (round 11 flat print vs round 12 raised piping)
add('progress-tessera-chest', st('tessera', 'chest'), R11 + 'skin_tessera_chest_4k.jpg', 'two renders of the same suit chest: judge raised vs flat line work, lines showing through the bandolier, faceted shading or stair steps near the armpit, sharpness')
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
