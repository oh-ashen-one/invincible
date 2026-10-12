#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r03: pick between two measured movies (mA.json / mB.json in <work_dir>): more good_run>=3 blows wins, ties: more crop_run>=3, then A.
import json, sys
w = sys.argv[1]
a = json.load(open(w + '/mA.json')); b = json.load(open(w + '/mB.json'))
ka = (a['good_run_ge3'], a['crop_run_ge3']); kb = (b['good_run_ge3'], b['crop_run_ge3'])
pick = 'B' if kb > ka else 'A'
open(w + '/picked.txt', 'w').write(pick + '\n')
print('picked movie %s: A good/crop %s of %d vs B %s of %d' % (pick, ka, a['hero_blows_measured'], kb, b['hero_blows_measured']))
print(pick)
