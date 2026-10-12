#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 13: the critic r12 test ("each trick is an isolated set piece: 1.7 s rise, trick, 1.3 s dive, then a camera cut").
#   usage: flow_check.py <telemetry.csv> <label> [--video <mp4>]      (60 fps telemetry of a rendered capture or a -nullrhi probe)
# Lines (all from the per-frame telemetry):
#   R1  release -> first flip shape <= 0.25 s          (release = the frame the mode leaves 'swing' for 'air'; first shape = first row
#                                                        with a flip program playing, flip_prog set)
#   R2  reach -> next web attach <= 0.3 s              (reach = first frame whose upper-body shape is Reach, or for a program without one
#                                                        (backDouble ends in the Kickout, web arm up) its catch window: program end - 0.2 s;
#                                                        attach = the mode enters 'swing' (a zip start counts for b))
#   R3  no web-less dive after the program            (time from program end to the attach; reported)
#   T4  release -> next attach <= 3.1 s, every release in the clip
#   T2  attach -> next attach <= 3.3 s, every consecutive pair of attaches
#   C1  per frame: |d pcm_pitch| <= 3 deg, |d pcm_yaw| <= 4 deg, |d pcm position| <= 1.2 m (whole clip)
#   C2  flip camera blend-out: flipcam_k from its value at the program end to < 0.02 takes >= 0.4 s
#   S1  backDouble uses <= 2 shapes (distinct upper-body flip_shape values while it plays)
#   V1  (--video) hero brightness in trick frames: median HSV V of the pixels inside the central 60 % of the hero's pixel bbox
#        (px_* columns, 1080p) -- the critic read "V 44/255" at r12 f4 8.45 s; reported p10 / p50 per clip
import csv, math, sys, os

path, label = sys.argv[1], sys.argv[2]
video = sys.argv[sys.argv.index('--video') + 1] if '--video' in sys.argv else None
R = list(csv.DictReader(open(path)))
f = lambda r, k, d=0.0: float(r[k]) if r.get(k, '') not in ('', '-') else d
T = [f(r, 't') for r in R]
mode = [r['mode'] for r in R]
out = []
P = lambda s: out.append(s)

# ---- events
rel, att = [], []
for i in range(1, len(R)):
    if mode[i - 1] == 'swing' and mode[i] != 'swing': rel.append(i)
    if mode[i] in ('swing', 'zip') and mode[i - 1] not in ('swing', 'zip'): att.append(i)
# end of a web-less air phase (T4): a web / zip, or the air ends on a wall, a perch or the ground
ends = [i for i in range(1, len(R)) if mode[i - 1] == 'air' and mode[i] != 'air']
# flip programs: contiguous runs of flip_prog
progs = []
i = 0
while i < len(R):
    if R[i].get('flip_prog', ''):
        j = i
        while j + 1 < len(R) and R[j + 1].get('flip_prog', '') == R[i]['flip_prog'] and f(R[j + 1], 'flip_t') >= f(R[j], 'flip_t') - 1e-4: j += 1
        progs.append((i, j, R[i]['flip_prog']))
        i = j + 1
    else: i += 1
DUR = {'backDouble': 1.80, 'frontPikeSwan': 1.59, 'corkscrew': 1.67, 'backSingle': 1.24, 'wallFront': 1.14}  # round 14 programs (r13: 1.70 / 1.65 / 1.66 / 1.22)
CATCH = {'backDouble': 0.2}
fails = 0
P('%s: %d releases, %d attaches, %d flip programs (%.1f s)' % (label, len(rel), len(att), len(progs), T[-1]))
for (a, b, name) in progs:
    if name == 'wallFront':
        P('  %.2f-%.2f s wallFront (wall-run top-out; not a web release)' % (T[a], T[b])); continue
    r0 = max([x for x in rel if x <= a] or [None], key=lambda x: x if x is not None else -1)
    d_rel = T[a] - T[r0] if r0 is not None else float('nan')
    reach = next((k for k in range(a, b + 1) if R[k].get('flip_shape', '') == 'Reach'), None)
    t_reach = T[reach] if reach is not None else T[a] + DUR.get(name, T[b] - T[a]) - CATCH.get(name, 0.2)
    nxt = next((x for x in att if x > a), None)
    t_att = T[nxt] if nxt is not None else float('nan')
    shapes = []
    for k in range(a, b + 1):
        s = R[k].get('flip_shape', '')
        if s and (not shapes or shapes[-1] != s): shapes.append(s)
    ok1 = d_rel <= 0.25
    # round 13 (rendered captures): a program still playing on the clip's last frame (the script's last release sits at the end of the
    # clip) cannot show its catch: R2 / C2 are reported "not judged" instead of FAIL (the clip length, not the game, ended it)
    trunc = b >= len(R) - 2
    ok2 = (t_att - t_reach) <= 0.3 if nxt is not None else trunc
    ok_s = len(set(shapes)) <= 2 if name == 'backDouble' else True
    fails += (not ok1) + (not ok2) + (not ok_s)
    P('  %.2f s %-13s R1 release->shape %.2f s %s | R2 reach %.2f -> attach %.2f = %+.2f s %s | program %.2f s, ended %.2f s, cut at t_prog %.2f | shapes %s%s'
      % (T[a], name, d_rel, 'PASS' if ok1 else 'FAIL', t_reach, t_att, t_att - t_reach, ('PASS' if ok2 else 'FAIL') if not (trunc and nxt is None) else 'n/a (clip ends first)', DUR.get(name, 0), T[b],
         f(R[b], 'flip_t'), '/'.join(shapes), (' S1 %d shapes %s' % (len(set(shapes)), 'PASS' if ok_s else 'FAIL')) if name == 'backDouble' else ''))
