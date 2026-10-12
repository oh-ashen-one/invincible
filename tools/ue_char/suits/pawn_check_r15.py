#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 15 pass test of the critic r14 "single biggest gap" on the playable pawn (P3's `WebTravAnimInstance`, merged from Opus-5.5-Loop-Night-1 r22: GroundBlendS 0.18 s),
measured on the swap movie of the real game and on the pawn's own telemetry:

  P1 luma pops   swap_pawn_T_key.mp4, 0 - 1.5 s: the mean absolute luma difference between consecutive frames (whole frame, and the hero blob only); no frame's difference is above 2x BOTH of
                 its neighbours' (the critic's "no frame diff exceeds 2x its neighbours in 0 - 1.5 s": r14 had pose pops at the frame 7 -> 8 start)
  P2 weight step pawn_telemetry.csv: no step of the telemetry's `anim_weight` above dt / 0.18 per frame (dt = 1/60 s: 0.0926).  NOTE `anim_weight` is the TOTAL clip weight (1.0 always:
                 docs/night1/traversal/r22_checks.py G22), so P2 is trivially met; the ground blend itself is checked on `pose_sig` (P3): the largest single-frame change of the 10-number
                 pose signature relative to the 0.5 - 2.0 s median, and the clip switches in 0 - 1.5 s
  python3 pawn_check_r15.py <swap_pawn_T_key.mp4> <pawn_telemetry.csv> [r14 mp4] [r14 csv]   -> JSON
"""
import sys, os, csv, json
import numpy as np
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loco_r12 as L  # noqa: E402


def luma_diffs(path, t0=0.0, t1=1.5):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
    prev = None; prev_h = None; out = []; i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t = i / fps; i += 1
        if t > t1 + 0.1: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None and t0 <= t <= t1 + 0.05:
            d = float(np.abs(g - prev).mean())
            m = L.hero_mask(f)
            dh = float(np.abs(g - prev)[m].mean()) if m is not None and m.sum() > 500 else float('nan')
            out.append((t, d, dh))
        prev = g
    return out, fps


def pops(diffs, col, floor):
    """frames whose difference is above 2x BOTH neighbours' and above an absolute floor (a 2x ratio of two tiny noise values is not a pop)"""
    v = np.array([d[col] for d in diffs], np.float64); t = [d[0] for d in diffs]; bad = []
    for i in range(1, len(v) - 1):
        nb = max(v[i - 1], v[i + 1])
        if np.isfinite(v[i]) and v[i] > 2.0 * nb and v[i] > floor: bad.append(dict(t=round(t[i], 4), diff=round(float(v[i]), 3), neighbours=[round(float(v[i - 1]), 3), round(float(v[i + 1]), 3)]))
    return bad


def telemetry(path, t0=0.0, t1=1.5, blend_s=0.18):
    rows = list(csv.DictReader(open(path)))
    T = np.array([float(r['t']) for r in rows]); W = np.array([float(r['anim_weight']) for r in rows])
    dt = np.diff(T); dw = np.abs(np.diff(W))
    lim = dt / blend_s
    sel = (T[1:] >= t0) & (T[1:] <= t1)
    P = np.array([[float(x) for x in r['pose_sig'].split()] for r in rows])
    dp = np.linalg.norm(np.diff(P, axis=0), axis=1)
    base = np.median(dp[(T[1:] >= 0.5) & (T[1:] <= 2.0)]) if ((T[1:] >= 0.5) & (T[1:] <= 2.0)).any() else float('nan')
    k = int(np.argmax(np.where(sel, dp, -1)))
    sw = []; prev = None
    for r in rows:
        if prev is not None and r['anim_clip'] != prev and t0 <= float(r['t']) <= t1: sw.append(dict(t=round(float(r['t']), 4), to=r['anim_clip']))
        prev = r['anim_clip']
    return dict(rows=len(rows), anim_weight_max_step=round(float(dw[sel].max()), 4) if sel.any() else None, limit_per_frame=round(float(lim[sel].max()), 4) if sel.any() else None,
                P2_anim_weight_step_ok=bool((dw[sel] <= lim[sel] + 1e-9).all()) if sel.any() else None,
                anim_weight_min=round(float(W.min()), 3), anim_weight_max=round(float(W.max()), 3),
                pose_sig_step_max=round(float(dp[sel].max()), 4), at_t=round(float(T[1:][k]), 4), pose_sig_step_median_0p5_2=round(float(base), 4), pose_sig_step_max_over_median=round(float(dp[sel].max() / base), 2) if base else None,
                clip_switches_0_1p5s=sw)


def main():
    a = sys.argv
    out = {}
    for tag, mp4, csvp in (('r15', a[1], a[2]), ('r14', a[3] if len(a) > 3 else None, a[4] if len(a) > 4 else None)):
        if not mp4 or not os.path.exists(mp4): continue
        d, fps = luma_diffs(mp4)
        arr = np.array([x[1] for x in d])
        rec = dict(movie=mp4, fps=fps, frames_0_1p5s=len(d), luma_diff_median=round(float(np.median(arr)), 3), luma_diff_max=round(float(arr.max()), 3),
                   P1_pops_whole_frame=pops(d, 1, 0.5), P1_pops_hero_blob=pops(d, 2, 3.0))
        rec['P1_ok'] = (not rec['P1_pops_whole_frame']) and (not rec['P1_pops_hero_blob'])
        rec['diffs_first_15'] = [(round(x[0], 3), round(x[1], 3), None if not np.isfinite(x[2]) else round(x[2], 3)) for x in d[:15]]
        if csvp and os.path.exists(csvp): rec['telemetry'] = telemetry(csvp)
        out[tag] = rec
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
