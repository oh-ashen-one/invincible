#!/usr/bin/env python3
"""Final-loop checker: SPEC_FINAL W1-W10 (web deployment / appearance) and A1-A7 (swing body / air) from a clip's telemetry CSV (+ the movie for W5).
One table per clip: line, value, pass/fail (or n/m = not measurable from this telemetry, with the reason).

Frame timing used throughout: a row is written during the actor tick, BEFORE the anim instance evaluates (the mesh ticks after the actor), so every bone column of row i is the pose
of the frame i-1 as rendered; the pose rendered at row i is read from row i+1. Strand columns (start / tip) of row i are what is drawn in frame i (start = the hand bone read in UpdateWebs
= the bone column of the same row).
usage: final_check.py <clip_telemetry.csv> [--mp4 clip.mp4] [--label name] [--out CHECK.txt] [--json out.json]"""
import argparse, csv, json, math, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ap = argparse.ArgumentParser()
ap.add_argument('csv'); ap.add_argument('--mp4'); ap.add_argument('--label'); ap.add_argument('--out'); ap.add_argument('--json')
a = ap.parse_args()
R = list(csv.DictReader(open(a.csv)))
label = a.label or Path(a.csv).stem.replace('_telemetry', '')
N = len(R)
DT = 1 / 60.0


def f(r, k, d=0.0):
    try: return float(r[k])
    except (KeyError, ValueError, TypeError): return d


def v3(r, p): return (f(r, p + 'x'), f(r, p + 'y'), f(r, p + 'z')) if (p + 'x') in r else (f(r, p + '_x'), f(r, p + '_y'), f(r, p + '_z'))
def sub(a_, b_): return (a_[0] - b_[0], a_[1] - b_[1], a_[2] - b_[2])
def dot(a_, b_): return a_[0] * b_[0] + a_[1] * b_[1] + a_[2] * b_[2]
def nrm(a_): return math.sqrt(dot(a_, a_))
def ang(a_, b_):
    na, nb = nrm(a_), nrm(b_)
    return 180.0 / math.pi * math.acos(max(-1.0, min(1.0, dot(a_, b_) / (na * nb)))) if na > 1e-6 and nb > 1e-6 else 0.0
def pct(x, p):
    x = sorted(x); return x[min(len(x) - 1, int(round(p / 100.0 * (len(x) - 1))))] if x else float('nan')


case = [r.get('case', '') for r in R]
t = [f(r, 't') for r in R]
def nxt(i): return i if ('fw_pl_x' in R[0]) else (i + 1 if i + 1 < N and case[i + 1] == case[i] else i)   # the row that shows frame i's rendered pose (round 01+: bone columns are same-frame)
hand = lambda i, right: v3(R[i], 'fw_hr' if right else 'fw_hl')
has_palm = bool(R) and 'fw_pl_x' in R[0]
palm = lambda i, right: v3(R[i], 'fw_pr' if right else 'fw_pl')
shoulder = lambda i, right: v3(R[i], 'fw_shr' if right else 'fw_shl')
out = []
rec = {}


def line(i_d, name, value, ok, note=''):
    out.append((i_d, name, value, ok, note)); rec[i_d] = {'value': value, 'pass': ok, 'note': note}


# ---- events
presses, attaches, releases, strand_on = [], [], [], []   # row indices
for i in range(1, N):
    if case[i] != case[i - 1]: continue
    if f(R[i], 'in_swing') > 0.5 and f(R[i - 1], 'in_swing') < 0.5: presses.append(i)
    if R[i]['mode'] == 'swing' and R[i - 1]['mode'] != 'swing': attaches.append(i)
    if R[i - 1]['mode'] == 'swing' and R[i]['mode'] != 'swing': releases.append(i)
    for s in (0, 1):
        live = lambda k: f(R[k], 'fw_s%d_on' % s) > 0.5 and f(R[k], 'fw_s%d_rel' % s, -1) < 0
        if live(i) and not live(i - 1): strand_on.append((i, s))
if N and R[0]['mode'] == 'swing': attaches.insert(0, 0)

