#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# TRAVERSAL-SPEC video instrument for T3 / T5 / T6 (rope on screen, reaches the frame edge, angle, width) and T8-T10 (hero
# box from the YOLO person masks), on a 1080p capture. Same method as the round-09 blind critic (critic-P3-r09 rope.py /
# pick.py): hero = the person detection holding the most red suit pixels; rope = the longest black-hat Hough line (>= 160 px)
# whose lower end lies within 60 px of the hero box.
# usage: rope_px_check.py <dets.json from specs/tools/ref_hero_dets.py (step 6 = 10 fps)> <frames dir (ffmpeg fps=10, %04d.jpg)> <label> [t0 t1]
import json, math, sys
import cv2, numpy as np
dets, fd, tag = sys.argv[1], sys.argv[2], sys.argv[3]
T0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
T1 = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
D = json.load(open(dets)); res = []
VMIN = 4.0  # deg from vertical: shorter angles are facade edges, not the rope
for k, fr in enumerate(D):
    im = cv2.imread(f'{fd}/%04d.jpg' % (k + 1))
    if im is None: break
    hh, ww = im.shape[:2]; hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    red = (((hsv[..., 0] < 10) | (hsv[..., 0] > 168)) & (hsv[..., 1] > 110) & (hsv[..., 2] > 60))
    best = None; bs = 0; bn = None
    for d in fr['dets']:
        b = d.get('mbox') or d['box']; x0, y0, x1, y1 = int(b[0] * ww), int(b[1] * hh), int(b[2] * ww), int(b[3] * hh)
        s = red[y0:y1, x0:x1].sum()
        if s > bs: bs, best, bn = s, (x0, y0, x1, y1), b
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
    m = (bh > 18).astype(np.uint8) * 255
    if best:
        x0, y0, x1, y1 = best; m[max(0, y0 - 5):y1 + 5, max(0, x0 - 5):x1 + 5] = 0
    L = cv2.HoughLinesP(m, 1, np.pi / 360, 80, minLineLength=160, maxLineGap=12)
    rope = None; vline = False
    if L is not None and best:
        x0, y0, x1, y1 = best; pad = 60
        for l in L.reshape(-1, 4):
            a, b, c, d = map(float, l)
            if b > d: a, b, c, d = c, d, a, b
            if x0 - pad <= c <= x1 + pad and y0 - pad <= d <= y1 + pad and d - b > 40:
                ang = abs(math.degrees(math.atan2(c - a, d - b))); L2 = math.hypot(c - a, d - b)
                if ang < VMIN: vline = True; continue   # facade verticals (critic r09: near-vertical lines excluded)
                if rope is None or L2 > rope[1]: rope = (ang, L2, (a, b, c, d))
    wpx = None
    if rope:
        a, b, c, d = rope[2]; ws = []
        for f in (0.3, 0.5, 0.7):
            px, py = a + (c - a) * f, b + (d - b) * f; n = np.array([d - b, -(c - a)]); n /= np.linalg.norm(n)
            prof = np.array([bh[int(py + n[1] * s), int(px + n[0] * s)] if 0 <= int(py + n[1] * s) < hh and 0 <= int(px + n[0] * s) < ww else 0
                             for s in range(-8, 9)], float)
            if prof.max() > 0: ws.append((prof > 0.5 * prof.max()).sum())
        wpx = float(np.median(ws)) if ws else None
    hero = None
    if bn is not None and bs >= 30: hero = dict(h=bn[3] - bn[1], cx=(bn[0] + bn[2]) / 2, cy=(bn[1] + bn[3]) / 2)
    res.append(dict(t=fr['t'], rope=rope is not None, vline=vline and rope is None, ang=round(rope[0], 1) if rope else None, top=round(rope[2][1]) if rope else None,
                    w=wpx, hero=hero))
json.dump(res, open(tag + '_rope.json', 'w'))
R = [r for r in res if T0 - 1e-6 <= r['t'] <= T1 + 1e-6]
on = np.array([r['rope'] for r in R])
print(f'{tag}: {len(R)} samples at 10 fps, window {R[0]["t"]:.1f}-{R[-1]["t"]:.1f} s')
print(f' T3 rope on screen, whole window: {on.mean():.2f}  (+ frames with only a near-vertical (<{VMIN:.0f} deg) line at the hero: {np.mean([r["vline"] for r in R]):.2f})')
W = []
for w0 in range(0, max(1, len(R) - 79), 5):
    W.append((R[w0]['t'], on[w0:w0 + 80].mean()))
print(' T3 per 8 s window (start: frac): ' + ' '.join(f'{t:.1f}:{f:.2f}' for t, f in W))
print(f' T3 8 s windows min/max: {min(f for _, f in W):.2f}/{max(f for _, f in W):.2f}')
# web-less runs (rope not detected) >= 1.5 s
runs = []; st = None
for r in R:
    if not r['rope'] and st is None: st = r['t']
    if r['rope'] and st is not None: runs.append((st, r['t'])); st = None
if st is not None: runs.append((st, R[-1]['t'] + 0.1))
print(' rope-less runs >= 1.0 s: ' + ' '.join(f'{a:.1f}-{b:.1f}' for a, b in runs if b - a >= 1.0))
A = [r['ang'] for r in R if r['rope']]; Wd = [r['w'] for r in R if r['rope'] and r['w']]; T = [r['top'] for r in R if r['rope']]
if A: print(' T6 angle from vertical p10/50/90 ' + '/'.join('%.1f' % v for v in np.percentile(A, [10, 50, 90])) + f'  width px p50 {np.median(Wd) if Wd else float("nan"):.1f}'
            + f' | T5 rope reaches the top edge (<= 15 px) {np.mean(np.array(T) <= 15):.2f}')
Hh = [r['hero'] for r in R if r['hero']]
if Hh:
    h = np.array([x['h'] for x in Hh]); cx = np.array([x['cx'] for x in Hh]); cy = np.array([x['cy'] for x in Hh])
    print(f' hero found {len(Hh)}/{len(R)} (T16)')
    print(' T8 hero h p10/50/90 %.3f/%.3f/%.3f min %.3f' % (*np.percentile(h, [10, 50, 90]), h.min()))
    print(' T9 hero cx p5/p95 %.3f/%.3f' % tuple(np.percentile(cx, [5, 95])))
    print(' T10 hero cy p5/p95 %.3f/%.3f spread %.3f' % (*np.percentile(cy, [5, 95]), np.percentile(cy, 95) - np.percentile(cy, 5)))
print(' ' + ''.join('R' if r['rope'] else '.' for r in R))
