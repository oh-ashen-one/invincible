#!/usr/bin/env python3
"""(r11) critic pack inputs for tools/night1/abpack.py: ours vs the matching reference stills (private ~/spiderman-learnings/refs, never committed), plus r10 vs r11 'progress' pairs.
Both sides of every pair are written with the SAME pixel size into <work>/inputs/ (<= 2048 px wide copies, plus native-4K pixel crops where the 4K frame matters), then pairs.json.
usage: make_pairs_r11.py <work_dir> [round_dir (default docs/night1/city/round-11)]   ->  <work_dir>/pairs.json
Both sides are INTER_AREA reduced / cropped by the same code; reference stills are 3840x2160 originals."""
import json, sys, os, cv2
work = sys.argv[1]; WT = '/Users/midir/sm2-n1/city/'
R = os.path.join(WT, sys.argv[2] if len(sys.argv) > 2 else 'docs/night1/city/round-11') + '/'
P = WT + 'docs/night1/city/round-10/'
REF = '/Users/midir/spiderman-learnings/refs/streets/'
S = {'S1': 'S1_avenue_street', 'S2': 'S2_avenue_swing', 'S3': 'S3_rooftop_watertower', 'S4': 'S4_perch_skyline', 'S5': 'S5_timessq_south', 'S6': 'S6_timessq_street', 'S7': 'S7_sunset_crosstown', 'S8': 'S8_aerial_midtown'}
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
def load(p):
    im = cv2.imread(p)
    if im is None: raise SystemExit('missing ' + p)
    return im
def to(im, w, h): return cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA) if im.shape[1] != w or im.shape[0] != h else im
IN = os.path.join(work, 'inputs'); os.makedirs(IN, exist_ok=True); out = []
def put(pid, a, b, note):
    xa, ya = os.path.join(IN, pid + '_x.jpg'), os.path.join(IN, pid + '_y.jpg')
    assert a.shape == b.shape, (pid, a.shape, b.shape)
    cv2.imwrite(xa, a, [cv2.IMWRITE_JPEG_QUALITY, 93]); cv2.imwrite(ya, b, [cv2.IMWRITE_JPEG_QUALITY, 93])
    out.append(dict(id=pid, x=xa, y=ya, note=note))
# 1) the 9 reference pairs at 1920x1080 (ours: the 4K frame reduced when it exists, else the 1080p frame)
for pid, k, ref, note in pairs:
    f4 = R + S[k] + '_3840x2160.jpg'; f1 = R + S[k] + '_1920x1080.jpg'
    ours = to(load(f4 if os.path.exists(f4) else f1), 1920, 1080)
    put(pid, ours, to(load(REF + ref), 1920, 1080), note)
# 2) native-4K pixel crops (same pixel size both sides): the S4 far band, the S8 upper glass, the S3 board region
crops = [('crop4k-skyline-band', 'S4', 'skyline-perch-nm__nm_0846.jpg', (0, 220, 2048, 760), 'native-pixel crop of the far skyline and shore band, perch view over a river'),
         ('crop4k-tower-glass', 'S8', 'swing-over-city-golden-trailer__st_0052.jpg', (2300, 0, 3300, 760), 'native-pixel crop of the upper part of a glass tower, aerial view'),
         ('crop4k-rooftop-board', 'S3', 'rooftops-watertowers-golden__nm_0314.jpg', (200, 200, 1900, 1900), 'native-pixel crop of a rooftop with a large painted advertising board and a water tank')]
for pid, k, ref, (x0, y0, x1, y1), note in crops:
    f4 = R + S[k] + '_3840x2160.jpg'
    if not os.path.exists(f4): print('no 4K frame for', pid); continue
    a = load(f4)[y0:y1, x0:x1]; b = load(REF + ref)[y0:y1, x0:x1]
    put(pid, a, b, note)
# 3) progress pairs: r10 vs r11 at 1920x1080 (S4, S8, S3 and the rest of the set)
for k in ('S4', 'S8', 'S3', 'S1', 'S5', 'S6'):
    a = to(load(R + S[k] + '_1920x1080.jpg'), 1920, 1080); b = to(load(P + S[k] + '_1920x1080.jpg'), 1920, 1080)
    put('progress-' + S[k].split('_', 1)[1].replace('_', '-'), a, b, 'two versions of our %s view (one is the newer build)' % S[k].split('_', 1)[1].replace('_', ' '))
os.makedirs(work, exist_ok=True); json.dump(out, open(os.path.join(work, 'pairs.json'), 'w'), indent=1); print(len(out), 'pairs ->', os.path.join(work, 'pairs.json'))
