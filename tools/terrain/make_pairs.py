#!/usr/bin/env python3
"""pairs.json for tools/night1/abpack.py (blind critic pack, piece E): our round stills / movies vs the matching reference stills / clips (private ~/spiderman-learnings/refs, never committed)
+ progress pairs (previous round vs this round). Notes are neutral view descriptions (no hint which side is ours).
usage: make_pairs.py <round dir> <out pairs.json> [<previous round dir>]
(round 2: the Reservoir pair uses a reference frame that shows a park water basin from above, cut from the library's pond clip; the library has no frame of the Reservoir itself)"""
import json, sys, os, subprocess
R = os.path.abspath(sys.argv[1]); out = sys.argv[2]; PREV = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else None
REFROOT = '/Users/midir/spiderman-learnings/refs/'; REF = REFROOT + 'streets/'; TRAV = REFROOT + 'traversal/'
S = lambda i: os.path.join(R, 'stills', i + '.jpg')
PS = lambda i: os.path.join(PREV, 'stills', i + '.jpg') if PREV else None
# a wide park-water-basin-from-above frame from the library's pond clip (t = 4.5 s), derived into the critic scratch (not committed)
POND = os.path.join(os.path.dirname(os.path.abspath(out)), 'refs', 'pond_aerial_4p5s.jpg')
os.makedirs(os.path.dirname(POND), exist_ok=True)
if not os.path.exists(POND):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '4.5', '-i', TRAV + 'clips/swing-over-pond-park__cp_1136-1143.mp4', '-frames:v', '1', '-q:v', '2', POND])
pairs = [
 ('park-south-high',   S('p1_south'),      REF + 'centralpark-skyline-over-park__cp_1230.jpg', 'high view over a large park toward a skyline, warm daylight, lawns, paths and tree masses below'),
 ('park-reservoir',    S('p2_reservoir'),  POND, 'aerial view over a park water basin with its banks and the woods around it, daylight'),
 ('park-pond-woods',   S('p3_lake'),       TRAV + 'swing-over-pond-skyline__cp_1139.jpg', 'view over a park pond with woodland banks, skyline beyond'),
 ('park-great-lawn',   S('p4_greatlawn'),  REF + 'centralpark-aerial-ballfields__cp_0554.jpg', 'high view over open meadows with ball fields and woods'),
 ('park-panorama',     S('p9_park_panorama'), REF + 'swing-over-city-golden-trailer__st_0052.jpg', 'high view along a whole park with the city skyline behind it, warm haze'),
 ('park-lawn-eye',     S('p10_lawn_eye'),  REF + 'centralpark-meadow-skyline__cp_0605.jpg', 'eye-level view over a mown lawn toward the tree line and skyline'),
 ('shore-west',        S('p6_west_shore'), REF + 'waterfront-dn__dn_0052.jpg', 'waterfront edge from above: seawall, esplanade, water, piers'),
 ('shore-east',        S('p7_east_shore'), REF + 'river-queens-aerial__gr_0936.jpg', 'river shoreline from above with the far bank'),
 ('piers',             S('p8_pier'),       REF + 'river-pier-golden__gr_0555.jpg', 'piers and water from a low aerial position'),
]
if PREV:   # previous round vs this round (same camera: p1 / p2 / p10; the r02 shore cameras were moved, so no shore progress pair)
    pairs += [
     ('progress-park-south', S('p1_south'),     PS('p1_south'),     'two versions of the same high park view (one is the newer build)'),
     ('progress-reservoir',  S('p2_reservoir'), PS('p2_reservoir'), 'two versions of the same view over the park water basin (one is the newer build)'),
     ('progress-lawn-eye',   S('p10_lawn_eye'), PS('p10_lawn_eye'), 'two versions of the same eye-level lawn view (one is the newer build)'),
    ]
    if os.environ.get('LAWN_PROGRESS'):   # r04: the lawn changed everywhere: the two other lawn cameras too
        pairs += [
         ('progress-great-lawn', S('p4_greatlawn'),      PS('p4_greatlawn'),      'two versions of the same high view over open meadows with ball fields (one is the newer build)'),
         ('progress-panorama',   S('p9_park_panorama'),  PS('p9_park_panorama'),  'two versions of the same high view along the whole park (one is the newer build)'),
        ]
    if os.environ.get('SHORE_PROGRESS'):   # r03: the shore cameras are unchanged since r02 -> shore progress pairs too
        pairs += [
         ('progress-shore-west', S('p6_west_shore'), PS('p6_west_shore'), 'two versions of the same waterfront view (one is the newer build)'),
         ('progress-shore-east', S('p7_east_shore'), PS('p7_east_shore'), 'two versions of the same river shoreline view (one is the newer build)'),
        ]
M = lambda n: os.path.join(R, n + '.mp4')
pairs += [
 ('move-lawn-sprint',  M('t4_lawn_sprint'),     REFROOT + 'streets/clips/centralpark-path-walk__cp_0026-0035.mp4', 'ground-level run along a park lawn and path, trees and lamps beside the route'),
 ('move-avenue-park',  M('t5_avenue_to_park'),  REFROOT + 'traversal/clips/swing-over-pond-park__cp_1136-1143.mp4', 'low swing pass over a park edge'),
]
pairs = [dict(id=i, x=x, y=y, note=n) for i, x, y, n in pairs]
miss = [(p['id'], k, p[k]) for p in pairs for k in ('x', 'y') if not p[k] or not os.path.exists(p[k])]
for m in miss: print('MISSING', m)
pairs = [p for p in pairs if p['x'] and p['y'] and os.path.exists(p['x']) and os.path.exists(p['y'])]
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True); json.dump(pairs, open(out, 'w'), indent=1); print(len(pairs), 'pairs ->', out)