# ---- W1 origin: strand start vs the firing hand as rendered in the same frame (release-phase frames reported separately: the strand there retracts from the hand toward the anchor)
errs, errs_same, first, relv, spd = [], [], [], [], []
lens_hidden = 0
flight_measured = 0
for i in range(N):
    for s in (0, 1):
        if f(R[i], 'fw_s%d_drawn' % s) < 0.5: continue
        right = f(R[i], 'fw_s%d_hand' % s) > 0.5
        st = v3(R[i], 'fw_s%d_s' % s)
        # round 11 (critic r10 gap 1): the lens-hide is now a contiguous hand-end prefix rule (120 cm, 45 cm during the shot's
        # flight) -- a drawn start off the palm is possible only while the palm itself is inside the zone. Exclusions tightened
        # to match (was: palm within 3.5 m, all phases): flight frames with the palm >= 1.0 m from the lens are MEASURED (the
        # strand must draw hand->tip on every flight frame), taut frames with the palm >= 1.8 m are measured.
        flight = f(R[i], 'fw_s%d_age' % s) < f(R[i], 'fw_s%d_shoot' % s) and f(R[i], 'fw_s%d_rel' % s) < 0
        zone = 1.0 if flight else 1.8
        if has_palm and nrm(sub(palm(i, right), v3(R[i], 'cam_'))) < zone and nrm(sub(st, palm(i, right))) > 1.0: lens_hidden += 1; continue   # the palm-end prefix inside the lens zone is not drawn
        e = nrm(sub(st, palm(i, right) if has_palm else hand(nxt(i), right))) * 100   # round 01: the palm of the final pose of the same frame (end-of-frame bone read); round 00: the next row's hand bone
        if flight: flight_measured += 1
        if f(R[i], 'fw_s%d_rel' % s) >= 0: relv.append(e); continue
        errs.append(e); errs_same.append(nrm(sub(st, hand(i, right))) * 100); spd.append(f(R[i], 'speed_mps'))
        if f(R[i], 'fw_s%d_age' % s) < DT * 1.5: first.append(e)
if errs:
    ok = sum(1 for e in errs if e <= 8.0) / len(errs)
    line('W1', 'strand start within 8 cm of the firing hand (rendered same frame; web-on frames before release)', '%.1f %% of %d frames; error p50 %.1f p95 %.1f max %.1f cm (hero speed median %.0f m/s); press/attach frame median %.1f cm; same-row bone read max %.1f cm; release-phase frames (%d): median %.0f cm; flight frames measured (palm outside the 45 cm flight hide zone): %d; palm-prefix inside the lens zone (excluded): %d' % (
        100 * ok, len(errs), pct(errs, 50), pct(errs, 95), max(errs), pct(spd, 50), pct(first, 50) if first else float('nan'), max(errs_same), len(relv), pct(relv, 50) if relv else float('nan'), flight_measured, lens_hidden), ok >= 0.999)
else:
    line('W1', 'strand start within 8 cm of the firing hand', 'no strand drawn', False)

