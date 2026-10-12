#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 25 rope readability test (critic r24 biggest gap, SPEC T5 / T6), on the rendered movie at 10 fps:
#   every web_on frame: the rope runs hand -> frame edge, is 2-4 px wide, and its mean luminance differs by >= 25/255 from a 6 px band on
#   either side -- including over dark glass at 10.5-11.2 s and over pale facades at 0.9-1.1 s.
# Where the rope is: the telemetry's projection of the strand as drawn (rope_ax/ay -> rope_bx/by, through the final camera of that frame;
# r25 columns). The line is sampled every 8 px from the hand end to the frame edge (or to its far end when that lies inside the frame),
# skipping the hero box (+8 px). At each sample point the luminance profile across the line (bilinear, Rec.601 luma of the 8-bit video) is
# read; the rope centre is re-found within +-3 px of the prediction (the offset with the largest rope-vs-band difference); rope pixels =
# |s - s0| <= w/2 with w = the drawn width there (rope_wpx_a .. rope_wpx_b), bands = the 6 px beyond w/2 + 1 px on each side.
# Reported per frame:
#   pt_pass   share of sample points whose rope mean differs >= 25 from BOTH bands (local readability along the rope)
#   pt_med    median over points of min(|rope - left band|, |rope - right band|)
#   glob      the literal whole-rope reading: |mean of all rope pixels - mean of all left-band pixels| and the same for the right band (min)
#   width     median measured width: pixels of the profile deviating > half the peak deviation from the band mean (contiguous around s0)
#   edge      the drawn line leaves the frame (far end outside) -- "hand -> frame edge"
#   gap_max_px / gap_pts (final round 13, critic r12: beaded/dashed strand) -- the longest run of CONSECUTIVE sample points along the line
#             whose rope-vs-band contrast is < 12 (locally invisible), x 8 px; a sampling break (hero box / frame edge) breaks a run
#   dlum      |rope_lum - previous judged frame's rope_lum| (tone flicker per 0.1 s sample)
# A frame PASSES when pt_med >= 25 and pt_pass >= 0.8 and the median measured width is 2-4 px; frames whose visible rope is < 40 px long
# (rope leaving the frame right at the hand, or released) are listed as 'short' and not judged.
# usage: rope_r25_check.py <movie.mp4> <telemetry.csv> <label> [--fps 10] [--debug <dir> t,t,...]
import argparse, csv, json, math, os
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('mp4'); ap.add_argument('csv'); ap.add_argument('label')
ap.add_argument('--fps', type=float, default=10.0)
ap.add_argument('--debug', nargs=2, default=None)
ap.add_argument('--thr', type=float, default=25.0)
ap.add_argument('--out', default=None)
a = ap.parse_args()
rows = list(csv.DictReader(open(a.csv)))
cap = cv2.VideoCapture(a.mp4)
vfps = cap.get(cv2.CAP_PROP_FPS) or 60.0
step = max(1, int(round(vfps / a.fps)))
dbg_t = set(round(float(x), 2) for x in a.debug[1].split(',')) if a.debug else set()
if a.debug: os.makedirs(a.debug[0], exist_ok=True)


def fl(r, k, d=-1.0):
    try: return float(r[k])
    except (KeyError, ValueError): return d


def clip_seg(x0, y0, x1, y1, W, H):
    """Liang-Barsky clip of the segment to [0,W-1]x[0,H-1]; returns (x0,y0,x1,y1,far_outside) or None."""
    dx, dy = x1 - x0, y1 - y0; t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0), (dx, W - 1 - x0), (-dy, y0), (dy, H - 1 - y0)):
        if abs(p) < 1e-12:
            if q < 0: return None
            continue
        r = q / p
        if p < 0: t0 = max(t0, r)
        else: t1 = min(t1, r)
        if t0 > t1: return None
    return (x0 + dx * t0, y0 + dy * t0, x0 + dx * t1, y0 + dy * t1, t1 < 1.0 - 1e-9)


def bilin(img, x, y):
    h, w = img.shape
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


