#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 12: the critic r11 sky-ring test (same measure as the critic's sky.py). Round 16: TC-I of TRICK_CAMERA_SPEC = pooled over the clips,
# >= 35 % of trick samples with ring >= 50 % sky AND hero h >= .15 (was >= 70 % per clip); px_* read one row late (shifted). For every 6th frame of a 60 fps capture (10 fps)
# in which a release trick / top-out flip plays (mode air, sub trick|topOut): a ring 40 px wide around the hero's pixel bbox
# (telemetry px_top/bottom/left/right, 1080p), sky pixel = bright and flat (V > 170, |Laplacian| < 12) or blue (H 95-125, S > 60,
# V > 120). Target (critic r11): >= 70 % of trick frames have >= 50 % sky in the ring AND hero bbox height >= 0.15 of the frame.
# usage: sky_check.py <round dir> <clip> [clip ...]   (clip = mp4 basename; <clip>_telemetry.csv beside it)
import csv, sys, os
import cv2, numpy as np
R = sys.argv[1]
tot_all = []
for n in sys.argv[2:]:
    T = list(csv.DictReader(open(os.path.join(R, n + '_telemetry.csv'))))
    for k in range(len(T) - 1):
        for c in ('px_top', 'px_bottom', 'px_left', 'px_right'): T[k][c] = T[k + 1][c]
    cap = cv2.VideoCapture(os.path.join(R, n + '.mp4'))
    i = 0; rows = []
    while True:
        ok, im = cap.read()
        if not ok or i >= len(T): break
        r = T[i]
        if i % 6 == 0 and r['mode'] == 'air' and r['sub'] in ('trick', 'topOut'):
            t, b, l, rr = [int(float(r[k])) for k in ('px_top', 'px_bottom', 'px_left', 'px_right')]
            H, W = im.shape[:2]; m = 40
            if b > t and rr > l:
                y0, y1, x0, x1 = max(0, t - m), min(H, b + m), max(0, l - m), min(W, rr + m)
                hsv = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
                mask = np.ones(hsv.shape[:2], bool); mask[max(0, t - y0):b - y0, max(0, l - x0):rr - x0] = False
                g = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(float)
                lap = np.abs(cv2.Laplacian(g, cv2.CV_64F))
                sky = ((hsv[..., 2] > 170) & (lap < 12)) | ((hsv[..., 0] > 95) & (hsv[..., 0] < 125) & (hsv[..., 1] > 60) & (hsv[..., 2] > 120))
                rows.append((float(r['t']), float(sky[mask].mean()) if mask.any() else 0.0, (b - t) / H, r.get('flip_prog', '') or r['sub']))
            else:
                rows.append((float(r['t']), 0.0, 0.0, r.get('flip_prog', '') or r['sub']))
        i += 1
    if not rows:
        print(n, 'no trick frames'); continue
    s = np.array([x[1] for x in rows]); h = np.array([x[2] for x in rows])
    both = (s >= .5) & (h >= .15)
    tot_all += list(both)
    print('%s: trick samples %d | ring sky p50 %.2f | frames >= 50%% sky %d%% | hero h p10/p50 %.3f/%.3f | frames sky>=.5 AND h>=.15: %d%% -> %s'
          % (n, len(rows), np.median(s), 100 * (s >= .5).mean(), *np.percentile(h, [10, 50]), 100 * both.mean(), 'info (TC-I is pooled)'))
    print('   ', ' '.join('%.1f:%.2f/%.2f' % (a, b, c) for a, b, c, _ in rows))
if tot_all:
    print('TC-I pooled over the clips: %d trick samples, %d%% have ring >= 50%% sky AND hero h >= .15 (need >= 35%%) -> %s' % (len(tot_all), 100 * np.mean(tot_all), 'PASS' if np.mean(tot_all) >= .35 else 'FAIL'))