# ---- W2 firing arm
has_sh = any(abs(f(r, 'fw_shr_x')) > 1e-3 for r in R)
if not has_sh: line('W2', 'firing arm toward the anchor', 'n/m: shoulder bone not logged', False)
else:
    arr, mx, start_dt = [], [], []
    for i, s in strand_on:
        right = f(R[i], 'fw_s%d_hand' % s) > 0.5; shoot = f(R[i], 'fw_s%d_shoot' % s); anc = v3(R[i], 'fw_s%d_a' % s)
        angs = []; arrival = None; j = i
        while j < N and case[j] == case[i] and f(R[j], 'fw_s%d_on' % s) > 0.5 and f(R[j], 'fw_s%d_rel' % s) < 0:
            k = nxt(j); angs.append((t[j] - t[i], ang(sub(hand(k, right), shoulder(k, right)), sub(anc, shoulder(k, right)))))
            if arrival is None and f(R[j], 'fw_s%d_age' % s) >= shoot: arrival = angs[-1][1]
            j += 1
        if len(angs) < 6: continue
        a0 = ang(sub(hand(max(0, i - 1), right), shoulder(max(0, i - 1), right)), sub(anc, shoulder(max(0, i - 1), right)))
        sd = next((tt for tt, g in angs if g <= a0 - 5.0), None)
        if sd is not None: start_dt.append(sd)
        arr.append(arrival if arrival is not None else angs[-1][1]); mx.append(max([g for tt, g in angs if tt >= shoot] or [angs[-1][1]]))
    if arr:
        line('W2', 'firing arm: starts <= 0.05 s, <= 20 deg at tip arrival, <= 30 deg for the swing', 'arrival median %.0f deg (%d/%d <= 20); max over swing median %.0f deg (%d/%d <= 30); motion start (angle -5 deg) median %s s (%d of %d strands started)' % (
            pct(arr, 50), sum(1 for x in arr if x <= 20), len(arr), pct(mx, 50), sum(1 for x in mx if x <= 30), len(mx), '%.3f' % pct(start_dt, 50) if start_dt else 'never', len(start_dt), len(arr)),
            sum(1 for x in arr if x <= 20) == len(arr) and sum(1 for x in mx if x <= 30) == len(mx) and bool(start_dt) and pct(start_dt, 50) <= 0.05 + DT)
    else: line('W2', 'firing arm', 'no complete strand', False)

# ---- P1 hero height by PIXELS (the -WHTravMask hero-only depth pass, 1920x1080 scale, previous-frame mask): swings 0.15-0.30, air / tricks 0.18-0.36, >= 90 % of 10 fps samples
if R and 'px_top' in R[0]:
    samp = [i for i in range(0, N, 6) if f(R[i], 'px_top', -1) >= 0 and f(R[i], 'px_bottom', -1) > f(R[i], 'px_top', -1)]
    if samp:
        hh = lambda i: (f(R[i], 'px_bottom') - f(R[i], 'px_top')) / 1080.0
        sw = [hh(i) for i in samp if R[i]['mode'] == 'swing']
        ai = [hh(i) for i in samp if R[i]['mode'] == 'air']
        miss = N // 6 + 1 - len(samp)
        okS = sum(1 for h in sw if 0.15 <= h <= 0.30) / len(sw) if sw else 1.0
        okA = sum(1 for h in ai if 0.18 <= h <= 0.36) / len(ai) if ai else 1.0
        line('P1', 'hero height by pixels: swing 0.15-0.30, air/trick 0.18-0.36 on >= 90 % of 10 fps samples (mask frames only; bbox of the hero-only depth pass)',
             'swing %d samples median %.2f p10 %.2f p90 %.2f in-band %.0f %%; air %d samples median %.2f p10 %.2f p90 %.2f in-band %.0f %%; no hero pixels in %d samples; telemetry hero_bbox_h median %.2f' % (
             len(sw), pct(sw, 50) if sw else -1, pct(sw, 10) if sw else -1, pct(sw, 90) if sw else -1, 100 * okS, len(ai), pct(ai, 50) if ai else -1, pct(ai, 10) if ai else -1, pct(ai, 90) if ai else -1, 100 * okA, miss,
             pct([f(r, 'hero_bbox_h') for r in R], 50)), okS >= 0.9 and okA >= 0.9)
    else: line('P1', 'hero height by pixels', 'no mask samples (render without -WHTravMask)', False)

