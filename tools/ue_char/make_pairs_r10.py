# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 10: pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private ~/spiderman-learnings/refs (never committed)
or the previous round's capture of the same view.

  python3 tools/ue_char/make_pairs_r10.py <round10 captures dir> <round09 captures dir> <crops dir> <out pairs.json>
The hero / crowd-key captures of round 08 are current (nothing of the hero changed) and are used unchanged for the standing hero pairs."""
import json, os, sys
cap, prev, crops, out = sys.argv[1:5]
R = '/Users/midir/spiderman-learnings/refs/'
R8 = '/Users/midir/sm2-n1/characters/docs/night1/characters/round-08/captures/'
pairs = []
def have(p): return os.path.exists(p)
def add(i, x, y, note):
    if have(x) and have(y): pairs.append(dict(id=i, x=x, y=y, note=note))
    else: print('skipped (missing file)', i, x if not have(x) else y)
c = lambda n: os.path.join(cap, n); p = lambda n: os.path.join(prev, n)
# the round target: every 8 s fight clip has >= 4 hit reactions, >= 2 knockdowns (two enemies on the ground together >= 1 s), >= 2 different get-ups, nobody holding a guard > 2 s
add('fight-clip-34', c('street_fight_34.mp4'), R + 'combat/clips/street-combo__nm_0214-0224.mp4', 'hero among a group of street criminals, mid camera above: judge hit reactions, knockdowns (how many enemies are down at once), the get-ups, and whether any enemy stands in one guard pose for seconds')
add('fight-clip-wide', c('street_fight_wide.mp4'), R + 'combat/clips/plaza-fight__dn_0818-0828.mp4', 'hero and a group of enemies trading blows, wide camera: judge hit reactions, knockdowns, get-ups and idle enemies')
add('fight-clip-cars', c('street_fight_34.mp4'), R + 'combat/clips/street-fight-cars__nm_0500-0510.mp4', 'hero fighting a group of criminals: judge enemy reactions to hits, knockdown and recovery')
add('fight-orbit', c('street_fight_orbit.mp4'), R + 'combat/clips/street-fight-cars__nm_0500-0510.mp4', 'orbiting camera around a hero fighting a group: judge reactions, knockdowns, get-ups, idle enemies')
add('enemy-knockdowns-still', c('street_fight_34_4k.jpg'), R + 'combat/enemy-launched-og__og_0149.jpg', 'enemies knocked to the ground by the hero: judge the poses, the contact with the ground, how many are down')
add('thugs-group', c('street_fight_wide_4k.jpg'), R + 'characters/thugs-group-nm__nm_0049.jpg', 'a group of street criminals around the hero')
add('thug-close', c('thug_face_4k.jpg'), R + 'characters/thug-closeup-dn__dn_0523.jpg', 'street criminal close-up')
add('citizens-clip', p('crowd_tracking.mp4'), R + 'characters/clips/street-npcs-idle__dn_0600-0608.mp4', 'pedestrians near the camera')
add('hero-run', R8 + 'hero_run_side.mp4', R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'masked acrobat hero running, full body')
add('hero-standing', R8 + 'hero_turntable_4k.jpg', R + 'characters/hero-idle-street-og__og_0000.jpg', 'hero full body on a street')
# previous round vs this round (same views)
add('progress-fight-34', c('street_fight_34.mp4'), p('street_fight_34.mp4'), 'two versions of the same staged street fight (same camera): judge hit reactions, knockdowns, get-ups and idle enemies; is anything wrong with the hero (an untextured limb)?')
add('progress-fight-wide', c('street_fight_wide.mp4'), p('street_fight_wide.mp4'), 'two versions of the same wide shot of the staged fight: judge hit reactions, knockdowns and idle enemies')
add('progress-fight-still', c('street_fight_34_4k.jpg'), p('street_fight_34_4k.jpg'), 'two versions of the same fight, one frame: judge what the enemies are doing')
add('progress-thug-collar', c('thug_face_4k.jpg'), p('thug_face_4k.jpg'), 'two versions of the same street criminal close-up: judge a skin-coloured / pale wedge at the jacket collar')
add('progress-beard', c('beard_face_4k.jpg'), p('beard_face_4k.jpg'), 'two versions of the same face close-up: judge the side hair (a gap between face and hair showing the background)')
add('progress-hood', c('hood_face_4k.jpg'), p('hood_face_4k.jpg'), 'two versions of the same face close-up: judge loose ribbon strands on the hair')
# the regression of round 09: the hero's limbs at the instants of the 'untextured grey arm' (hero-centred 3x crops of each clip, two versions)
for clip in ('34', 'wide', 'orbit'):
    add('hero-limbs-%s' % clip, os.path.join(crops, 'r10_hero_%s.jpg' % clip), os.path.join(crops, 'r9_hero_%s.jpg' % clip),
        'the masked hero in the staged street fight at three instants 0.1 s apart, 3x crop, two versions: is any limb of the hero untextured, grey or pale, or is any object passing through his body?')
for n, note in (('arm-3x', 'the region at 1.30 / 1.40 / 1.50 s of the 3/4 fight clip where a pale untextured limb showed in the previous round, 3x crop, two versions'),
                ('thug-collar-3x', 'street criminal collar, 3x crop, two versions: judge a pale wedge'),
                ('beard-hair-3x', 'beard face temple hair, 3x crop, two versions: judge a gap showing the background'),
                ('hood-hair-3x', 'hood face hair, 3x crop, two versions: judge loose strands')):
    b = n[:-3]
    add(n, os.path.join(crops, 'r10_%s.jpg' % b), os.path.join(crops, 'r9_%s.jpg' % b), note)
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
