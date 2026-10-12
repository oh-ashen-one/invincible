#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 16 (piece G, hero skins; = make_pairs_r15.py with the progress pairs against the MERGED round-14 baseline - lossless 4K originals - plus r15 -> r16 pairs on the four r15 defects): pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private
~/spiderman-learnings/refs (never committed) or the previous round's capture.  Every axis of the merged round-08 [5,5,5,5,5] gets fresh evidence: suit stills
(CH1-framed fronts, backs, chest, head), the stage-hero run / chase clips, the swap movie, the 7-enemy lineup still, the fight clip and the crowd clip.

  python3 tools/ue_char/suits/make_pairs_r16.py <round-16 dir> <out pairs.json>
"""
import json, os, sys
r12, out = sys.argv[1:3]      # (the variable keeps its r12 name: it is the CURRENT round directory)
R = '/Users/midir/spiderman-learnings/refs/'
R13 = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-14/'      # the MERGED skins baseline (round 14) - the progress pairs' y
R15D = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-15/'
P14 = os.environ.get('STILLS_R14', '/Users/midir/sm2-n1/_scratch/characters/r14/chain1/run/stills')
P15 = os.environ.get('STILLS_R15', '/Users/midir/sm2-n1/_scratch/characters/r15/chain1/run/stills')
S = os.path.join(r12, 'stills')
S4 = os.environ.get('STILLS_4K', '/Users/midir/sm2-n1/_scratch/characters/r16/chain1/run/stills')
pairs = []
def have(p): return os.path.exists(p)
R12DIR = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-15/'      # round 16: clips not re-shot this round (stage-hero run / chase, fight, crowd: content unchanged) come from round 15 - disclosed in CAPTURES.md
def cur(name):
    """this round's file, else the round-15 file of the same name (clips whose content is unchanged, when a round-16 re-shoot is not in the round dir)"""
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
# progress: the merged round 14 vs this round (lossless 4K originals of both, same camera, same suit), and round 15 vs round 16 on the four r15 defects
def stp(s_, v):      # this round's lossless original (the progress pairs compare PNG with PNG)
    p = os.path.join(S4, 'skin_%s_%s_4k.png' % (s_, v))
    return p if os.path.exists(p) else st(s_, v)
def prev(name, d=None):
    d = d or P14
    p = os.path.join(d, name + '.png')
    return p if os.path.exists(p) else R13 + 'stills/' + name + '.jpg'
TWO = 'two renders of the same suit from the same camera: which one is better (sculpted brow / nose bridge / cheeks / chin, lenses and rim, seam, sash ends, armpit, shoulders, trapezius), and say what differs'
BACK = 'two renders of the same suit from BEHIND, same camera: which is better? Does either show the FRONT emblem or the front sash repeated on the back, as if projected through the torso? judge line work, seams, shading'
for s_ in ('tessera', 'plum', 'verdant', 'cinder', 'ash', 'saffron', 'glacier', 'sage'):
    add('progress-back-%s' % s_, stp(s_, 'back'), prev('skin_%s_back_4k' % s_), BACK)
CHJ = TWO + ' (look at the torso side under the arm: does any cord or groove line make a stair-step / jog where it crosses the side, or meets a panel border? any smear or notch?)'
for s_ in ('verdant', 'ash', 'cinder', 'tessera'):
    add('progress-chest-%s' % s_, stp(s_, 'chest'), prev('skin_%s_chest_4k' % s_), CHJ)
HF = TWO + ' (straight-on face: is the centre seam a straight line or does it zig-zag / jog at the brow, the nose, the mouth?)'
for s_ in ('cinder', 'tessera', 'plum', 'glacier'):
    add('progress-headfront-%s' % s_, stp(s_, 'headfront'), prev('skin_%s_headfront_4k' % s_), HF)
add('progress-head-tessera', stp('tessera', 'head'), prev('skin_tessera_head_4k'), TWO)
add('progress-profile-verdant', stp('verdant', 'headside'), prev('skin_verdant_headside_4k'), 'two profile renders of the same head from the same camera: in which does the brow overhang the lens rim (the rim sits BEHIND the brow, not proud of it), and in which is the hood trim over the brow sharp rather than smeared')
add('progress-head-sage', stp('sage', 'head34'), prev('skin_sage_head34_4k'), TWO + ' (look at the neck / trapezius creases too)')
add('progress-swap-pawn', os.path.join(r12, 'swap_pawn_T_key.mp4'), R13 + 'swap_pawn_T_key.mp4', 'two captures of the playable hero starting to run: which has a smoother start (no pose pop in the first 0.3 s, no snap from idle to run), and judge the suit render quality in motion')
add('progress-lineup', os.path.join(r12, 'enemy_lineup_4k.jpg'), R13 + 'enemy_lineup_4k.jpg', 'two versions of the same enemy lineup: count the enemies, judge the weapons in their hands, the lighting / exposure, the variety of outfits')
# the previous round (r15) vs this round (r16): the defects the r15 critic named
add('r15-back-tessera', stp('tessera', 'back'), prev('skin_tessera_back_4k', P15), BACK)
add('r15-chest-verdant', stp('verdant', 'chest'), prev('skin_verdant_chest_4k', P15), CHJ)
add('r15-headfront-cinder', stp('cinder', 'headfront'), prev('skin_cinder_headfront_4k', P15), HF)
add('r15-chest-ash', stp('ash', 'chest'), prev('skin_ash_chest_4k', P15), CHJ)
if os.environ.get('LINEUP34'): add('enemy-lineup-34', os.path.join(r12, 'enemy_lineup_34_4k.jpg'), R + 'characters/thugs-group-nm__nm_0049.jpg', 'a lineup of street enemies seen three-quarter: judge variety, weapons held in the hands (gripped or floating / piercing the fingers), faces, cloth, lighting')
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