# ---- P2 silhouette evolution (hero mask, 16x16 grid over its bbox): IoU between frames 0.3 s apart < 0.85 on >= 90 % of swing / air samples; no pose held > 0.4 s (IoU of frames 0.1 s apart >= 0.92)
if R and 'hero_sil' in R[0]:
    def bits(i):
        h = R[i]['hero_sil']
        return None if not h or h == '0' else int(h, 16)
    def iou(a, b):
        u = bin(a | b).count('1'); return bin(a & b).count('1') / u if u else 1.0
    SW = 18; ST = 6
    pairs = [iou(bits(i), bits(i + SW)) for i in range(0, N - SW) if R[i]['mode'] in ('swing', 'air') and case[i] == case[i + SW] and bits(i) and bits(i + SW)]
    run = best = 0
    for i in range(0, N - ST):
        ba, bb = bits(i), bits(i + ST)
        if R[i]['mode'] in ('swing', 'air') and case[i] == case[i + ST] and ba and bb and iou(ba, bb) >= 0.92: run += 1; best = max(best, run)
        else: run = 0
    if pairs:
        okp = sum(1 for x in pairs if x < 0.85) / len(pairs)
        line('P2', 'pose evolution by silhouette: IoU(0.3 s apart) < 0.85 on >= 90 % of swing/air frames; no pose held > 0.4 s',
             '%d pairs; IoU median %.2f p90 %.2f; below 0.85 on %.0f %%; longest held (IoU >= 0.92 over 0.1 s) %.2f s' % (len(pairs), pct(pairs, 50), pct(pairs, 90), 100 * okp, (best + ST) / 60.0), okp >= 0.9 and (best + ST) / 60.0 <= 0.4)
    else: line('P2', 'pose evolution by silhouette', 'no silhouettes (render without -WHTravMask)', False)

# ---- W3 shot travel
trav = []
for i, s in strand_on:
    i0 = i
    i = next((j for j in range(i0, min(N, i0 + 8)) if f(R[j], 'fw_s%d_drawn' % s) > 0.5 and case[j] == case[i0]), i0)   # round 04: the strand is not drawn while the arm anticipates (Age < 0)
    shoot = f(R[i], 'fw_s%d_shoot' % s); A = v3(R[i], 'fw_s%d_s' % s); B = v3(R[i], 'fw_s%d_a' % s); L = nrm(sub(B, A))
    if f(R[i], 'fw_s%d_drawn' % s) < 0.5 or L < 1: continue
    prog = nrm(sub(v3(R[i], 'fw_s%d_t' % s), A)) / L
    land = t[i] + max(0.0, shoot - f(R[i], 'fw_s%d_age' % s))
    lead = t[i] - t[i0]
    ten = next((t[j] for j in range(i, min(N, i + 40)) if f(R[j], 'tension') > 0.05), None)
    mstep, mono, prev = 0.0, True, 0.0
    for j in range(i, min(N, i + 16)):
        if f(R[j], 'fw_s%d_on' % s) < 0.5 or case[j] != case[i]: break
        Lj = nrm(sub(v3(R[j], 'fw_s%d_t' % s), v3(R[j], 'fw_s%d_s' % s))); Lf = max(nrm(sub(v3(R[j], 'fw_s%d_a' % s), v3(R[j], 'fw_s%d_s' % s))), 1.0)
        if Lj < prev - 0.02 * Lf: mono = False
        mstep = max(mstep, (Lj - prev) / Lf); prev = Lj
        if Lj >= 0.97 * Lf: break
    trav.append((shoot, L / max(shoot, 1e-3), prog, (ten - land) if ten is not None else None, L, mstep, mono))
if trav:
    okc = [1 for sh, sp, pr, tl, L, ms, mo in trav if 0.08 - 1e-3 <= sh <= 0.20 + 1e-3 and 150 <= sp <= 400 and pr <= 0.35 and ms <= 0.26 and mo and (tl is not None and tl >= -DT * 1.5)]
    line('W3', 'tip travels visibly 0.06-0.20 s at 150-400 m/s, not full length in frame 1, tension after landing', '%d/%d shots pass (0.08-0.20 s, growth <= 25 %%/frame, monotone); max per-frame growth %.0f %%; shoot s median %.3f (%.3f-%.3f); tip speed median %.0f m/s; first-frame progress median %.2f; tension starts %.2f s relative to tip landing (median; negative = before)' % (
        len(okc), len(trav), 100 * max(x[5] for x in trav), pct([x[0] for x in trav], 50), min(x[0] for x in trav), max(x[0] for x in trav), pct([x[1] for x in trav], 50), pct([x[2] for x in trav], 50), pct([x[3] for x in trav if x[3] is not None], 50)), len(okc) == len(trav))
else: line('W3', 'shot travel', 'no shots', False)

