#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 25 run-cadence hard line (director; characters r12-r14 instrument loco_r12.py `bob`): head-top FFT 3.2-3.8 Hz over 1.5-11 s of a pawn
# run clip. The characters stage had a flat background (row-median mask); in the city the hero is found from the rendered hero mask box
# of the telemetry (px_left..px_bottom, reported one row late) and, inside that box (+15 px), the suit pixels of the movie (red: H < 10 or
# > 168, S > 110, V > 60; blue: H 100-130, S > 110, V > 40). Head top = the 0.5th percentile row of the suit pixels. Same signal processing as
# loco_r12.bob: 31-frame moving-average detrend, Hann window, FFT peak in 1-6 Hz, plus bob minima per second. The mask box top itself
# (4 px grid) is reported as a cross-check.
# usage: cadence_r25.py <movie.mp4> <telemetry.csv> [t0 t1]
import csv, json, sys
import cv2
import numpy as np
from scipy.signal import find_peaks

mp4, tel = sys.argv[1], sys.argv[2]
T0 = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
T1 = float(sys.argv[4]) if len(sys.argv) > 4 else 11.0
rows = list(csv.DictReader(open(tel)))
cap = cv2.VideoCapture(mp4); fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
Y, YM, TT = [], [], []
k = 0
while True:
    ok, f = cap.read()
    if not ok or k >= len(rows): break
    t = float(rows[k]['t'])
    if T0 <= t <= T1:
        rr = rows[min(k + 1, len(rows) - 1)]
        try:
            l, tp, r, b = (float(rr[c]) for c in ('px_left', 'px_top', 'px_right', 'px_bottom'))
        except ValueError:
            l = -1
        if l >= 0:
            H, W = f.shape[:2]
            x0, y0, x1, y1 = int(max(0, l - 15)), int(max(0, tp - 15)), int(min(W, r + 15)), int(min(H, b + 15))
            hsv = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
            h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
            m = ((((h < 10) | (h > 168)) & (s > 110) & (v > 60)) | ((h >= 100) & (h <= 130) & (s > 110) & (v > 40)))
            ys = np.nonzero(m)[0]
            if len(ys) > 30:
                Y.append(y0 + np.percentile(ys, 0.5)); YM.append(tp); TT.append(t)
    k += 1


def bob(Yv):
    Yv = np.asarray(Yv, float)
    T = Yv - np.convolve(Yv, np.ones(31) / 31, 'same'); T = T[15:-15]
    F = np.abs(np.fft.rfft(T * np.hanning(len(T)))); fr = np.fft.rfftfreq(len(T), 1 / fps); sel = (fr > 1) & (fr < 6)
    pk = float(fr[sel][np.argmax(F[sel])])
    mins, _ = find_peaks(T, distance=int(fps / 6), prominence=max(0.5, 0.25 * np.std(T)))  # rows grow downward: a peak of y = lowest head
    return pk, len(mins) / (len(T) / fps), float(np.std(T))


out = dict(clip=mp4, t0=T0, t1=T1, fps=fps, frames=len(Y))
if len(Y) > 120:
    pk, mps, sd = bob(Y); pkm, mpsm, sdm = bob(YM)
    out.update(head_top_fft_hz=round(pk, 3), head_low_per_s=round(mps, 2), head_bob_sd_px=round(sd, 2),
               mask_top_fft_hz=round(pkm, 3), mask_low_per_s=round(mpsm, 2), target='3.2-3.8 Hz', ok=bool(3.2 <= pk <= 3.8))
sp = [float(r['hspeed_mps']) for r in rows if T0 <= float(r['t']) <= T1]
clips = {}
for r in rows:
    if T0 <= float(r['t']) <= T1: clips[r['anim_clip']] = clips.get(r['anim_clip'], 0) + 1
out.update(speed_median=round(float(np.median(sp)), 2) if sp else None, anim_clips=clips)
print(json.dumps(out))
