#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 15 (piece G, hero skins): pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private
~/spiderman-learnings/refs (never committed) or the previous round's capture.  Every axis of the merged round-08 [5,5,5,5,5] gets fresh evidence: suit stills
(CH1-framed fronts, backs, chest, head), the stage-hero run / chase clips, the swap movie, the 7-enemy lineup still, the fight clip and the crowd clip.

  python3 tools/ue_char/suits/make_pairs_r15.py <round-15 dir> <out pairs.json>
"""
import json, os, sys
r12, out = sys.argv[1:3]      # (the variable keeps its r12 name: it is the CURRENT round directory)
R = '/Users/midir/spiderman-learnings/refs/'
R13 = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-14/'      # the previous round's captures (the variable keeps its r13 name)
S = os.path.join(r12, 'stills')
S4 = os.environ.get('STILLS_4K', '/Users/midir/sm2-n1/_scratch/characters/r15/chain1/run/stills')
pairs = []
def have(p): return os.path.exists(p)
R12DIR = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-12/'
def cur(name):
    """this round's file, else the round-12 file of the same name (clips whose content is unchanged since r10 / r12 when a round-13 re-shoot is not in the round dir)"""
    p = os.path.join(r12, name)
    return p if os.path.exists(p) else R12DIR + name
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
for i, s_ in enumerate(('tessera', 'cinder', 'saffron', 'ash')):
    add('suit-full-%s' % s_, st(s_, 'front'), R + refs[i], SUIT_NOTE)
for s_ in ('plum', 'glacier', 'sage', 'tessera'):
    add('suit-back-%s' % s_, st(s_, 'back'), R + 'characters/hero-run-street-dn__dn_1115.jpg', 'masked hero seen from behind, in a fitted suit: judge suit texture quality, raised line work, seams, shading; any resemblance to an existing licensed costume?')