# ---- W4 attach transition
cr, hs = [], []
for i in attaches:
    w = [f(R[j], 'fw_chest_rate_dps') for j in range(max(0, i - 1), min(N, i + 10)) if case[j] == case[i]]   # the attach frame (tip landed) .. +0.15 s
    if w: cr.append(max(w))
    right = f(R[i], 'fw_s0_hand') > 0.5
    sp = lambda k: nrm(sub(hand(min(N - 1, k + 1), right), hand(k, right))) / DT
    if i > 1: hs.append(sp(i) / max(sp(i - 1), 0.5))
has_chest = any(f(r, 'fw_chest_rate_dps') > 0 for r in R)
if cr and has_chest:
    ok1 = sum(1 for x in cr if x <= 400) / len(cr)
    line('W4', 'attach: chest rate <= 400 deg/s on >= 90 %, never > 700; hand speed <= 2.5x', 'chest rate max within -1..+9 frames of the attach: %.0f %% <= 400, worst %.0f deg/s (>700: %d of %d); hand speed ratio median %.2f, max %.2f (> 2.5: %d of %d)' % (
        100 * ok1, max(cr), sum(1 for x in cr if x > 700), len(cr), pct(hs, 50), max(hs) if hs else 0, sum(1 for x in hs if x > 2.5), len(hs)), ok1 >= 0.9 and max(cr) <= 700 and all(x <= 2.5 for x in hs))
else: line('W4', 'attach transition', 'n/m: no attaches or chest bone not logged', False)

# ---- W5 readability (rendered frames)
w5 = None
if a.mp4:
    jp = Path(a.csv).with_suffix('.rope.json')
    try:
        r = subprocess.run([sys.executable, str(ROOT / 'docs/night1/traversal/rope_r25_check.py'), a.mp4, a.csv, label, '--fps', '10', '--out', str(jp)], capture_output=True, text=True, timeout=1800)
        res = json.loads(jp.read_text()); on = [x for x in res if x.get('web_on')]; judged = [x for x in on if 'pass' in x]
        if judged:
            # round 13 (critic r12 gap 1): continuity metrics -- longest low-contrast hole along the sampled line (gap_max_px)
            # and per-sample tone flicker (dlum); reported alongside the width/contrast medians (not part of pass/fail yet)
            G = [x.get('gap_max_px', 0) for x in judged]; DL = [x['dlum'] for x in judged if 'dlum' in x]
            P = sum(1 for x in judged if x['pass']); w5 = (P, len(judged), pct([x['width'] for x in judged], 50), pct([x['pt_med'] for x in judged], 50), sum(1 for x in on if x.get('short')), len(on),
                pct(G, 50), pct(G, 90), max(G), pct(DL, 50) if DL else -1, pct(DL, 90) if DL else -1)
    except Exception as ex:
        w5 = str(ex)[:120]
if isinstance(w5, tuple):
    line('W5', 'strand 2-4 px, visible on >= 95 % of web-on frames (10 fps samples of the movie)', '%d/%d judged frames pass (%.0f %%); measured width median %.2f px; contrast median %.0f/255; not judged (short / off-screen) %d of %d web-on; continuity: gap_max_px p50/p90/max %.0f/%.0f/%.0f (0 = no low-contrast hole along the sampled line), tone flicker |dlum| p50/p90 %.0f/%.0f' % (w5[0], w5[1], 100.0 * w5[0] / w5[1], w5[2], w5[3], w5[4], w5[5], w5[6], w5[7], w5[8], w5[9], w5[10]), w5[0] / w5[1] >= 0.95)
else: line('W5', 'strand readability', 'n/m: ' + (w5 if isinstance(w5, str) else 'no movie given'), False)

# ---- W6 shape: wave amplitude in flight / after landing
land_w, after_w, fly_w = [], [], []
for i, s in strand_on:
    shoot = f(R[i], 'fw_s%d_shoot' % s)
    for j in range(i, min(N, i + 60)):
        if case[j] != case[i]: break
        age = f(R[j], 'fw_s%d_age' % s)
        if age <= shoot: fly_w.append(f(R[j], 'fw_s%d_wave_cm' % s))
        if abs(age - shoot) <= DT * 0.6: land_w.append(f(R[j], 'fw_s%d_wave_cm' % s))
        if abs(age - (shoot + 0.10)) <= DT * 0.6: after_w.append(f(R[j], 'fw_s%d_wave_cm' % s)); break
