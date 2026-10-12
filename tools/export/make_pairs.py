#!/usr/bin/env python3
"""(r10) pairs.json for tools/night1/abpack.py: our round-NN frames vs the matching reference stills (private ~/spiderman-learnings/refs, never committed) + 'progress' pairs
(previous round vs this round). usage: make_pairs.py <round NN> <out pairs.json>   e.g. make_pairs.py 10 /Users/midir/sm2-n1/_scratch/critic-P1-r10/pairs.json"""
import json, sys, os
nn = int(sys.argv[1]); out = sys.argv[2]
R = '/Users/midir/sm2-n1/city/docs/night1/city/round-%02d/' % nn; P = '/Users/midir/sm2-n1/city/docs/night1/city/round-%02d/' % (nn - 1)
REF = '/Users/midir/spiderman-learnings/refs/streets/'
S = {'S1': 'S1_avenue_street', 'S2': 'S2_avenue_swing', 'S3': 'S3_rooftop_watertower', 'S4': 'S4_perch_skyline', 'S5': 'S5_timessq_south', 'S6': 'S6_timessq_street', 'S7': 'S7_sunset_crosstown', 'S8': 'S8_aerial_midtown'}
f = lambda d, k: d + S[k] + '_1920x1080.jpg'
pairs = [
 ('street-avenue', 'S1', 'street-avenue-hero-taxis__og_0000.jpg', 'street level, avenue canyon looking up the avenue, daylight'),
 ('avenue-swing-height', 'S2', 'street-midtown-high__og_0410.jpg', 'mid-height view down an avenue canyon, daylight'),
 ('rooftop-watertowers', 'S3', 'rooftops-watertowers-golden__nm_0314.jpg', 'rooftop level with timber water tanks, towers behind'),
 ('perch-skyline', 'S4', 'skyline-perch-nm__nm_0846.jpg', 'perch on a tall tower over a river and the far shore, daylight'),
 ('perch-skyline-dn', 'S4', 'skyline-perch-dn__dn_1438.jpg', 'perch on a tall tower over a river and the far shore, midday'),
 ('plaza-red-steps', 'S5', 'timessquare-red-steps__ts_0027.jpg', 'raised plaza with steps, billboards all around, looking at a tower'),
 ('plaza-street', 'S6', 'timessquare-billboards-street__ts_0217.jpg', 'plaza at street level looking along the billboards'),
 ('sunset-crosstown', 'S7', 'sunset-swing-trailer__eny_0142.jpg', 'low sun down a cross street, above street level'),
 ('aerial-midtown', 'S8', 'swing-over-city-golden-trailer__st_0052.jpg', 'high aerial view over midtown blocks toward a park'),
]
out_pairs = [dict(id=i, x=f(R, k), y=REF + r, note=n) for i, k, r, n in pairs]
for i, k, n in (('progress-skyline', 'S4', 'two versions of our perch view over the river and the far shore (one is the newer build)'), ('progress-street', 'S1', 'two versions of our street-level avenue view (one is the newer build)'),
                ('progress-rooftop', 'S3', 'two versions of our rooftop water-tank view (one is the newer build)'), ('progress-plaza', 'S6', 'two versions of our plaza street view (one is the newer build)')):
    out_pairs.append(dict(id=i, x=f(R, k), y=f(P, k), note=n))
for p in out_pairs:
    for k in ('x', 'y'):
        if not os.path.exists(p[k]): print('MISSING', p['id'], k, p[k])
os.makedirs(os.path.dirname(out), exist_ok=True); json.dump(out_pairs, open(out, 'w'), indent=1); print(len(out_pairs), 'pairs ->', out)
