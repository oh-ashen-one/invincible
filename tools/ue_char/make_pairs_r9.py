# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 09: pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private ~/spiderman-learnings/refs
(never committed) or the previous round's capture of the same view.

  python3 tools/ue_char/make_pairs_r9.py <round09 captures dir> <round08 captures dir> <crops dir> <out pairs.json>
The hero / crowd-key captures of round 08 are current (nothing of the hero changed this round) and are used unchanged for the standing reference pairs.
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
# the round target: real combat reactions (hit reactions, knockdown, nobody idle)
add('fight-clip-34', c('street_fight_34.mp4'), R + 'combat/clips/street-combo__nm_0214-0224.mp4', 'hero among a group of street criminals, mid camera above: judge hit reactions, knockdowns and whether any of them stands idle')
add('fight-clip-cars', c('street_fight_34.mp4'), R + 'combat/clips/street-fight-cars__nm_0500-0510.mp4', 'hero fighting a group of criminals: judge enemy reactions to hits, knockdown and recovery')
add('fight-clip-wide', c('street_fight_wide.mp4'), R + 'combat/clips/plaza-fight__dn_0818-0828.mp4', 'hero and a group of enemies closing in and trading blows, wide camera')
add('fight-orbit', c('street_fight_orbit.mp4'), R + 'combat/clips/street-fight-cars__nm_0500-0510.mp4', 'orbiting camera around a hero fighting a group')
add('enemy-knockdown', c('street_fight_34_4k.jpg'), R + 'combat/enemy-launched-og__og_0149.jpg', 'an enemy knocked to the ground by the hero: judge the pose, the contact with the ground and the other enemies')
add('thugs-group', c('street_fight_wide_4k.jpg'), R + 'characters/thugs-group-nm__nm_0049.jpg', 'a group of street criminals around the hero')
add('thug-close', c('thug_face_4k.jpg'), R + 'characters/thug-closeup-dn__dn_0523.jpg', 'street criminal close-up')
add('citizens-clip', c('crowd_tracking.mp4'), R + 'characters/clips/street-npcs-idle__dn_0600-0608.mp4', 'pedestrians near the camera')
add('citizens-still', c('crowd_tracking_4k.jpg'), R + 'characters/npc-group-dn__dn_0725.jpg', 'a group of pedestrians on a street')
# hero: unchanged since round 08 (its captures stand)
add('hero-run', p('hero_run_side.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'masked acrobat hero running, full body')
add('hero-standing', p('hero_turntable_4k.jpg'), R + 'characters/hero-idle-street-og__og_0000.jpg', 'hero full body on a street')
add('hero-face', p('hero_face_lens_4k.jpg'), R + 'characters/miles-face-closeup__gr_0230.jpg', 'mask and eye lens close-up')
# previous round vs this round
add('progress-fight', c('street_fight_34.mp4'), p('street_fight_34.mp4'), 'two versions of the same staged street fight (same camera): judge hit reactions, knockdowns and idle enemies')
add('progress-fight-still', c('street_fight_34_4k.jpg'), p('street_fight_34_4k.jpg'), 'two versions of the same fight, one frame: judge what the enemies are doing')
add('progress-tee-mask', c('tee_face_4k.jpg'), p('tee_face_4k.jpg'), 'two versions of the same masked face: judge holes through the cloth mask (background showing through)')
add('progress-thug-collar', c('thug_face_4k.jpg'), p('thug_face_4k.jpg'), 'two versions of the same street criminal close-up: judge a skin-coloured wedge at the jacket collar')
add('progress-crowd', c('crowd_tracking.mp4'), p('crowd_tracking.mp4'), 'two versions of the same pedestrians clip: judge the legs of the walkers (how high a swinging foot is lifted) and long coats')
for n, note in (('tee-mouth-3x', 'masked face around the nose / mouth, 3x crop, two versions: judge holes through the mask'),
                ('thug-collar-3x', 'street criminal collar, 3x crop, two versions: judge a skin-coloured wedge'),
                ('knockdown-3x', 'enemy lying on the ground, 3x crop, two versions of the choreography')):
    b = n[:-3]
    add(n, os.path.join(crops, 'r9_%s.jpg' % b), os.path.join(crops, 'r8_%s.jpg' % b), note)
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