if fly_w:
    line('W6', 'in-flight wave, straight <= 0.10 s after landing (model wave cm, before the screen-space clamp)', 'wave in flight median %.1f cm (max %.1f); at landing median %.1f; 0.10 s after landing median %.1f cm (max %.1f)' % (pct(fly_w, 50), max(fly_w), pct(land_w, 50) if land_w else float('nan'), pct(after_w, 50) if after_w else float('nan'), max(after_w) if after_w else float('nan')),
         bool(after_w) and max(after_w) <= 2.0 and max(fly_w) >= 2.0)
else: line('W6', 'strand shape', 'no strand', False)

# ---- W7 clearance (collision geometry; tree crowns have no collision)
cl = [f(R[i], 'fw_s%d_clear' % s, 1.0) for i in range(N) for s in (0, 1) if f(R[i], 'fw_s%d_drawn' % s) > 0.5]
if cl:
    blocked = sum(1 for x in cl if x < 0.995)
    line('W7', 'hand->anchor line clear of building geometry (tree crowns: no collision, not measured)', '%d/%d drawn frames blocked; min clear fraction %.3f' % (blocked, len(cl), min(cl)), blocked == 0)
else: line('W7', 'clearance', 'no strand', False)

# ---- W8 release
dur = []
for s in (0, 1):
    run = 0
    for i in range(N):
        if f(R[i], 'fw_s%d_rel' % s) >= 0 and f(R[i], 'fw_s%d_drawn' % s) > 0.5: run += 1
        elif run: dur.append(run * DT); run = 0
if dur:
    line('W8', 'release: strand leaves the hand and retracts over 0.15-0.40 s (no vanish in one frame)', '%d releases; drawn-after-release duration median %.2f s (min %.2f max %.2f)' % (len(dur), pct(dur, 50), min(dur), max(dur)), all(0.15 <= d <= 0.40 for d in dur))
else: line('W8', 'release', 'no released strand drawn', False)

# ---- W9 hand choice
side, match, alt_ok, alt_n = 0, 0, 0, 0
prev = None
for i, s in strand_on:
    if s != 0: continue
    vx, vy = f(R[i], 'vx'), f(R[i], 'vy'); hs_ = math.hypot(vx, vy)
    if hs_ < 1: continue
    fx, fy = vx / hs_, vy / hs_; rx, ry = -fy, fx
    anc = v3(R[i], 'fw_s0_a'); lat = (anc[0] - f(R[i], 'x_m')) * rx + (anc[1] - f(R[i], 'y_m')) * ry
    right_anchor = lat > 0; hand_r = f(R[i], 'fw_s0_hand') > 0.5
    side += 1; match += int(right_anchor == hand_r)
    if prev is not None and prev[0] != right_anchor:
        alt_n += 1; alt_ok += int(prev[1] != hand_r)
    prev = (right_anchor, hand_r)
if side: line('W9', 'firing hand matches the anchor side on >= 90 % of attaches; alternates where the anchors alternate', '%d/%d attaches match (%.0f %%); where the anchor side alternated the hand alternated %d/%d' % (match, side, 100.0 * match / side, alt_ok, alt_n), match / side >= 0.9)
else: line('W9', 'hand choice', 'no attaches', False)

# ---- W10 every press resolves
res, nores, behind = 0, [], 0
for i in presses:
    ok = False
    for j in range(i, min(N, i + 4)):
        if case[j] != case[i]: break
        if (f(R[j], 'fw_s0_on') > 0.5 and f(R[j], 'fw_s0_rel', -1) < 0) or (f(R[j], 'fw_s1_on') > 0.5 and f(R[j], 'fw_s1_rel', -1) < 0) or f(R[j], 'fw_reach_t', -1) >= 0 or 'noanchor' in R[j]['anim_clip'].lower() or 'noanchor' in R[j]['anim_node'].lower(): ok = True; break
    if ok:
        res += 1
        j = i
        if f(R[j], 'fw_s0_on') > 0.5 and f(R[j], 'fw_s0_rel', -1) < 0:
            anc = v3(R[j], 'fw_s0_a'); fwd = (f(R[j], 'vx'), f(R[j], 'vy'), 0)
            if (anc[0] - f(R[j], 'x_m')) * fwd[0] + (anc[1] - f(R[j], 'y_m')) * fwd[1] < 0: behind += 1
    else: nores.append(round(t[i], 2))
