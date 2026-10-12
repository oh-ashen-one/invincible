# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C r01: source clips + pairs.json for the blind A/B critic pack (tools/night1/abpack.py). Everything it writes stays in _scratch
# (the owner clip is footage of the real game: local only, never committed).
#   python3 tools/tricks/make_pairs.py <reel.mp4> <reel_telemetry.csv> <traversal f4.mp4> <out dir>      -> <out dir>/pairs.json
# x = ours (tricks r01 reel excerpt, cropped around the hero to the owner clip's 610:556 aspect), y = the owner clip segment (FLIPS_SPEC
# S1 / S2 / S3 / S6), both scaled to the SAME 1220x1112; progress pairs: traversal r26 f4 vs the tricks r01 reel, both 1280x720.
import csv, json, os, statistics, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tricks_check import instances  # noqa: E402

REEL, TEL, F4, OUT = sys.argv[1:5]
OWNER = '/Users/midir/sm2-n1/_scratch/refs/owner/flips_owner_2026-09-29.mov'
W, H = 1220, 1112
os.makedirs(OUT, exist_ok=True)
T = list(csv.DictReader(open(TEL)))
I = [c for c in instances(T) if c['scale'] > 0]
# movie time of telemetry time t: the merged reel's frame 0 is sequence frame 0 (capture.sh); MOVIE_OFF (s) corrects a measured offset
OFF = float(os.environ.get('MOVIE_OFF', '0'))


def ff(*a):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + list(a), check=True)