# ---- T4 / T2
worst4, worst2 = 0.0, 0.0
bad4, bad2 = [], []
for x in rel:
    nxt = next((y for y in ends if y > x), None)
    if nxt is None: continue
    g = T[nxt] - T[x]; worst4 = max(worst4, g)
    if g > 3.1: bad4.append((T[x], g))
for p, q in zip(att, att[1:]):
    g = T[q] - T[p]; worst2 = max(worst2, g)
    if g > 3.3: bad2.append((T[p], g))
fails += len(bad4) + len(bad2)
P('  T4 release -> end of the web-less air (web / zip / wall / perch / ground): max %.2f s (<= 3.1) %s%s' % (worst4, 'PASS' if not bad4 else 'FAIL', ''.join(' [%.2f s: %.2f]' % b for b in bad4)))
P('  T2 attach -> attach: max %.2f s (<= 3.3) %s%s   (attaches at %s)' % (worst2, 'PASS' if not bad2 else 'FAIL', ''.join(' [%.2f s: %.2f]' % b for b in bad2),
  ', '.join('%.2f' % T[a] for a in att)))
# ---- C1 camera continuity (pcm = the rendered view; rows are one frame late, which does not change a per-frame delta)
mp = my = mpos = 0.0; wp = wy = wpos = 0.0; nbad = 0; badt = []
for i in range(1, len(R)):
    try:
        dp = abs(f(R[i], 'pcm_pitch') - f(R[i - 1], 'pcm_pitch'))
        dy = abs((f(R[i], 'pcm_yaw') - f(R[i - 1], 'pcm_yaw') + 180) % 360 - 180)
        dpos = math.dist([f(R[i], k) for k in ('pcm_x', 'pcm_y', 'pcm_z')], [f(R[i - 1], k) for k in ('pcm_x', 'pcm_y', 'pcm_z')])
    except ValueError: continue
    if i < 3: continue  # first rendered rows (pcm of the pre-roll frame)
    if dp > mp: mp, wp = dp, T[i]
    if dy > my: my, wy = dy, T[i]
    if dpos > mpos: mpos, wpos = dpos, T[i]
    if dp > 3 or dy > 4 or dpos > 1.2: nbad += 1; badt.append(T[i])
fails += nbad
slew = [int(f(r, 'cam_slew')) for r in R if r.get('cam_slew', '') not in ('', '-')]
P('  C1 per-frame camera: max |d pitch| %.2f deg @%.2f s (<= 3), |d yaw| %.2f deg @%.2f s (<= 4), |d pos| %.2f m @%.2f s (<= 1.2) -> %d frames over %s%s'
  % (mp, wp, my, wy, mpos, wpos, nbad, 'PASS' if nbad == 0 else 'FAIL', (' at ' + ', '.join('%.2f' % t for t in badt[:8])) if badt else ''))
if slew:
    P('     slew limiter active: position %d, pitch %d, yaw %d frames (of %d)' % (sum(1 for s in slew if s & 1), sum(1 for s in slew if s & 2),
      sum(1 for s in slew if s & 4), len(slew)))
cig = sum(1 for r in R if r.get('cam_in_geometry', '0') == '1')
P('     camera in geometry: %d frames' % cig)
# ---- C2 blend-out
for (a, b, name) in progs:
    if name == 'wallFront': continue  # the top-out uses the wall camera, not the flip camera
    k0 = f(R[b], 'flipcam_k')
    e = next((k for k in range(b, len(R)) if f(R[k], 'flipcam_k') < 0.02), None)
    if e is None: P('  C2 %.2f s %s: flip camera still blending at the clip end (not judged: the clip ends first)' % (T[b], name)); continue
    dur = T[e] - T[b]
    okb = dur >= 0.4
    fails += not okb
    P('  C2 %.2f s %-13s flip camera k %.2f at the program end -> < 0.02 after %.2f s (>= 0.4) %s' % (T[b], name, k0, dur, 'PASS' if okb else 'FAIL'))
# ---- V1 hero brightness
if video and os.path.exists(video):
    try:
        import cv2, numpy as np
        cap = cv2.VideoCapture(video)
        vals = []; allv = []
        i = 0
        while True:
            ok, im = cap.read()
            if not ok or i >= len(R): break
            r = R[i]
            if i % 3 == 0 and r.get('px_top', '') not in ('', '-'):
                t, bb, l, rr = [int(float(r[k])) for k in ('px_top', 'px_bottom', 'px_left', 'px_right')]
                if bb - t > 20 and rr - l > 10:
                    cy, cx, hh, ww = (t + bb) / 2, (l + rr) / 2, (bb - t) * 0.3, (rr - l) * 0.3
                    crop = im[int(cy - hh):int(cy + hh), int(cx - ww):int(cx + ww)]
                    if crop.size:
                        v = float(np.median(cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)[..., 2]))
                        allv.append(v)
                        if r['mode'] == 'air' and r['sub'] in ('trick', 'topOut'): vals.append(v)
            i += 1
        if vals:
            P('  V1 hero brightness (median V, central 60 %% of the pixel bbox): trick frames p10 %.0f / p50 %.0f / min %.0f; all frames p10 %.0f / p50 %.0f'
              % (np.percentile(vals, 10), np.median(vals), min(vals), np.percentile(allv, 10), np.median(allv)))
    except ImportError:
        P('  V1: needs cv2 (venv _scratch/traversal/specv)')
P('  => %s (%d failing lines / frames)' % ('PASS' if fails == 0 else 'FAIL', fails))
print('\n'.join(out))