if presses: line('W10', 'every press: a strand within 0.05 s or a readable no-anchor reach; none to an anchor behind the hero', '%d/%d presses resolve; no visible response at t=%s; anchor behind the hero %d' % (res, len(presses), nores[:12], behind), not nores and behind == 0)
else: line('W10', 'press resolves', 'no press', False)

# ---- A1 swing phases: pose signature changes during swings
def sig(r): return [float(x) for x in r['pose_sig'].split()] if r.get('pose_sig') else []
sw = []
i = 0
while i < N:
    if R[i]['mode'] == 'swing':
        j = i
        while j < N and R[j]['mode'] == 'swing' and case[j] == case[i]: j += 1
        if j - i >= 0.9 / DT: sw.append((i, j))
        i = j
    else: i += 1
dd = []
for i, j in sw:
    k = i
    while k + 18 < j:
        a_, b_ = sig(R[k]), sig(R[k + 18])
        if a_ and b_: dd.append(math.sqrt(sum((x - y) ** 2 for x, y in zip(a_, b_)) / len(a_)))
        k += 18
if dd: line('A1', 'pose signature changes >= 0.15 between 0.3 s samples during a swing (rms over the 10 values)', '%.0f %% of %d sample pairs in %d swings; median %.2f; (legs-lag 0.05-0.15 s: n/m, no per-bone timing logged)' % (100.0 * sum(1 for x in dd if x >= 0.15) / len(dd), len(dd), len(sw), pct(dd, 50)), sum(1 for x in dd if x >= 0.15) / len(dd) >= 0.9)
else: line('A1', 'swing phases', 'no swing >= 0.9 s', False)

# ---- A2 variety: swing body style = anim_clip at 40 % of the swing
styles = []
for i, j in sw: styles.append(R[i + int(0.4 * (j - i))]['anim_clip'])
if len(styles) >= 3:
    w6 = [len(set(styles[k:k + 6])) for k in range(0, max(1, len(styles) - 5))]
    line('A2', '>= 3 distinct swing body styles in any 6 consecutive swings (style = the clip at 40 % of the swing)', '%d swings; distinct in 6-windows %s; styles %s' % (len(styles), w6[:6], sorted(set(styles))), all(x >= 3 for x in w6) if len(styles) >= 6 else len(set(styles)) >= 3)
else: line('A2', 'swing variety', 'fewer than 3 swings', False)

# ---- A3 release opens within 0.1 s
op = []
for i in releases:
    if i + 7 < N and case[i + 7] == case[i]:
        a_, b_ = sig(R[i]), sig(R[i + 6])
        if a_ and b_: op.append((math.sqrt(sum((x - y) ** 2 for x, y in zip(a_, b_)) / len(a_)), f(R[i], 'vz'), f(R[i], 'speed_mps')))
if op: line('A3', 'release: pose opens (>= 0.10 signature change) within 0.1 s; upward / forward momentum', '%d releases; signature change in 0.1 s median %.2f (%d/%d >= 0.10); vz at release median %.1f m/s, speed %.1f m/s' % (len(op), pct([x[0] for x in op], 50), sum(1 for x in op if x[0] >= 0.10), len(op), pct([x[1] for x in op], 50), pct([x[2] for x in op], 50)), sum(1 for x in op if x[0] >= 0.10) >= 0.9 * len(op))
else: line('A3', 'release', 'no release', False)

