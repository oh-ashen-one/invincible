# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private ~/spiderman-learnings/refs
(never committed) or the previous round's capture of the same view.

  python3 tools/ue_char/make_pairs_r8.py <round08 captures dir> <round07 captures dir> <crops dir> <out pairs.json>
"""
import json, os, sys
cap, prev, crops, out = sys.argv[1:5]
R = '/Users/midir/spiderman-learnings/refs/'
pairs = []
def have(p): return os.path.exists(p)
def add(i, x, y, note):
    if have(x) and have(y): pairs.append(dict(id=i, x=x, y=y, note=note))
    else: print('skipped (missing file)', i, x if not have(x) else y)
c = lambda n: os.path.join(cap, n); p = lambda n: os.path.join(prev, n)
add('hero-run', c('hero_run_side.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'masked acrobat hero running, full body')
add('hero-chase', c('hero_run_chase.mp4'), R + 'animation/clips/run-toward-camera__dn_0418-0425.mp4', 'hero running away from a chase camera behind')
add('hero-standing', c('hero_turntable_4k.jpg'), R + 'characters/hero-idle-street-og__og_0000.jpg', 'hero full body on a street')
add('suit-close', c('suit_closeup_4k.jpg'), R + 'characters/press-suit-closeup-fire__psblog_14.jpg', 'suit fabric close-up')
add('hero-face', c('hero_face_lens_4k.jpg'), R + 'characters/miles-face-closeup__gr_0230.jpg', 'mask and eye lens close-up')
add('thugs-group', c('street_fight_wide_4k.jpg'), R + 'characters/thugs-group-nm__nm_0049.jpg', 'a group of street criminals around the hero')
add('fight-clip', c('street_fight_34.mp4'), R + 'combat/clips/street-combo__nm_0214-0224.mp4', 'hero among a group of thugs, mid camera above')
add('thug-close', c('thug_face_4k.jpg'), R + 'characters/thug-closeup-dn__dn_0523.jpg', 'street criminal close-up')
add('citizens-clip', c('crowd_tracking.mp4'), R + 'characters/clips/street-npcs-idle__dn_0600-0608.mp4', 'pedestrians near the camera')
add('citizens-still', c('crowd_tracking_4k.jpg'), R + 'characters/npc-group-dn__dn_0725.jpg', 'a group of pedestrians on a street')
# previous round vs this round (targets of round 08: the original suit, the closed eye rims, the crowd heads)
add('progress-hero-face', c('hero_face_lens_4k.jpg'), p('hero_face_lens_4k.jpg'), 'two versions of the same hero mask close-up (eye lens and rim): judge the lens sitting inside the head, any background showing between rim and lens, and any lens beyond the mask outline')
add('progress-hero-standing', c('hero_turntable_4k.jpg'), p('hero_turntable_4k.jpg'), 'two versions of the same hero, full body: judge whether either suit copies a well-known existing suit design (layout, emblem, colour blocking, web pattern)')
add('progress-suit-close', c('suit_closeup_4k.jpg'), p('suit_closeup_4k.jpg'), 'two versions of the same suit close-up: judge line quality (stair-stepped or wobbling lines), emblem and panel originality')
add('progress-crowd-still', c('crowd_tracking_4k.jpg'), p('crowd_tracking_4k.jpg'), 'two versions of our pedestrians (still): judge fused or overlapping heads')
add('progress-thug-collar', c('thug_face_4k.jpg'), p('thug_face_4k.jpg'), 'two versions of the same street criminal close-up: judge jagged skin-coloured shards at the jacket collar')
add('progress-tee-mask', c('tee_face_4k.jpg'), p('tee_face_4k.jpg'), 'two versions of the same masked face: judge lips or a mouth slit showing through the cloth mask')
for n, note in (('hero-eye-3x', 'hero eye, 3x crop, two versions: judge background pixels between rim and lens, and any lens reaching beyond the mask outline'),
                ('hero-lines-3x', 'hero suit line work, 3x crop, two versions: judge stair-stepped lines'),
                ('thug-collar-3x', 'street criminal collar, 3x crop, two versions: judge jagged shards'),
                ('tee-mouth-3x', 'masked face mouth area, 3x crop, two versions: judge lips showing through the mask'),
                ('crowd-heads-3x', 'two pedestrians heads, 3x crop, two versions: judge fused heads')):
    b = n[:-3] if n.endswith('-3x') else n      # crop files are r7_<name>.jpg / r8_<name>.jpg (crops_r8.py)
    add(n, os.path.join(crops, 'r8_%s.jpg' % b), os.path.join(crops, 'r7_%s.jpg' % b), note)
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
