#!/usr/bin/env python3
"""Round 09: does every strike of the script actually reach its victim?  Reads a bone log (the engine's -WHBoneLog csv, or the script's own prediction from
`preview_cpu.py --bones`) and, at each hero strike's contact instant, prints the distance (cm) from the striking wrist / foot to the victim's head and spine2 joints.
A wrist 15 - 30 cm from the head joint touches the face (head radius ~11 cm + fist); beyond ~40 cm the blow misses.  Fan homage project; no affiliation.
  python3 tools/ue_char/fight/contact_check.py bones.csv [out.json]"""
import csv, json, sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
rows = {}
for r in csv.DictReader(open(sys.argv[1])):
    rows[(r['label'], r['bone'], round(float(r['time']) * 60))] = np.array([float(r['bx']), float(r['by']), float(r['bz'])])
FS = json.load(open(os.path.join(HERE, 'fight_script.json')))
CONTACT = {'hero:punch1': (0.33, 'hand.L'), 'hero:punch2': (0.27, 'hand.R'), 'hero:punch3': (0.33, 'hand.L'), 'hero:kick': (0.30, 'foot.R'), 'hero:uppercut': (0.25, 'hand.R'),
           'thug:thugPunch1': (0.33, 'hand.R'), 'thug:thugPunch2': (0.30, 'hand.L')}
get = lambda l, b, t: rows[(l, b, int(round(t * 60)))]
out = []
for who, a in FS['actors'].items():
    for b in a['beats']:
        if b['clip'] not in CONTACT: continue
        c, limb = CONTACT[b['clip']]; tc = b['start'] + c / b['rate']
        for l2, a2 in FS['actors'].items():
            if l2 == who: continue
            for bb in a2['beats']:
                if abs(bb['start'] - (tc + 0.02)) < 0.011 and (bb['clip'].startswith('fight:') or bb['clip'] == 'hero:hitReact'):
                    try:
                        lp = get(who, limb, tc)
                        out.append({'t': round(tc, 2), 'attacker': who, 'clip': b['clip'], 'limb': limb, 'victim': l2, 'reaction': bb['clip'],
                                    'to_head_cm': round(float(np.linalg.norm(lp - get(l2, 'head', tc))), 1), 'to_spine2_cm': round(float(np.linalg.norm(lp - get(l2, 'spine2', tc))), 1)})
                    except KeyError: pass
for o in sorted(out, key=lambda o: o['t']): print(o['t'], o['attacker'].split('_')[1], o['clip'], '->', o['victim'].split('_')[1], o['reaction'], 'head %.1f spine2 %.1f cm' % (o['to_head_cm'], o['to_spine2_cm']))
best = [min(o['to_head_cm'], o['to_spine2_cm']) for o in out]
print('%d strikes, nearest joint distance median %.1f cm, worst %.1f cm' % (len(out), float(np.median(best)), max(best)))
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
