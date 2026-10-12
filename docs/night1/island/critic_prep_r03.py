#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A) round 03 blind critic pack inputs (M2 whole island). Builds BASE/src (every file of a pair the SAME pixel size, <= 2048 px on
# the long edge) and BASE/pairs.json ({"id","x" = ours,"y" = the other side,"note"}); then pack it:
#   python3 docs/night1/island/critic_prep_r03.py
#   python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-A-r03/pack /Users/midir/sm2-n1/_scratch/critic-A-r03/pairs.json .
# Pairs: ours vs a matching real-game reference (private ~/spiderman-learnings/refs, never committed), and this round vs round 02 (same place or
# same input). Only captures made THIS round (mtime after R03_T0) count as "ours"; a missing capture leaves its pair out (printed).
import json, os, subprocess, time
BASE = '/Users/midir/sm2-n1/_scratch/critic-A-r03'
OUT = BASE + '/src'
os.makedirs(OUT, exist_ok=True)
R = '/Users/midir/sm2-n1/island/docs/night1/island/round-03'
R2 = '/Users/midir/sm2-n1/island/docs/night1/island/round-02'
REF = '/Users/midir/spiderman-learnings/refs'
R03_T0 = time.mktime((2026, 10, 2, 5, 0, 0, 0, 0, -1))
W1, H1 = 1920, 1080     # movies and 1080p stills
W2, H2 = 2048, 1152     # the 3840x2160 stills (long edge <= 2048)
R5_T0, R5_DUR = float(os.environ.get('R5_T0', 0.0)), float(os.environ.get('R5_DUR', 8.0))   # window of the M2 route used for the movie pair
R02_R2_Y1010 = float(os.environ.get('R02_R2_Y1010', 19.7))   # second at which the round-02 r2 telemetry crosses y = 1010


def ff(*a): subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *a], check=True)


def fresh(p): return p and os.path.exists(p) and os.path.getmtime(p) >= R03_T0


def vf(w, h): return 'scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d' % (w, h, w, h)


def clip(src, tag, t0, dur, need_fresh=False):
    if not src or not os.path.exists(src) or (need_fresh and not fresh(src)): return None
    o = os.path.join(OUT, tag + '.mp4')
    ff('-ss', str(t0), '-i', src, '-t', str(dur), '-an', '-vf', vf(W1, H1), '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-pix_fmt', 'yuv420p', o)
    return o


def still(src, tag, w=W1, h=H1, need_fresh=False):
    if not src or not os.path.exists(src) or (need_fresh and not fresh(src)): return None
    o = os.path.join(OUT, tag + '.jpg'); ff('-i', src, '-vf', vf(w, h), '-q:v', '2', o); return o


def mine(name):  # this round's route master (run_game 29 Mbps) from the scratch capture dir, else the committed 2-pass movie
    m = '/Users/midir/sm2-n1/_scratch/island/capture/%s/%s.mp4' % (name, name)
    return m if fresh(m) else R + '/%s.mp4' % name


