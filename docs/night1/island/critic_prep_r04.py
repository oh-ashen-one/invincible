#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A) round 04 blind critic pack inputs. Builds BASE/src (both files of a pair the SAME pixel size, <= 2048 px on the long edge) and
# BASE/pairs.json ({"id","x" = ours,"y" = the other side,"note"}); then pack it:
#   python3 docs/night1/island/critic_prep_r04.py
#   python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-A-r04/pack /Users/midir/sm2-n1/_scratch/critic-A-r04/pairs.json .
# Pairs: ours vs a matching real-game reference (private ~/spiderman-learnings/refs, never committed), and round 03 vs round 04 (same route,
# same input) for r3 (fire escapes), r5 and the fire-escape close-ups. Only round-04 captures (mtime after R04_T0) count as "ours".
import json, os, subprocess, time
BASE = '/Users/midir/sm2-n1/_scratch/critic-A-r04'
OUT = BASE + '/src'
os.makedirs(OUT, exist_ok=True)
R = '/Users/midir/sm2-n1/island/docs/night1/island/round-04'
R3 = '/Users/midir/sm2-n1/island/docs/night1/island/round-03'
REF = '/Users/midir/spiderman-learnings/refs'
R04_T0 = time.mktime((2026, 10, 3, 15, 0, 0, 0, 0, -1))
W1, H1 = 1920, 1080
W2, H2 = 2048, 1152
FE_T = [float(v) for v in os.environ.get('FE_T', '2.5,3.5').split(',')]   # r3 seconds at the fire escape (x -235.5, y 616)


def ff(*a): subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *a], check=True)


def fresh(p): return p and os.path.exists(p) and os.path.getmtime(p) >= R04_T0


def vf(w, h): return 'scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d' % (w, h, w, h)


def clip(src, tag, t0, dur, need_fresh=False):
    if not src or not os.path.exists(src) or (need_fresh and not fresh(src)): return None
    o = os.path.join(OUT, tag + '.mp4')
    ff('-ss', str(t0), '-i', src, '-t', str(dur), '-an', '-vf', vf(W1, H1), '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-pix_fmt', 'yuv420p', o)
    return o


def still(src, tag, w=W1, h=H1, need_fresh=False):
    if not src or not os.path.exists(src) or (need_fresh and not fresh(src)): return None
    o = os.path.join(OUT, tag + '.jpg'); ff('-i', src, '-vf', vf(w, h), '-q:v', '2', o); return o


def frame(src, tag, t, need_fresh=False):
    """one movie frame at game time t (frame k shows (k - 1) / 60 s), 1920x1080 jpg"""
    if not src or not os.path.exists(src) or (need_fresh and not fresh(src)): return None
    o = os.path.join(OUT, tag + '.jpg'); ff('-ss', '%.4f' % t, '-i', src, '-frames:v', '1', '-vf', vf(W1, H1), '-q:v', '2', o); return o


def mine(name):  # this round's route master (run_game ~29 Mbps) from the scratch capture dir, else the committed 2-pass movie
    m = '/Users/midir/sm2-n1/_scratch/island/capture/%s/%s.mp4' % (name, name)
    return m if fresh(m) else R + '/%s.mp4' % name


