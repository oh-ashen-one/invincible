#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 12, suit-agnostic pixel measures on the plain skins stage (sky gradient + flat floor, so the background is the per-row median colour):

  ch1   STILL [STILL ...]           hero height / frame height (CH1 target 0.48 - 0.62), hero = pixels > 38 RGB from the row's median colour, largest blob
  bob   CLIP t0 t1                  step rate from the head-top bob (FFT peak 1 - 6 Hz and bob minima per s) of the hero blob (CH6), any suit colour
  tpop  TELEMETRY.csv t0 t1        idle -> run start from the pawn telemetry (clip switch weight, frames to 90 % of the pose change)
  pop   CLIP t0 t1                  largest single-frame change of the hero blob's height and width (relative) in the window: an idle -> run cut in
                                    1 frame shows as one big jump, a >= 0.15 s blend (CH10) as >= 9 small steps
All print JSON."""
import sys, json
import numpy as np
import cv2


def hero_mask(f, thr=38.0):
    med = np.median(f, axis=1, keepdims=True)
    d = np.abs(f.astype(np.float32) - med.astype(np.float32)).max(-1)
    m = (d > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(m, np.ones((9, 9), np.uint8)))
    if n < 2: return None
    k = 1 + int(np.argmax(st[1:, 4]))
    return (lab == k) & (m > 0)


def ch1(paths):
    out = []
    for p in paths:
        f = cv2.imread(p); m = hero_mask(f)
        ys, xs = np.nonzero(m)
        top, bot = int(np.percentile(ys, 0.05)), int(np.percentile(ys, 99.95))
        out.append(dict(image=p, top=top, bottom=bot, height_frac=round((bot - top) / f.shape[0], 3), ok=bool(0.48 <= (bot - top) / f.shape[0] <= 0.62)))
    return dict(target='0.48-0.62', stills=out, all_ok=all(o['ok'] for o in out))


def frames(path, t0, t1):
    cap = cv2.VideoCapture(path); fps = cap.get(5) or 60.0; i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t = i / fps; i += 1
        if t0 <= t <= t1: yield t, f, fps


def track(path, t0, t1):
    R = []
    for t, f, fps in frames(path, t0, t1):
        m = hero_mask(f)
        if m is None: continue
        ys, xs = np.nonzero(m)
        R.append((t, np.percentile(ys, 0.3), ys.max() - ys.min(), xs.max() - xs.min(), fps))
    return np.array(R)


def bob(path, t0, t1):
    from scipy.signal import find_peaks
    R = track(path, t0, t1); fps = float(R[0, 4])
    Y = R[:, 1]; T = Y - np.convolve(Y, np.ones(31) / 31, 'same'); T = T[15:-15]
    F = np.abs(np.fft.rfft(T * np.hanning(len(T)))); fr = np.fft.rfftfreq(len(T), 1 / fps); sel = (fr > 1) & (fr < 6)
    pk, _ = find_peaks(-T, distance=8, prominence=1.5)
    per = np.diff(pk) / fps if len(pk) > 2 else np.array([np.nan])
    return dict(clip=path, t0=t0, t1=t1, fps=fps, frames=len(R), bob_fft_hz=round(float(fr[np.argmax(F * sel)]), 3), bob_minima_per_s=round(len(pk) / (len(T) / fps), 3),
                median_minima_period_frames=round(float(np.median(per) * fps), 2), steps_per_s_from_period=round(float(1 / np.median(per)), 3),
                hero_height_frac_median=round(float(np.median(R[:, 2]) / 1080.0), 3))


def pop(path, t0, t1):
    R = track(path, t0, t1)
    h = R[:, 2] / np.median(R[:, 2]); w = R[:, 3] / np.median(R[:, 3])
    dh = np.abs(np.diff(h)); dw = np.abs(np.diff(w))
    i = int(np.argmax(dh + dw))
    return dict(clip=path, t0=t0, t1=t1, frames=len(R), max_frame_change_height=round(float(dh.max()), 3), max_frame_change_width=round(float(dw.max()), 3),
                at_t=round(float(R[i + 1, 0]), 3), median_frame_change=round(float(np.median(dh + dw)), 4))


if __name__ == '__main__' and sys.argv[1] != 'tpop':
    c, a = sys.argv[1], sys.argv[2:]
    r = ch1(a) if c == 'ch1' else bob(a[0], float(a[1]), float(a[2])) if c == 'bob' else pop(a[0], float(a[1]), float(a[2]))
    print(json.dumps(r))


def tpop(csv_path, t0, t1):
    """Idle -> run start from the pawn's own telemetry (-WHTravScript run, P3 WebTravAnimInstance): clip switches with their blend weights and the per-frame
    change of the 10-number pose signature; a 1-frame pop = the whole pose change lands in 1-2 frames, a >= 0.15 s blend spreads it over >= 9 frames."""
    import csv
    rows = list(csv.reader(open(csv_path))); h = rows[0]
    ic, iw, ip, it = h.index('anim_clip'), h.index('anim_weight'), h.index('pose_sig'), h.index('t')
    out = []; prev = None; sw = []
    for r in rows[1:]:
        t = float(r[it])
        if not (t0 <= t <= t1): continue
        sig = np.array([float(v) for v in r[ip].split()])
        if prev is not None:
            out.append((t, float(np.linalg.norm(sig - prev[1])), r[ic], float(r[iw])))
            if r[ic] != prev[2]: sw.append(dict(t=round(t, 4), from_clip=prev[2], to_clip=r[ic], weight=float(r[iw])))
        prev = (t, sig, r[ic])
    d = np.array([o[1] for o in out]); tt = np.array([o[0] for o in out])
    # the start: the first clip switch to a locomotion clip; the pose change around it
    k = next((i for i, o in enumerate(out) if o[2] not in ('A_Hero_idle',) and out[max(i - 1, 0)][2] == 'A_Hero_idle'), None)
    res = dict(csv=csv_path, t0=t0, t1=t1, clip_switches=sw[:8])
    if k is not None:
        w = d[k:k + 30]; tot = float(w.sum())
        c = np.cumsum(w) / max(tot, 1e-9)
        n90 = int(np.searchsorted(c, 0.9)) + 1
        res.update(start_t=round(float(tt[k]), 4), switch_weight=out[k][3], pose_change_first_frame_share=round(float(w[0] / max(tot, 1e-9)), 3),
                   largest_frame_share=round(float(w.max() / max(tot, 1e-9)), 3), frames_to_90pct_of_pose_change=n90, seconds_to_90pct=round(n90 / 60.0, 3))
    return res


if __name__ == '__main__' and sys.argv[1] == 'tpop':
    print(json.dumps(tpop(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))))