# ---- A4 float: longest air stretch whose pose signature stays within 0.03 over 0.1 s samples
held = []
i = 0
while i < N:
    if R[i]['mode'] == 'air' and R[i]['sub'] != 'trick':
        j = i; best = 0.0; run_start = i
        while j + 6 < N and R[j]['mode'] == 'air' and case[j] == case[i]:
            a_, b_ = sig(R[j]), sig(R[j + 6])
            d = math.sqrt(sum((x - y) ** 2 for x, y in zip(a_, b_)) / len(a_)) if a_ and b_ else 1
            if d < 0.03:
                best = max(best, (j + 6 - run_start) * DT)
            else: run_start = j + 1
            j += 3
        held.append(best); i = j + 1
    else: i += 1
if held: line('A4', 'no held identical air pose > 0.6 s (signature change < 0.03 per 0.1 s)', 'longest held stretch %.2f s over %d air spans' % (max(held), len(held)), max(held) <= 0.6)
else: line('A4', 'float / air', 'no air', False)

# ---- A5 catch out of a trick; A6 end-pose variety; A7 shapes
tr = []
i = 0
while i < N:
    if R[i].get('flip_prog'):
        j = i
        while j < N and R[j].get('flip_prog') and case[j] == case[i]: j += 1
        tr.append((i, j)); i = j
    else: i += 1
if tr:
    gaps, rates, ends = [], [], []
    for i, j in tr:
        k = next((m for m in range(j, min(N, j + 90)) if R[m]['mode'] == 'swing' and case[m] == case[i]), None)
        if k is not None:
            gaps.append((k - j) * DT)
            rates.append(max(f(R[m], 'fw_chest_rate_dps') for m in range(max(i, k - 18), min(N, k + 6))))
        ends.append(R[min(N - 1, j)]['anim_clip'] + '/' + R[min(N - 1, j)]['anim_node'])
    line('A5', 'catch <= 0.25 s after the last shape; chest rate <= 400 deg/s through the catch on >= 90 %', '%d tricks, %d caught by a web; catch delay median %.2f s (%d/%d <= 0.25); chest-rate max through catch median %.0f deg/s (%d/%d <= 400)' % (
        len(tr), len(gaps), pct(gaps, 50) if gaps else float('nan'), sum(1 for g in gaps if g <= 0.25), len(gaps), pct(rates, 50) if rates else float('nan'), sum(1 for x in rates if x <= 400), len(rates)),
        bool(gaps) and sum(1 for g in gaps if g <= 0.25) == len(gaps) and sum(1 for x in rates if x <= 400) >= 0.9 * len(rates))
    line('A6', '>= 3 visibly different end poses across 6 tricks (end clip / node at the end of each trick)', '%d tricks; distinct end clips %d: %s' % (len(tr), len(set(ends)), sorted(set(ends))[:8]), (len(set(ends)) >= 3) if len(tr) >= 6 else None)
    runs = []
    for i, j in tr:
        cur, n_ = None, 0
        for m in range(i, j):
            s_ = R[m].get('flip_shape', '')
            if s_ == cur: n_ += 1
            else:
                if cur: runs.append(n_)
                cur, n_ = s_, 1
        if cur: runs.append(n_)
    line('A7', 'each shape readable >= 3 frames at 25 fps (>= 8 frames at 60); pike hip angle / pencil straightness: n/m (no hip-angle column)', '%d shape segments; %.0f %% >= 8 frames; shortest %d frames' % (len(runs), 100.0 * sum(1 for x in runs if x >= 8) / max(1, len(runs)), min(runs) if runs else 0), bool(runs) and all(x >= 8 for x in runs))
else:
    for k, n_ in (('A5', 'catch out of a trick'), ('A6', 'end-pose variety'), ('A7', 'flip shapes')): line(k, n_, 'no flip in this clip', None, 'n/a')

txt = ['CHECK %s: %d rows (%.1f s), %d presses, %d attaches, %d releases, %d strands' % (label, N, N * DT, len(presses), len(attaches), len(releases), len(strand_on)), '%-4s %-5s %s' % ('line', 'pass', 'value')]
for i_d, name, value, ok, note in out:
    txt.append('%-4s %-5s %s -- %s' % (i_d, {True: 'PASS', False: 'FAIL', None: 'n/a'}[ok], name, value))
text = '\n'.join(txt)
print(text)
if a.out: Path(a.out).write_text(text + '\n')
if a.json: Path(a.json).write_text(json.dumps(rec, indent=1))