res = []
k = 0
while True:
    ok, frame = cap.read()
    if not ok: break
    if k % step == 0 and k < len(rows):
        r = rows[k]; t = fl(r, 't')
        rec = dict(t=round(t, 3), web_on=int(fl(r, 'web_on', 0) > 0.5), drawn=int(fl(r, 'rope_drawn', 0)))
        if rec['web_on'] and rec['drawn'] > 0 and fl(r, 'rope_ax', -1) > -1:
            H, W = frame.shape[:2]
            g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            ax, ay, bx, by = fl(r, 'rope_ax') * W, fl(r, 'rope_ay') * H, fl(r, 'rope_bx') * W, fl(r, 'rope_by') * H
            wa, wb = fl(r, 'rope_wpx_a'), fl(r, 'rope_wpx_b')
            cs = clip_seg(ax, ay, bx, by, W, H)
            # hero box (the mask of this frame is reported on the next row) + 8 px
            hb = []
            for rr in (r, rows[min(k + 1, len(rows) - 1)]):
                if fl(rr, 'px_top') >= 0: hb.append((fl(rr, 'px_left') - 8, fl(rr, 'px_top') - 8, fl(rr, 'px_right') + 8, fl(rr, 'px_bottom') + 8))
            if cs is None:
                rec.update(short=True, vis_len=0.0)
            else:
                x0, y0, x1, y1, far_out = cs
                L = math.hypot(x1 - x0, y1 - y0)
                rec.update(edge=bool(far_out), vis_len=round(L, 1))
                ux, uy = (x1 - x0) / max(L, 1e-6), (y1 - y0) / max(L, 1e-6); nx, ny = -uy, ux
                LT = math.hypot(bx - ax, by - ay)
                pts = []
                for s in np.arange(4.0, L, 8.0):
                    px, py = x0 + ux * s, y0 + uy * s
                    if any(b[0] <= px <= b[2] and b[1] <= py <= b[3] for b in hb): continue
                    if px < 12 or py < 12 or px > W - 13 or py > H - 13: continue
                    f = math.hypot(px - ax, py - ay) / max(LT, 1e-6)
                    pts.append((px, py, wa + (wb - wa) * min(1.0, f)))
                rec['n_pts'] = len(pts)
                if len(pts) < 5:
                    rec['short'] = True
                else:
                    S = np.arange(-16, 16.01, 0.5)
                    PX = np.array([p[0] for p in pts])[:, None] + nx * S[None, :]
                    PY = np.array([p[1] for p in pts])[:, None] + ny * S[None, :]
                    prof = bilin(g, PX, PY)                                 # points x offsets (0.5 px)
                    con, Rv, Lv, Rt, widths = [], [], [], [], []
                    for i, p in enumerate(pts):
                        w = float(np.clip(p[2], 1.0, 8.0)); best = None
                        for s0 in np.arange(-3.0, 3.01, 0.5):
                            rm = np.abs(S - s0) <= w / 2
                            lm = (S < s0 - w / 2 - 1) & (S >= s0 - w / 2 - 7)
                            gm = (S > s0 + w / 2 + 1) & (S <= s0 + w / 2 + 7)
                            vr, vl, vg = prof[i, rm].mean(), prof[i, lm].mean(), prof[i, gm].mean()
                            c = min(abs(vr - vl), abs(vr - vg))
                            if best is None or c > best[0]: best = (c, vr, vl, vg, s0)
                        c, vr, vl, vg, s0 = best
                        con.append(c); Rv.append(vr); Lv.append(vl); Rt.append(vg)
                        band = 0.5 * (vl + vg); dev = np.abs(prof[i] - band); pk = dev[np.abs(S - s0) <= w / 2 + 1].max()
                        j0 = int(np.argmin(np.abs(S - s0))); lo = hi = j0
                        while lo > 0 and dev[lo - 1] > 0.5 * pk: lo -= 1
                        while hi < len(S) - 1 and dev[hi + 1] > 0.5 * pk: hi += 1
                        widths.append((hi - lo + 1) * 0.5)
                    con = np.array(con)
                    # final round 13 (critic r12 gap 1: the strand renders BEADED/DASHED in daylight -- width/contrast medians
                    # pass while the line has holes): continuity along the sampled strand line. A "gap point" is a sample whose
                    # rope-vs-band contrast is < 12 (half the 25 readability threshold: the strand is locally invisible there).
                    # gap_max_px = the longest run of consecutive gap points along the line (8 px sampling; a sampling break --
                    # the hero box or the frame edge -- does NOT count as a strand gap). dlum = |rope_lum - previous sampled
                    # frame's rope_lum| (tone flicker frame to frame; filled by the caller loop below).
                    grun = gbest = 0
                    prev_pt = None
                    for i, p in enumerate(pts):
                        brk = prev_pt is not None and math.hypot(p[0] - prev_pt[0], p[1] - prev_pt[1]) > 12.0
                        if con[i] < 12.0:
                            grun = 1 if brk else grun + 1
                            gbest = max(gbest, grun)
                        else:
                            grun = 0
                        prev_pt = p
                    rec.update(pt_pass=round(float((con >= a.thr).mean()), 3), pt_med=round(float(np.median(con)), 1), pt_p10=round(float(np.percentile(con, 10)), 1),
                               glob=round(float(min(abs(np.mean(Rv) - np.mean(Lv)), abs(np.mean(Rv) - np.mean(Rt)))), 1),
                               rope_lum=round(float(np.mean(Rv)), 1), band_lum=round(float(0.5 * (np.mean(Lv) + np.mean(Rt))), 1),
                               width=round(float(np.median(widths)), 2), wdraw=round(float(np.median([p[2] for p in pts])), 2),
                               gap_max_px=gbest * 8, gap_pts=int(gbest))
                    rec['pass'] = bool(rec['pt_med'] >= a.thr and rec['pt_pass'] >= 0.8 and 2.0 <= rec['width'] <= 4.0)
                if a.debug and round(t, 2) in dbg_t:
                    im = frame.copy()
                    cv2.line(im, (int(x0), int(y0)), (int(x1), int(y1)), (0, 255, 255), 1)
                    for p in pts: cv2.circle(im, (int(p[0] + nx * 12), int(p[1] + ny * 12)), 1, (255, 0, 255), -1)
                    cv2.imwrite(os.path.join(a.debug[0], f'{a.label}_{t:.2f}.png'), im)
        res.append(rec)
    k += 1