def ours(c, name, pre=0.35, post=0.45, until=None):
    t0, t1 = c['t0'] - pre, (until if until is not None else c['t0'] + c['len']) + post
    rows = [r for r in T if t0 <= float(r['t']) <= t1 and float(r.get('px_bottom') or 0) > float(r.get('px_top') or 0)]
    cx = statistics.median((float(r['px_left']) + float(r['px_right'])) / 2 for r in rows)
    cy = statistics.median((float(r['px_top']) + float(r['px_bottom'])) / 2 for r in rows)
    hh = statistics.median(max(float(r['px_bottom']) - float(r['px_top']), float(r['px_right']) - float(r['px_left'])) for r in rows)
    ch = min(1080.0, max(420.0, hh / 0.27)); cw = ch * 610 / 556
    bx = max(0, min(1920 - cw, cx - cw / 2)); by = max(0, min(1080 - ch, cy - ch / 2))
    dst = os.path.join(OUT, 'ours_' + name + '.mp4')
    ff('-ss', '%.3f' % max(0, t0 + OFF), '-t', '%.3f' % (t1 - t0), '-i', REEL, '-an', '-vf',
       'crop=%d:%d:%d:%d,scale=%d:%d,setsar=1' % (cw, ch, bx, by, W, H), '-r', '50', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', dst)
    return dst, (t0, t1)


def owner(a, b, name):
    dst = os.path.join(OUT, 'ref_' + name + '.mp4')
    ff('-ss', '%.3f' % a, '-t', '%.3f' % (b - a), '-i', OWNER, '-an', '-vf', 'scale=%d:%d:flags=lanczos,setsar=1' % (W, H),
       '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', dst)
    return dst


def first(p, k=0):
    L = [c for c in I if c['prog'] == p]
    return L[min(k, len(L) - 1)] if L else None


pairs = []
plan = [  # id, our program (instance), owner segment (s), note
    ('single-release-flip', 'backSingle', 0, (0.80, 2.44), 'One flip off a swing release into the next web catch.'),
    ('triple-chain', 'backTripleChain', 0, (8.40, 11.36), 'Three rotations in one release, a shape per rotation.'),
    ('pike-twist-open', 'barani', 0, (21.32, 23.80), 'Piked / inverted shapes opening to an upright spread before the next catch.'),
    ('inverted-pencil', 'frontPikeSwan', 0, (4.60, 5.96), 'Inverted held shape, then the unwind.'),
    ('short-tuck', 'frontDouble', 0, (14.80, 15.60), 'Tucked rotation between two webs.'),
]
# each owner segment is used once (S1, S3, S6, S2, S5); two wide pairs use the private reference library's trick clips (1920x1080 60 fps)
REFLIB = '/Users/midir/spiderman-learnings/refs/traversal/clips/'
WIDE = [('release-trick-wide', 'corkscrew', 0, REFLIB + 'trick-release-sky__nm_0425-0433.mp4', 'Release into an aerial trick, camera trailing.'),
        ('rooftop-trick-wide', 'backLayout', 1, REFLIB + 'trick-over-rooftops__nm_0905-0912.mp4', 'Release and mid-air trick over the city, then the next swing.')]
for pid, prog, k, (a, b), note in plan:
    c = first(prog, k)
    if not c: print('no instance of', prog); continue
    x, (t0, t1) = ours(c, pid)
    y = owner(a, b, pid)
    pairs.append(dict(id=pid, x=x, y=y, note=note + ' Both %dx%d.' % (W, H)))
    print(pid, prog, 'ours t %.2f-%.2f' % (t0, t1), 'ref %.2f-%.2f' % (a, b))
for pid, prog, k, ref, note in WIDE:
    c = first(prog, k)
    if not c: print('no instance of', prog); continue
    rd = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ref], capture_output=True, text=True).stdout)
    t0 = max(0.0, c['t0'] - 1.5); t1 = t0 + rd
    xa = os.path.join(OUT, 'ours_' + pid + '.mp4'); ya = os.path.join(OUT, 'ref_' + pid + '.mp4')
    ff('-ss', '%.3f' % (t0 + OFF), '-t', '%.3f' % rd, '-i', REEL, '-an', '-vf', 'scale=1280:720,setsar=1', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', xa)
    ff('-i', ref, '-an', '-vf', 'scale=1280:720,setsar=1', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', ya)
    pairs.append(dict(id=pid, x=xa, y=ya, note=note + ' Both 1280x720.'))
    print(pid, prog, 'ours t %.2f-%.2f' % (t0, t1), 'ref', os.path.basename(ref))
# stills: one held shape each (our longest held segment of that shape, its middle frame, cropped like the clips) vs the owner frame of
# that shape (ab_sheet.OWNER_T, FLIPS_SPEC segment times), both 1220x1112 PNG
from ab_sheet import OWNER_T  # noqa: E402
segs, cur = [], None
for r in T:
    s, l, p = r.get('flip_shape', ''), r.get('flip_shape_legs', ''), r.get('flip_prog', '')
    if s and s == l:
        if cur and cur['shape'] == s and cur['prog'] == p and float(r['t']) - cur['t1'] < 0.05:
            cur['t1'] = float(r['t']); cur['rows'].append(r)
        else:
            cur = dict(shape=s, prog=p, t1=float(r['t']), rows=[r]); segs.append(cur)
    else:
        cur = None
for shape in ('Tuck', 'Layout', 'Pencil', 'Straddle'):
    cand = sorted([s for s in segs if s['shape'] == shape and len(s['rows']) >= 6], key=lambda s: -len(s['rows']))
    if not cand: continue
    r = cand[0]['rows'][len(cand[0]['rows']) // 2]
    if float(r['px_bottom']) <= float(r['px_top']): continue
    x0, x1, y0, y1 = (float(r[k]) for k in ('px_left', 'px_right', 'px_top', 'px_bottom'))
    ch = min(1080.0, max(420.0, max(y1 - y0, x1 - x0) / 0.27)); cw = ch * 610 / 556
    bx = max(0, min(1920 - cw, (x0 + x1) / 2 - cw / 2)); by = max(0, min(1080 - ch, (y0 + y1) / 2 - ch / 2))
    xa = os.path.join(OUT, 'ours_still_%s.png' % shape.lower()); ya = os.path.join(OUT, 'ref_still_%s.png' % shape.lower())
    ff('-ss', '%.3f' % (float(r['t']) + OFF), '-i', REEL, '-frames:v', '1', '-vf', 'crop=%d:%d:%d:%d,scale=%d:%d' % (cw, ch, bx, by, W, H), xa)
    ff('-ss', '%.3f' % OWNER_T[shape][0], '-i', OWNER, '-frames:v', '1', '-vf', 'scale=%d:%d:flags=lanczos' % (W, H), ya)
    pairs.append(dict(id='shape-' + shape.lower(), x=xa, y=ya, note='Held %s shape in the air (still). Both %dx%d.' % (shape.lower(), W, H)))
    print('shape', shape, cand[0]['prog'], 'ours t %.2f' % float(r['t']), 'ref t %.2f' % OWNER_T[shape][0])
# progress: traversal's merged r26 f4 flip chain vs this reel (the same lit city, 1280x720 each)
dur_f4 = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', F4], capture_output=True, text=True).stdout)
for n, (a, b) in enumerate([(0.0, dur_f4)]):
    xa = os.path.join(OUT, 'reel_%d.mp4' % n); ya = os.path.join(OUT, 'f4_%d.mp4' % n)
    ff('-ss', '%.3f' % (a + OFF), '-t', '%.3f' % (b - a), '-i', REEL, '-an', '-vf', 'scale=1280:720,setsar=1', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', xa)
    ff('-ss', '%.3f' % a, '-t', '%.3f' % (min(b, dur_f4) - a), '-i', F4, '-an', '-vf', 'scale=1280:720,setsar=1', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', ya)
    pairs.append(dict(id='progress-flips-%d' % (n + 1), x=xa, y=ya, note='Flip chain through the lit city, %.0f-%.0f s of each clip. Both 1280x720.' % (a, b)))
json.dump(pairs, open(os.path.join(OUT, 'pairs.json'), 'w'), indent=1)
print('pairs', len(pairs), '->', os.path.join(OUT, 'pairs.json'))