CH = 'suit chest close-up at 4K: is the line work RAISED (lit edge + shadow edge on every line) or flat print; is EVERY end of the sash / chevron panel finished (border cord, stitching, piping) or raw; any faceted shading patches, folds, zigzag stitches or stair-stepped edges near the armpit; faceted shoulder silhouette; weave continuity'
add('suit-chest-tessera', st('tessera', 'chest'), R + 'characters/press-suit-closeup-fire__psblog_14.jpg', CH)
add('suit-chest-ash', st('ash', 'chest'), R + 'characters/suits-duo-closeup__gr_1003.jpg', CH)
add('suit-chest-cinder', st('cinder', 'chest'), R + 'characters/suits-duo-closeup-2__gr_1010.jpg', CH)
add('suit-chest-verdant', st('verdant', 'chest'), R + 'characters/suits-duo-closeup-2__gr_1010.jpg', CH)
HEAD = 'masked head close-up at 4K: is the head SCULPTED (a brow ridge that overhangs the lenses, eye sockets, a recessed nose bridge and a nose, cheek bones, a mouth bulge, a chin plane) or a smooth sock; are the lenses large and seated under the brow with ONE closed raised rim and a curved glossy surface; is the face seam raised piping or black ink; does the relief READ on this hood colour; any resemblance to an existing licensed mask?'
add('suit-head-tessera', st('tessera', 'headfront'), R + 'characters/miles-face-closeup__gr_0230.jpg', HEAD + ' (straight on)')
add('suit-head-tessera-12deg', st('tessera', 'head'), R + 'characters/miles-closeup-trailer__st_0106.jpg', HEAD)
add('suit-head-cinder', st('cinder', 'headfront'), R + 'characters/press-suit-closeup-fire__psblog_14.jpg', HEAD + ' (formerly a near-black hood: does the relief read now?)')
add('suit-head-cinder-25deg', st('cinder', 'head34'), R + 'characters/miles-face-closeup__gr_0230.jpg', HEAD)
add('suit-head-glacier', st('glacier', 'head'), R + 'characters/suits-duo-closeup__gr_1003.jpg', HEAD)
add('suit-head-plum', st('plum', 'head'), R + 'characters/symbiote-lens-extreme-closeup__gr_1016.jpg', HEAD)
add('suit-head-sage-34', st('sage', 'head34'), R + 'characters/miles-face-closeup__gr_0230.jpg', HEAD + ' ALSO the neck / trapezius at the bottom: any torn creases or grooves?')
PROF = 'masked head in PROFILE: does the silhouette show a brow ridge, a recessed nose bridge (a notch between brow and nose), a nose, a mouth, a chin plane, or a smooth egg with a ramp?'
add('suit-head-verdant-profile', st('verdant', 'headside'), R + 'characters/miles-closeup-trailer__st_0106.jpg', PROF)
add('suit-head-tessera-profile', st('tessera', 'headside'), R + 'characters/miles-face-closeup__gr_0230.jpg', PROF)
add('suit-head-cinder-profile', st('cinder', 'headside'), R + 'characters/miles-closeup-trailer__st_0106.jpg', PROF + ' (dark mask)')
add('swatch-sheet', os.path.join(r12, 'SWATCH_SHEET.jpg'), R + 'characters/suits-render-trailer__eny_0200.jpg', 'a set of hero suit designs shown side by side: judge variety and polish; is any design a copy of an existing licensed costume, emblem or colour scheme?')
add('suit-swap-clip', os.path.join(r12, 'swap_pawn_T_key.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'the PLAYABLE hero running, its suit changed by key presses: judge suit render quality in motion, how clean each change looks, the run cadence and any pose pop at the start')
add('hero-run-side', cur('hero_run_side.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'a masked hero running past a side-tracking camera: judge step cadence, torso lean, arm swing, foot planting, transitions, suit quality in motion')
add('hero-run-chase', cur('hero_run_chase.mp4'), R + 'animation/clips/run-toward-camera__dn_0418-0425.mp4', 'a masked hero running, gameplay chase camera: judge cadence, lean, framing (hero size in frame), blends, suit in motion')
add('orbit-all-suits', os.path.join(r12, 'orbit_all_suits.mp4'), R + 'streets/clips/street-life-pedestrians__dn_0712-0721.mp4', 'a masked hero in a fitted suit seen in 3D, the suit design changing every 1.5 s: judge render quality, sharpness, raised line work, folds at the armpit, faceted shoulders, stray objects')
add('enemy-lineup', os.path.join(r12, 'enemy_lineup_4k.jpg'), R + 'characters/thugs-close-nm__nm_0947.jpg', 'a lineup of street enemies: judge variety of outfits / silhouettes / weapons, modelled faces, hands, cloth, shoes, image quality at 4K')
add('fight-clip', cur('street_fight_wide.mp4'), R + 'combat/clips/plaza-fight__dn_0818-0828.mp4', 'a staged street fight, hero vs a group: judge enemy count / size in frame, hit reactions, knockdowns, choreography readability, animation quality')
add('crowd-clip', cur('crowd_tracking.mp4'), R + 'streets/clips/street-life-pedestrians__dn_0712-0721.mp4', 'pedestrians on a sidewalk, tracking camera: judge density, variety of people, gait (no gliding / lockstep), clothing, faces')
# previous round (r14) vs this round (r15): the same camera, the same suit
def prev(name):
    for d in (R13 + 'stills/',):
        for ext in ('jpg',):
            p = d + name + '.' + ext
            if os.path.exists(p): return p
    return R13 + 'stills/' + name + '.jpg'
TWO = 'two renders of the same suit from the same camera: which one is better (sculpted brow / nose bridge / cheeks / chin, lenses and rim, seam, sash ends, armpit, shoulders, trapezius), and say what differs'
add('progress-head-tessera', st('tessera', 'head'), prev('skin_tessera_head_4k'), TWO)
add('progress-profile-verdant', st('verdant', 'headside'), prev('skin_verdant_headside_4k'), 'two profile renders of the same head from the same camera: in which does the brow overhang the lens rim (the rim sits BEHIND the brow, not proud of it), and in which is the hood trim over the brow sharp rather than smeared')
add('progress-profile-tessera', st('tessera', 'headside'), prev('skin_tessera_headside_4k'), 'two profile renders of the same head from the same camera: in which does the brow overhang the lens rim, is the eye seated deeper in a socket under the brow, is the profile still a head and not a mask over a sock')
add('progress-profile-ash', st('ash', 'headside'), prev('skin_ash_headside_4k'), 'two profile renders of the same head from the same camera: which has the lens rim further behind the brow, and which has the sharper hood trim')
add('progress-chest-verdant', st('verdant', 'chest'), prev('skin_verdant_chest_4k'), TWO + ' (look at the armpit: is the amber piping cord pinched / broken where the arm meets the torso? do the net lines end on a seam cord or fade out in the open fabric?)')
add('progress-swap-pawn', os.path.join(r12, 'swap_pawn_T_key.mp4'), R13 + 'swap_pawn_T_key.mp4', 'two captures of the playable hero starting to run: which has a smoother start (no pose pop in the first 0.3 s, no snap from idle to run), and judge the suit render quality in motion')
add('progress-head-cinder', st('cinder', 'head34'), prev('skin_cinder_head34_4k'), TWO + ' (dark mask: does the relief read?)')
add('progress-head-sage', st('sage', 'head34'), prev('skin_sage_head34_4k'), TWO + ' (look at the neck / trapezius creases too)')
add('progress-chest-ash', st('ash', 'chest'), prev('skin_ash_chest_4k'), TWO + ' (is the accent pipe at the sash end attached to the end, or floating off it? do the net lines end on a seam cord?)')
add('progress-chest-cinder', st('cinder', 'chest'), prev('skin_cinder_chest_4k'), TWO + ' (are the shoulders faceted?)')
add('progress-lineup', os.path.join(r12, 'enemy_lineup_4k.jpg'), R13 + 'enemy_lineup_4k.jpg', 'two versions of the same enemy lineup: count the enemies, judge the weapons in their hands, the lighting / exposure, the variety of outfits')
if os.environ.get('LINEUP34'): add('enemy-lineup-34', os.path.join(r12, 'enemy_lineup_34_4k.jpg'), R + 'characters/thugs-group-nm__nm_0049.jpg', 'a lineup of street enemies seen three-quarter: judge variety, weapons held in the hands (gripped or floating / piercing the fingers), faces, cloth, lighting')
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