on = [x for x in res if x['web_on']]
judged = [x for x in on if 'pass' in x]
short = [x for x in on if x.get('short')]
prev_lum = None
for x in res:   # tone flicker: |rope luminance - previous JUDGED frame's| (samples are 0.1 s apart at 10 fps)
    if 'rope_lum' not in x: continue
    if prev_lum is not None: x['dlum'] = round(abs(x['rope_lum'] - prev_lum), 1)
    prev_lum = x['rope_lum']
print(f"{a.label}: {len(res)} samples at {a.fps:g} fps, web_on {len(on)} ({100.0 * len(on) / max(1, len(res)):.1f} %), judged {len(judged)}, short/not drawn {len(short) + len(on) - len(judged) - len(short)}")
if judged:
    P = [x for x in judged if x['pass']]
    print(f"  PASS {len(P)}/{len(judged)} judged web_on frames (pt_med >= {a.thr:g}, pt_pass >= .8, width 2-4 px)")
    print(f"  pt_med p10/p50 {np.percentile([x['pt_med'] for x in judged], 10):.1f}/{np.median([x['pt_med'] for x in judged]):.1f}; pt_pass median {np.median([x['pt_pass'] for x in judged]):.2f}; "
          f"glob (whole-rope literal) >= {a.thr:g}: {sum(1 for x in judged if x['glob'] >= a.thr)}/{len(judged)}; width median {np.median([x['width'] for x in judged]):.2f} px "
          f"(drawn {np.median([x['wdraw'] for x in judged]):.2f}); edge {sum(1 for x in judged if x.get('edge'))}/{len(judged)}")
    G = [x.get('gap_max_px', 0) for x in judged]; DL = [x['dlum'] for x in judged if 'dlum' in x]
    print(f"  continuity (r13): gap_max_px median {np.median(G):.0f} p90 {np.percentile(G, 90):.0f} max {max(G)} (0 = no low-contrast hole along the sampled line); "
          f"frames with an interior gap run > 16 px: {sum(1 for g in G if g > 16)}/{len(G)}; tone flicker |dlum| p50/p90 {np.median(DL):.1f}/{np.percentile(DL, 90):.1f} per 0.1 s")
    for nm, t0, t1 in (('pale facades 0.9-1.1 s', 0.9, 1.1), ('dark glass 10.5-11.2 s', 10.5, 11.2)):
        W_ = [x for x in judged if t0 - 1e-6 <= x['t'] <= t1 + 1e-6]
        if W_: print(f"  {nm}: " + ' '.join(f"{x['t']:.1f}:{'P' if x['pass'] else 'F'}(med {x['pt_med']:.0f}, pass {x['pt_pass']:.2f}, glob {x['glob']:.0f}, rope {x['rope_lum']:.0f}/band {x['band_lum']:.0f}, w {x['width']:.1f})" for x in W_))
    F = [x for x in judged if not x['pass']]
    if F: print('  failing: ' + ' '.join(f"{x['t']:.1f}(med {x['pt_med']:.0f} pass {x['pt_pass']:.2f} w {x['width']:.1f})" for x in F[:40]))
json.dump(res, open(a.out or (a.label + '_rope25.json'), 'w'))
