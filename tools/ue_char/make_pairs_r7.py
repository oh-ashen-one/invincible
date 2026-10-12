# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: pairs.json for the blind critic pack (tools/night1/abpack.py).  x = our capture, y = the matching reference of the private ~/spiderman-learnings/refs
(never committed) or the previous round's capture of the same view.

  python3 tools/ue_char/make_pairs_r7.py <round07 captures dir> <round06 captures dir> <crops dir> <out pairs.json>
"""
import json, os, sys
cap, prev, crops, out = sys.argv[1:5]
R = '/Users/midir/spiderman-learnings/refs/'
def have(p): return os.path.exists(p)
pairs = []
def add(i, x, y, note):
    if have(x) and have(y): pairs.append(dict(id=i, x=x, y=y, note=note))
    else: print('skipped (missing file)', i, x if not have(x) else y)
c = lambda n: os.path.join(cap, n); p = lambda n: os.path.join(prev, n)
add('hero-run', c('hero_run_side.mp4'), R + 'animation/clips/run-crosswalk__dn_0329-0337.mp4', 'hero running, full body')
add('hero-chase', c('hero_run_chase.mp4'), R + 'animation/clips/run-toward-camera__dn_0418-0425.mp4', 'hero running away from a chase camera behind')
add('hero-standing', c('hero_turntable_4k.jpg'), R + 'characters/hero-idle-street-og__og_0000.jpg', 'hero full body on a street')
add('suit-close', c('suit_closeup_4k.jpg'), R + 'characters/press-suit-closeup-fire__psblog_14.jpg', 'suit fabric close-up')
add('hero-face', c('hero_face_lens_4k.jpg'), R + 'characters/miles-face-closeup__gr_0230.jpg', 'mask and lens close-up')
add('thugs-group', c('street_fight_wide_4k.jpg'), R + 'characters/thugs-group-nm__nm_0049.jpg', 'a group of street criminals around the hero')
add('fight-clip', c('street_fight_34.mp4'), R + 'combat/clips/street-combo__nm_0214-0224.mp4', 'hero among a group of thugs, mid camera above')
add('thug-close', c('thug_face_4k.jpg'), R + 'characters/thug-closeup-dn__dn_0523.jpg', 'street criminal close-up')
add('citizens-clip', c('crowd_tracking.mp4'), R + 'characters/clips/street-npcs-idle__dn_0600-0608.mp4', 'pedestrians near the camera')
add('citizens-still', c('crowd_tracking_4k.jpg'), R + 'characters/npc-group-dn__dn_0725.jpg', 'a group of pedestrians on a street')
# previous round vs this round (the target of round 07: crowd separation, key see-through)
add('progress-crowd-clip', c('crowd_tracking.mp4'), p('crowd_tracking.mp4'), 'two versions of our pedestrians walking past a side camera (clip): judge whether any two people pass through each other or overlap')
add('progress-crowd-still', c('crowd_tracking_4k.jpg'), p('crowd_tracking_4k.jpg'), 'two versions of our pedestrians (still)')
add('progress-key-a', c('crowd_key_a_4k.png'), p('crowd_key_a_4k.jpg'), 'two versions of the same pedestrians with the street replaced by one flat green colour: judge green showing through or tinting any person, people overlapping, stray floating shapes')
add('progress-key-c', c('crowd_key_c_4k.png'), p('crowd_key_c_4k.jpg'), 'two versions of the same pedestrians with the street replaced by one flat green colour: judge green showing through or tinting any person, people overlapping, stray floating shapes')
add('progress-avoid', c('crowd_avoidance_demo.mp4'), p('crowd_tracking.mp4'), 'the same crowd lanes in two versions (clip): judge whether people pass through each other or step around each other')
for n, note in (('jeans-leg', 'lower legs of a walker in light jeans and white shoes, close-up on a flat green backdrop: judge any green showing through or tinting the trousers (two versions of our pedestrian)'),
                ('overlap-near', 'two pedestrians who cross paths, close-up on a flat green backdrop: judge whether they pass through each other (two versions)'),
                ('ankle-close', 'a pedestrian trouser cuff and shoe, close-up on a flat green backdrop: judge slivers of background between cuff and shoe (two versions)'),
                ('floating-shape', 'an empty patch of the flat green backdrop: judge any floating polygon (two versions)')):
    add(n, os.path.join(crops, 'r7_%s.jpg' % n), os.path.join(crops, 'r6_%s.jpg' % n), note)
json.dump(pairs, open(out, 'w'), indent=1)
print('pairs', len(pairs), '->', out)