S = R + '/stills/'
P = [
    # ---- ours vs the real game
    {'id': 'v1-street-start', 'x': clip(mine('r1_north_avenue'), 'r1_0s', 0.0, 8.0), 'y': clip(REF + '/traversal/clips/swing-start-from-street__og_0000-0008.mp4', 'ref_street_start', 0, 8),
     'note': 'movement, 8 s: from a run on the avenue sidewalk into the first web swings up the avenue'},
    {'id': 'v2-avenue-chain-south', 'x': clip(mine('r5_m2_avenue'), 'r5_m2', R5_T0, R5_DUR), 'y': clip(REF + '/traversal/clips/swing-avenue-traffic__dn_0949-0957.mp4', 'ref_avenue_traffic', 0, R5_DUR),
     'note': 'movement: a long swing chain down an avenue far from the start (street level below: lanes, paint, cars, sidewalks, trees)'},
    {'id': 'v3-crosstown', 'x': clip(mine('r3_crosstown_east'), 'r3_9s', 9.0, 8.0), 'y': clip(REF + '/traversal/clips/swing-canyon-chase__nm_0139-0147.mp4', 'ref_canyon', 0, 8),
     'note': 'movement, 8 s: swinging along a narrower cross street between mid-rise blocks'},
    {'id': 'v4-wallrun-roofs', 'x': clip(mine('r4_wallrun_roofs'), 'r4_0s', 0.0, 10.0), 'y': clip(REF + '/traversal/clips/wallrun-empire__nm_0003-0013.mp4', 'ref_wallrun', 0, 10),
     'note': 'movement, 10 s: swing into a facade, wall-run up it, over the top onto the roofs'},
    {'id': 's1-perch-north', 'x': still(S + 'a1_high_north_00_t000.6_3840x2160.jpg', 'a1_north', W2, H2, True), 'y': still(REF + '/streets/skyline-perch-dn__dn_1438.jpg', 'ref_perch', W2, H2),
     'note': 'still, 2048x1152: high view looking up the island; does the city read as one continuous detailed city to the horizon'},
    {'id': 's2-aerial-south', 'x': still(S + 'a1_high_south_00_t000.6_3840x2160.jpg', 'a1_south', W2, H2, True), 'y': still(REF + '/streets/skyline-queens-aerial__gr_0033.jpg', 'ref_aerial', W2, H2),
     'note': 'still, 2048x1152: high view over the towers looking down the island'},
    {'id': 's3-avenue-late', 'x': still(S + os.environ.get('R5_S3', 'r5_m2_avenue_t26s_1920x1080.jpg'), 'r5_s3', need_fresh=True), 'y': still(REF + '/streets/street-avenue-hero-taxis__og_0000.jpg', 'ref_avenue_taxis'),
     'note': 'still, 1920x1080: over an avenue far from the start; road surface, lane paint, cars, sidewalks below'},
    {'id': 's4-avenue-mid', 'x': still(S + os.environ.get('R5_S4', 'r5_m2_avenue_t12s_1920x1080.jpg'), 'r5_s4', need_fresh=True), 'y': still(REF + '/streets/street-midtown-high__og_0410.jpg', 'ref_midtown_high'),
     'note': 'still, 1920x1080: swinging high over an avenue canyon; facades both sides, street layer below'},
    {'id': 's5-rooftops', 'x': still(S + 'r4_wallrun_roofs_t20s_1920x1080.jpg', 'r4_t20', need_fresh=True), 'y': still(REF + '/streets/rooftops-watertowers-golden__nm_0314.jpg', 'ref_rooftops'),
     'note': 'still, 1920x1080: hero on / just above mid-rise roofs (water tanks, bulkheads)'},
    {'id': 's6-street-level-m2', 'x': still(S + 'street_m2_after_ism_fix_1920x1080.jpg', 'street_m2', need_fresh=True), 'y': still(REF + '/streets/street-walk-taxis__dn_0715.jpg', 'ref_walk_taxis'),
     'note': 'still, 1920x1080: street level on an avenue block (parked cars, traffic, trees, crosswalk, shop fronts)'},
    # ---- this round vs round 02 (x = round 03)
    {'id': 'p1-same-place-m2', 'x': clip(mine('r5_m2_avenue'), 'r5_p1', 0.0, 10.0), 'y': clip(R2 + '/r2_south_avenue.mp4', 'r02_r2_p1', R02_R2_Y1010, 10.0),
     'note': 'movement, 10 s: the same stretch of avenue (the blocks south of the old detailed area) in two builds, a held swing down the avenue'},
    {'id': 'p2-perch-north-prev', 'x': still(S + 'a1_high_north_00_t000.6_3840x2160.jpg', 'a1_north_p2', W2, H2, True), 'y': still(R2 + '/stills/a1_high_north_00_t000.6_3840x2160.jpg', 'r02_a1_north', W2, H2),
     'note': 'still, 2048x1152: the same viewpoint high over the island looking north, two builds'},
    {'id': 'p3-aerial-south-prev', 'x': still(S + 'a1_high_south_00_t000.6_3840x2160.jpg', 'a1_south_p3', W2, H2, True), 'y': still(R2 + '/stills/a1_high_south_00_t000.6_3840x2160.jpg', 'r02_a1_south', W2, H2),
     'note': 'still, 2048x1152: the same viewpoint high over the island looking south, two builds'},
    {'id': 'p4-chain-late-prev', 'x': clip(mine('r2_south_avenue'), 'r2_p4', 18.0, 10.0), 'y': clip(R2 + '/r2_south_avenue.mp4', 'r02_r2_p4', 18.0, 10.0),
     'note': 'movement, 10 s: two builds of the same game, same start and the same held swing input (one re-presses after 0.3 s, the other after 0.8 s), 18-28 s into a chain down one avenue'},
]
skipped = [p['id'] for p in P if not (p['x'] and os.path.exists(p['x']) and p['y'] and os.path.exists(p['y']))]
P = [p for p in P if p['id'] not in skipped]
if skipped: print('pairs left out (capture missing):', skipped)
json.dump(P, open(BASE + '/pairs.json', 'w'), indent=1)
print('pairs', len(P), [p['id'] for p in P])
