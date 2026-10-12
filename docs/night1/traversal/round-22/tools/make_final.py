#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r22: write the shot-list w1 / w2 scripts on the picked sunlit route.
#   make_final.py <pick>                       -> scripts/city/w2_wallrun_side_zip.json + r22/scripts/w1probe.json (no zip)
#   make_final.py <pick> --w1 <w1probe csv>    -> scripts/city/w1_wallrun_tall_zip.json (E 0.75 s after the wall contact, >= 3.6 s)
import csv, json, sys
R = '/Users/midir/sm2-n1/_scratch/traversal/r22'
SC = '/Users/midir/sm2-n1/traversal/docs/night1/traversal/scripts/city'
pick = sys.argv[1]
src = json.load(open(f'{R}/scripts/{pick}.json'))
if '--w1' not in sys.argv:
    w2 = dict(src)
    w2['name'] = 'w2_wallrun_side_zip'
    w2['note'] = ('Round 22 (director: route the side run on a sun-facing facade): the west face of the 96 m tower at x ~267.5, '
                  'y -620..-570 (a park west of it, sun yaw -178 elev 8: lit from ~15 m up). Swing south down the avenue, turn east '
                  f'at the facade, release, stick sideways + sprint from {src["keys"][3]["t"]} s (upright side run north along the face), '
                  f'E at {src["keys"][4]["t"]} s -> zip to the nearest place. Route variant {pick} (r22/pick_route.py).')
    json.dump(w2, open(f'{SC}/w2_wallrun_side_zip.json', 'w'), indent=1)
    w1 = dict(src); w1['name'] = 'w1probe'
    w1['keys'] = [k for k in src['keys'][:3]]
    json.dump(w1, open(f'{R}/scripts/w1probe.json', 'w'), indent=1)
    print('w2 written from', pick)
else:
    rows = list(csv.DictReader(open(sys.argv[sys.argv.index('--w1') + 1])))
    tc = next((float(r['t']) for r in rows if r['mode'] == 'wall'), 2.85)
    tz = round(max(3.6, tc + 0.75), 2)
    w1 = dict(src)
    w1['name'] = 'w1_wallrun_tall_zip'
    w1['note'] = (f'Round 22: w1 on the r22 sunlit route ({pick}): swing, release onto the 96 m tower west face (wall at {tc:.2f} s), '
                  f'wall run, E mid-wall at {tz} s -> zip to the facade top -> perch; E on the perch at {round(tz + 2.6, 2)} s.')
    w1['keys'] = [k for k in src['keys'][:3]] + [
        {'t': tz, 'zip': True}, {'t': round(tz + 0.1, 2), 'zip': False},
        {'t': round(tz + 1.0, 2), 'move': [0, 0], 'heading': False},
        {'t': round(tz + 2.6, 2), 'zip': True}, {'t': round(tz + 2.7, 2), 'zip': False}]
    json.dump(w1, open(f'{SC}/w1_wallrun_tall_zip.json', 'w'), indent=1)
    print(f'w1 written: wall {tc:.2f} s, E {tz} s')