S = R + '/stills/'
P = [
    # ---- ours vs the real game
    {'id': 'v1-street-start', 'x': clip(mine('r1_north_avenue'), 'r1_0s', 0.0, 8.0, True), 'y': clip(REF + '/traversal/clips/swing-avenue-midday__dn_0212-0220.mp4', 'ref_avenue_midday', 0, 8),
     'note': 'movement, 8 s: the first web swings up an avenue from the sidewalk'},
    {'id': 'v2-avenue-chain', 'x': clip(mine('r5_m2_avenue'), 'r5_m2', 0.0, 8.0, True), 'y': clip(REF + '/traversal/clips/swing-avenue-traffic__dn_0949-0957.mp4', 'ref_avenue_traffic', 0, 8),
     'note': 'movement, 8 s: a long swing chain down an avenue far from the start (street level below: lanes, paint, cars, sidewalks, trees)'},
    {'id': 'v3-crosstown-fire-escapes', 'x': clip(mine('r3_crosstown_east'), 'r3_1s', 1.0, 8.0, True), 'y': clip(REF + '/traversal/clips/swing-canyon-chase__nm_0139-0147.mp4', 'ref_canyon', 0, 8),
     'note': 'movement, 8 s: swinging along a narrower cross street between mid-rise brick blocks with fire escapes'},
    {'id': 'v4-wallrun-roofs', 'x': clip(mine('r4_wallrun_roofs'), 'r4_0s', 0.0, 8.0, True), 'y': clip(REF + '/traversal/clips/swing-river-to-canyon__og_0243-0253.mp4', 'ref_river_canyon', 0, 8),
     'note': 'movement, 8 s: swing into a facade, wall-run up it, over the top onto the roofs'},
    {'id': 's1-avenue-late', 'x': still(S + 'r5_m2_avenue_t26s_1920x1080.jpg', 'r5_t26', need_fresh=True), 'y': still(REF + '/streets/street-avenue-hero-taxis__og_0000.jpg', 'ref_avenue_taxis'),
     'note': 'still, 1920x1080: over an avenue far from the start; road surface, lane paint, cars, sidewalks below'},
    {'id': 's2-avenue-mid', 'x': still(S + 'r5_m2_avenue_t12s_1920x1080.jpg', 'r5_t12', need_fresh=True), 'y': still(REF + '/streets/street-midtown-high__og_0410.jpg', 'ref_midtown_high'),
     'note': 'still, 1920x1080: swinging high over an avenue canyon; facades both sides, street layer below'},
    {'id': 's3-rooftops', 'x': still(S + 'r4_wallrun_roofs_t20s_1920x1080.jpg', 'r4_t20', need_fresh=True), 'y': still(REF + '/streets/rooftops-watertowers-golden__nm_0314.jpg', 'ref_rooftops'),
     'note': 'still, 1920x1080: hero on / just above mid-rise roofs (water tanks, bulkheads)'},
    {'id': 's4-fire-escape', 'x': frame(mine('r3_crosstown_east'), 'r3_fe_a', FE_T[0], True), 'y': still(REF + '/traversal/swing-brick-canyon__og_0250.jpg', 'ref_brick_canyon'),
     'note': 'still, 1920x1080: close to a brick facade with fire escapes during a swing'},
    {'id': 's5-avenue-trees', 'x': still(S + 'r1_north_avenue_t20s_1920x1080.jpg', 'r1_t20', need_fresh=True), 'y': still(REF + '/traversal/swing-street-trees__nm_0550.jpg', 'ref_street_trees'),
     'note': 'still, 1920x1080: low swing over an avenue lined with street trees'},
    # ---- round 03 vs round 04 (x = round 04, same route script and input)
    {'id': 'p1-crosstown-fire-escape-prev', 'x': clip(mine('r3_crosstown_east'), 'r3_p1', 2.0, 8.0, True), 'y': clip(R3 + '/r3_crosstown_east.mp4', 'r03_r3_p1', 2.0, 8.0),
     'note': 'movement, 8 s: the same cross-street swing in two builds, 2-10 s, where the hero meets a fire escape'},
    {'id': 'p2-fire-escape-frame-prev', 'x': frame(mine('r3_crosstown_east'), 'r3_fe_p2', FE_T[1], True), 'y': frame(R3 + '/r3_crosstown_east.mp4', 'r03_r3_fe_p2', FE_T[1]),
     'note': 'still, 1920x1080: the same second of the same cross-street swing (at the fire escape) in two builds'},
    {'id': 'p3-avenue-m2-prev', 'x': clip(mine('r5_m2_avenue'), 'r5_p3', 4.0, 8.0, True), 'y': clip(R3 + '/r5_m2_avenue.mp4', 'r03_r5_p3', 4.0, 8.0),
     'note': 'movement, 8 s: the same avenue swing (same start, same held input) in two builds, 4-12 s'},
    {'id': 'p4-avenue-m2-late-prev', 'x': clip(mine('r5_m2_avenue'), 'r5_p4', 22.0, 8.0, True), 'y': clip(R3 + '/r5_m2_avenue.mp4', 'r03_r5_p4', 22.0, 8.0),
     'note': 'movement, 8 s: the same avenue swing in two builds, 22-30 s'},
    {'id': 'p5-north-avenue-prev', 'x': clip(mine('r1_north_avenue'), 'r1_p5', 14.0, 8.0, True), 'y': clip(R3 + '/r1_north_avenue.mp4', 'r03_r1_p5', 14.0, 8.0),
     'note': 'movement, 8 s: the same avenue swing in two builds, 14-22 s (street trees along the route)'},
]
skipped = [p['id'] for p in P if not (p['x'] and os.path.exists(p['x']) and p['y'] and os.path.exists(p['y']))]
P = [p for p in P if p['id'] not in skipped]
if skipped: print('pairs left out (capture missing):', skipped)
json.dump(P, open(BASE + '/pairs.json', 'w'), indent=1)
print('pairs', len(P), [p['id'] for p in P])
