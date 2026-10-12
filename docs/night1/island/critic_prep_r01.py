#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A) round 01 blind critic pack inputs: trims our route clips to the reference clip lengths (both 1920x1080 60 fps),
# downscales 3840x2160 stills to 1920x1080 where the other side is 1080p, writes pairs.json.
import json, os, subprocess
R = '/Users/midir/sm2-n1/island/docs/night1/island/round-01'
M = '/Users/midir/sm2-n1/_scratch/island/capture'          # 29 Mbps run_game masters
REF = '/Users/midir/spiderman-learnings/refs'
OUT = '/Users/midir/sm2-n1/_scratch/critic-A-r01/src'
PREV = '/Users/midir/sm2-n1/island/docs/night1/city/round-10/S4_perch_skyline_1920x1080.jpg'
def ff(*a): subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *a], check=True)
def clip(name, t0, dur):
    o = os.path.join(OUT, '%s_%gs.mp4' % (name, t0)); ff('-ss', str(t0), '-i', os.path.join(M, name, name + '.mp4'), '-t', str(dur), '-an',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-pix_fmt', 'yuv420p', o); return o
def still(src, tag, w=1920):
    o = os.path.join(OUT, tag + '.jpg'); ff('-i', src, '-vf', 'scale=%d:-2' % w, '-q:v', '2', o); return o
P = [
 {'id': 'v1-street-start', 'x': clip('r1_north_avenue', 0.0, 8.0), 'y': REF + '/traversal/clips/swing-start-from-street__og_0000-0008.mp4',
  'note': 'movement, 8 s: from a run on the avenue sidewalk into the first web swings up the avenue'},
 {'id': 'v2-avenue-chain', 'x': clip('r2_south_avenue', 0.0, 10.0), 'y': REF + '/traversal/clips/swing-avenue-sunset__og_0605-0615.mp4',
  'note': 'movement, 10 s: swing chain down a long avenue in low sun'},
 {'id': 'v3-crosstown', 'x': clip('r3_crosstown_east', 8.0, 8.0), 'y': REF + '/traversal/clips/swing-canyon-chase__nm_0139-0147.mp4',
  'note': 'movement, 8 s: swinging along a narrower cross street between mid-rise blocks'},
 {'id': 'v4-wallrun-roofs', 'x': clip('r4_wallrun_roofs', 0.0, 10.0), 'y': REF + '/traversal/clips/wallrun-empire__nm_0003-0013.mp4',
  'note': 'movement, 10 s: swing into a facade, wall-run up it, over the top onto the roofs'},
 {'id': 's1-perch-north', 'x': still(R + '/stills/a1_high_north_00_t000.6_3840x2160.jpg', 'a1_north_3840', 3840), 'y': REF + '/streets/skyline-perch-dn__dn_1438.jpg',
  'note': 'still, 3840x2160: high view over midtown looking up the island; does the city read as continuous detailed city to the horizon'},
 {'id': 's2-aerial-south', 'x': still(R + '/stills/a1_high_south_00_t000.6_3840x2160.jpg', 'a1_south_3840', 3840), 'y': REF + '/streets/skyline-queens-aerial__gr_0033.jpg',
  'note': 'still, 3840x2160: high view over the towers looking down the island'},
 {'id': 's3-over-avenue', 'x': R + '/stills/r1_north_avenue_t12s_1920x1080.jpg', 'y': still(REF + '/streets/swing-over-city-golden-trailer__st_0052.jpg', 'ref_swing_over_city'),
  'note': 'still, 1920x1080: mid-swing over an avenue at golden hour'},
 {'id': 's4-rooftops', 'x': R + '/stills/r4_wallrun_roofs_t20s_1920x1080.jpg', 'y': still(REF + '/streets/rooftops-watertowers-golden__nm_0314.jpg', 'ref_rooftops'),
  'note': 'still, 1920x1080: hero on / just above mid-rise roofs (water tanks, bulkheads)'},
 {'id': 'p1-previous-vs-this', 'x': still(R + '/stills/a1_high_north_00_t000.6_3840x2160.jpg', 'a1_north_1920'), 'y': PREV,
  'note': 'still, 1920x1080: two versions of a high view over midtown (same game, two builds); which reads as the better, more continuous city'},
]
for p in P: assert os.path.exists(p['x']) and os.path.exists(p['y']), p
json.dump(P, open('/Users/midir/sm2-n1/_scratch/critic-A-r01/pairs.json', 'w'), indent=1)
print('pairs', len(P))
