#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat round 03: pixel + telemetry measurements of a recorded fight (run_fight.sh movie output dir).
#   measure_r03.py <movie_out_dir> <out.md> <out.json> [--video <mp4>] [--trim <frames>] [--sheet <boxes.jpg>] [--strips <dir>] [--label <text>]
# Inputs in <movie_out_dir>: fight.mp4 (1080p60, -dumpmovie fixed step, crf 18 master), fight_frames.jsonl (per frame: camera, hit shake, every character's
# screen box + visual yaw + held flag), fight_events.jsonl.  --video measures another encode of the same run instead (e.g. the published crf-30 mp4 that the
# critic sees); --trim = number of frames cut from its start (the published file skips the first 0.9 s = 54 frames).
# Frame alignment: the movie lags the simulation by the render pipeline. The offset L (video index v <-> sim frame f = v + 1 - L + trim) is calibrated from
# the hero's local hit-stop: frames where the sim held the hero (frz = 1 in two consecutive frames) must show ~no change in the hero's crop.
# Round-03 target tests (critic r02 "biggest gap"), per hero blow, all at 480x270 gray, 60 fps (the frames the movie really has):
#   crop_run   : longest run of consecutive frames (1..8 after the contact frame) in which the VICTIM crop (fixed box of the contact frame, +25 % pad) changes
#                by < 1.0 (mean abs gray diff)                                                                                (target >= 3)
#   good_run   : the same, but only frames whose WHOLE-frame diff is >= 1.0 (the camera keeps a 2-4 px shake, the world keeps running)   (target >= 3)
#   flare      : share of the frame that turned red-orange (dR >= 45, dR - dB >= 35, dR >= dG versus the frame before the contact, in a window around the victim)
#                peak over frames 0..6 (target 1-3 %), at frame +8 (target: gone, <= max(0.5 %, 20 % of the peak))
#   frozen     : whole-frame frozen frames = share of frames with whole-frame diff < 0.3, at 60 fps and at 30 fps (frame v vs v-2)   (target <= 3 %)
# plus the r02 tests that are still valid (aggression, telegraph, enemies in frame, hero margin, occluders, snaps) and, from the sim record, the victim
# reaction numbers of react_metrics.py (push >= 0.5 m and rotation >= 30 deg within 0.3 s, heavy blows >= 2 m).
import json, subprocess, sys, os, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import react_metrics as RM

args = sys.argv[1:]
d, out_md, out_json = args[0:3]
def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default
vid = opt('--video', os.path.join(d, 'fight.mp4')); trim = int(opt('--trim', 0)); sheet = opt('--sheet'); strips = opt('--strips'); label = opt('--label', os.path.basename(vid))
W, H = 480, 270

def decode(fmt, ch):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', vid, '-vf', f'scale={W}:{H}:flags=area,format={fmt}', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    fr = []; n = W * H * ch
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        fr.append(np.frombuffer(b, np.uint8).reshape((H, W) if ch == 1 else (H, W, ch)))
    return np.array(fr)
G = decode('gray', 1)          # uint8 (N, H, W)
RGB = decode('rgb24', 3)       # uint8 (N, H, W, 3)
NV = len(G)
V = G.astype(np.int16)
wd = np.zeros(NV); wd[1:] = np.abs(np.diff(V, axis=0)).mean(axis=(1, 2))
wd30 = np.zeros(NV); wd30[2:] = np.abs(V[2:] - V[:-2]).mean(axis=(1, 2))
rows = [json.loads(l) for l in open(os.path.join(d, 'fight_frames.jsonl')) if l.strip()]
byf = {r['f']: r for r in rows}
ev = [json.loads(l) for l in open(os.path.join(d, 'fight_events.jsonl')) if l.strip()]
rt2f = sorted((r['rt'], r['f']) for r in rows)
rts = np.array([x[0] for x in rt2f]); fs = [x[1] for x in rt2f]
def frame_at(rt): return fs[int(np.argmin(np.abs(rts - rt)))]

def edata(r, tag):
    e = [x for x in r['e'] if x[0] == tag]
    return e[0] if e else None
def crop_of(box, pad=0.25):
    if box is None or box[0] < -0.5: return None
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    x0 -= w * pad; x1 += w * pad; y0 -= h * pad; y1 += h * pad
    X0, X1 = int(max(0, x0 * W)), int(min(W, x1 * W)); Y0, Y1 = int(max(0, y0 * H)), int(min(H, y1 * H))
    if X1 - X0 < 12 or Y1 - Y0 < 12: return None
    return X0, Y0, X1, Y1
def crop_box(r, tag):
    if tag == 'hero': return crop_of(r['hero'][3:7])
    e = edata(r, tag)
    return crop_of(e[6:10]) if e else None

# ---- lag calibration on the hero's held frames
def cdiff_hero(v, cb):
    X0, Y0, X1, Y1 = cb
    return float(np.abs(V[v, Y0:Y1, X0:X1] - V[v - 1, Y0:Y1, X0:X1]).mean())
held = [f for f in byf if byf[f]['frz'] and byf.get(f - 1, {}).get('frz')]
best = None
for L in range(-2, 8):
    vs = []
    for f in held:
        v = f - 1 + L - trim; cb = crop_box(byf[f], 'hero')
        if 2 <= v < NV and cb: vs.append(cdiff_hero(v, cb))
    if len(vs) < 20: continue
    m = float(np.mean(vs))
    if best is None or m < best[1]: best = (L, m, len(vs))
L = best[0] if best else 2
def v_of(f): return f - 1 + L - trim
def f_of(v): return v + 1 - L + trim

# ---- variants (experiment runs): the variant event precedes each blow
variants = [(e['rt'], e['ev']) for e in ev if e['ev'].startswith('variant ')]
def variant_at(rt):
    prev = [x for x in variants if x[0] <= rt + 1e-6]
    return prev[-1][1] if prev and rt - prev[-1][0] < 0.02 else None

# ---- contacts
contacts = []
for e in ev:
    s = e['ev']
    if s.startswith('hit ') and '->' in s:
        vt = s.split('->')[1].split()[0]; kind = s.split()[1]
        contacts.append((e['rt'], vt, 'hero->' + vt + ' ' + kind, True))
    elif s.startswith('hero hit by'):
        contacts.append((e['rt'], 'hero', s.split(' dmg')[0].replace('hero hit by ', '') + ' ->hero', False))

def red_mask(v, vref, win, arr=False):
    X0, Y0, X1, Y1 = win
    a = RGB[v, Y0:Y1, X0:X1].astype(np.int16); b = RGB[vref, Y0:Y1, X0:X1].astype(np.int16)
    dd = a - b
    m = (dd[..., 0] >= 45) & (dd[..., 0] - dd[..., 2] >= 35) & (dd[..., 0] >= dd[..., 1])
    return m if arr else int(m.sum())

cres = []
for rt, tag, label_, bHero in contacts:
    fc = frame_at(rt); vc0 = v_of(fc)
    if vc0 + 12 >= NV or vc0 < 3 or fc not in byf: continue
    r = byf[fc]; cb = crop_box(r, tag)
    if not cb: cres.append(dict(rt=rt, label=label_, hero_blow=bHero, note='victim off screen')); continue
    X0, Y0, X1, Y1 = cb
    cdiff = lambda v: float(np.abs(V[v, Y0:Y1, X0:X1] - V[v - 1, Y0:Y1, X0:X1]).mean())
    # the contact frame = the frame (calibrated one -1 .. +3) where the victim crop changes most: the flinch appears there
    vc = max(range(vc0 - 1, vc0 + 4), key=cdiff)
    seq = [cdiff(v) for v in range(vc + 1, vc + 9)]
    wseq = [float(wd[v]) for v in range(vc + 1, vc + 9)]
    run = best_run = good = best_good = 0
    for x, w in zip(seq, wseq):
        run = run + 1 if x < 1.0 else 0; best_run = max(best_run, run)
        good = good + 1 if (x < 1.0 and w >= 1.0) else 0; best_good = max(best_good, good)
    # flare: red-orange area in a window around the victim (0.22 W x 0.30 H each side of the box centre), vs the frame before the contact
    b = r['hero'][3:7] if tag == 'hero' else edata(r, tag)[6:10]
    cx, cy = (b[0] + b[2]) / 2 * W, (b[1] + b[3]) / 2 * H
    win = (int(max(0, cx - 0.22 * W)), int(max(0, cy - 0.30 * H)), int(min(W, cx + 0.22 * W)), int(min(H, cy + 0.30 * H)))
    fl = [round(red_mask(min(NV - 1, vc + k), vc - 1, win) / (W * H) * 100, 2) for k in range(0, 10)]
    # 'gone': the pixels that show the flare at +3 (against +10, flare-free by construction) and how many of them still show it at +7 / +8 (against +10)
    S3 = red_mask(min(NV - 1, vc + 3), min(NV - 1, vc + 10), win, True)
    def left(k):
        return float((red_mask(min(NV - 1, vc + k), min(NV - 1, vc + 10), win, True) & S3).sum()) / max(1, int(S3.sum()))
    f8_resid = round(left(8), 3); f7_left = round(left(7), 3)
    newwhite = lambda v: float(((V[v] - V[vc - 1] > 45) & (V[v] > 200)).mean()) * 100
    crowded = any(rt + 0.01 < r2[0] < rt + 0.16 for r2 in contacts)   # another blow / hit lands within 9 frames: its own flare is still up at frame 8
    cres.append(dict(rt=round(rt, 3), label=label_, hero_blow=bHero, frame=vc, crop=[X0, Y0, X1, Y1], diffs=[round(x, 2) for x in seq], wdiffs=[round(x, 2) for x in wseq],
                     crop_run=best_run, good_run=best_good, flinch_diff=round(cdiff(vc), 2), flare=fl, flare_peak=max(fl[:7]), flare_f8=f8_resid, flare_f7=f7_left, flare_f8_vs_pre=fl[8],
                     flare_f9=fl[9], crowded=crowded, newwhite_peak=round(max(newwhite(v) for v in range(vc, vc + 7)), 2), variant=variant_at(rt),
                     shake_px=round(max(abs(byf[f]['shk'][0]) + abs(byf[f]['shk'][1]) for f in range(fc, fc + 6) if f in byf), 2) if 'shk' in r else None))
okc = [c for c in cres if 'crop_run' in c]
hb = [c for c in okc if c['hero_blow']]

# ---- reaction (sim record)
rres = RM.analyse(rows, ev); rsum = RM.summarize(rres)

# ---- attacks
t0 = next((e['rt'] for e in ev if e['ev'].startswith('fight start')), 0)
starts = [e['rt'] for e in ev if e['ev'].startswith('threat ')]
leads = [float(e['ev'].split('lead ')[1]) for e in ev if e['ev'].startswith('threat ')]
gaps = sorted([(round(b - a, 3), round(a, 2)) for a, b in zip(starts, starts[1:])], reverse=True)
first_gap = round(starts[0] - t0, 3) if starts else None

# ---- per frame: enemies in frame, hero margin, occluders, whole-frame diffs
def clipped(b):
    x0, y0, x1, y1 = max(0, b[0]), max(0, b[1]), min(1, b[2]), min(1, b[3])
    return max(0, x1 - x0), max(0, y1 - y0)
STAND = {'hold', 'approach', 'attack', 'aim', 'fire', 'stagger', 'getup', 'webbed', 'yanked'}
per = []
for v in range(NV):
    f = f_of(v)
    if f not in byf: continue
    r = byf[f]
    if r['rt'] < t0 + 0.5: continue
    hbx = r['hero'][3:7]
    margin = min(hbx[0], hbx[1], 1 - hbx[2], 1 - hbx[3]) if hbx[0] > -0.5 else -1
    n5 = 0; occ = 0.0; nwarn = 0
    for e in r['e']:
        tag, typ, st, x, y, z, bx0, by0, bx1, by1, dist, warn, alive = e[:13]
        if bx0 < -0.5: continue
        cw, ch = clipped([bx0, by0, bx1, by1])
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if alive and st in STAND and 0 <= cx <= 1 and 0 <= cy <= 1 and ch >= 0.05: n5 += 1
        if warn and 0 <= cx <= 1 and 0 <= cy <= 1: nwarn += 1
        if dist < r['hero'][7] - 0.3:
            ox = max(0, min(bx1, hbx[2]) - max(bx0, hbx[0])); oy = max(0, min(by1, hbx[3]) - max(by0, hbx[1]))
            if ox > 0 and oy > 0: occ = max(occ, cw * ch)
    per.append(dict(v=v, rt=r['rt'], n5=n5, margin=margin, occ=occ, warn=nwarn, cine=r.get('cine', 0), wd=float(wd[v]), wd30=float(wd30[v]), frz=r['frz']))
N = len(per)
n5s = np.array([p['n5'] for p in per]); mg = np.array([p['margin'] for p in per]); oc = np.array([p['occ'] for p in per])
wds = np.array([p['wd'] for p in per]); wds30 = np.array([p['wd30'] for p in per])
frozen60 = float((wds < 0.3).mean()) * 100; frozen30 = float((wds30 < 0.3).mean()) * 100
hero_held = np.array([p['frz'] for p in per]) > 0
snaps = [(round(p['rt'], 2), round(p['wd'], 1)) for p in per if p['wd'] > 25]
sh_max = max((max(abs(r['shk'][0]), abs(r['shk'][1])) for r in rows if 'shk' in r), default=0)

# ---- per variant (experiment run)
vt = {}
for c in okc:
    if c['variant']: vt.setdefault(c['variant'].split(' shake')[0], []).append(c)

res = dict(video=vid, label=label, lag_frames=L, lag_calib_mean_hero_diff=None if not best else round(best[1], 3), frames_measured=N, fight_start_rt=t0,
           hero_blows_measured=len(hb), crop_run_ge3=sum(c['crop_run'] >= 3 for c in hb), good_run_ge3=sum(c['good_run'] >= 3 for c in hb),
           crop_run_median=float(np.median([c['crop_run'] for c in hb])) if hb else None, good_run_median=float(np.median([c['good_run'] for c in hb])) if hb else None,
           hero_hit_contacts=sum(not c['hero_blow'] for c in okc), hero_hit_crop_run_ge3=sum(c['crop_run'] >= 3 for c in okc if not c['hero_blow']),
           flare_peak_min=min((c['flare_peak'] for c in hb), default=None), flare_peak_median=float(np.median([c['flare_peak'] for c in hb])) if hb else None,
           flare_peak_max=max((c['flare_peak'] for c in hb), default=None), flare_in_1_3=sum(1 <= c['flare_peak'] <= 3 for c in hb),
           flare_f8_max=max((c['flare_f8'] for c in hb if not c['crowded']), default=None), flare_f7_median=float(np.median([c['flare_f7'] for c in hb])) if hb else None, flare_gone_by_8=sum(c['flare_f8'] <= 0.2 for c in hb if not c['crowded']), flare_uncrowded=sum(not c['crowded'] for c in hb),
           whole_frozen_pct_60fps=round(frozen60, 2), whole_frozen_pct_30fps=round(frozen30, 2), whole_diff_median=round(float(np.median(wds)), 2),
           whole_diff_in_hold_min=round(float(wds[hero_held].min()), 2) if hero_held.any() else None,
           whole_diff_in_hold_p10=round(float(np.percentile(wds[hero_held], 10)), 2) if hero_held.any() else None, held_frames=int(hero_held.sum()),
           shake_px_max=round(float(sh_max), 2), reaction=rsum,
           attack_starts=len(starts), first_attack_after_start_s=first_gap, max_attack_gap_s=gaps[0][0] if gaps else None, top_gaps=gaps[:5],
           min_warning_lead_s=min(leads) if leads else None,
           enemies_ge5_frac=round(float((n5s >= 5).mean()), 3), enemies_in_frame_median=float(np.median(n5s)),
           hero_margin_ge5_frac=round(float((mg >= 0.05).mean()), 4), hero_margin_min=round(float(mg.min()), 3),
           occluder_max_pct=round(float(oc.max()) * 100, 1), occluder_gt15_frames=int((oc > 0.15).sum()),
           snaps=snaps, warn_frames_frac=round(float(np.mean([p['warn'] > 0 for p in per])), 3),
           variants={k: dict(n=len(x), crop_run_ge3=sum(c['crop_run'] >= 3 for c in x), good_run_ge3=sum(c['good_run'] >= 3 for c in x),
                             crop_diff_mean=round(float(np.mean([np.mean(c['diffs'][:5]) for c in x])), 2), flare_peak_mean=round(float(np.mean([c['flare_peak'] for c in x])), 2),
                             wdiff_mean=round(float(np.mean([np.mean(c['wdiffs'][:5]) for c in x])), 2)) for k, x in vt.items()},
           contact_rows=cres, reaction_rows=rres)
json.dump(res, open(out_json, 'w'), indent=1)

R = res
md = [f'# P5 combat r03: measurements (`measure_r03.py`, {label})', '', '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
      f'Video `{os.path.basename(vid)}` ({NV} frames, 60 fps), analysed at {W}x{H} gray. Sim-to-video lag {L} frames (mean hero-crop diff over held frames {res["lag_calib_mean_hero_diff"]}). '
      f'Measured window: fight start {t0:.2f} s + 0.5 s to the end ({N} frames).', '',
      '## Summary (target tests of round 03)', '', '| test | target | measured |', '|---|---|---|',
      f'| hero blows: victim-crop diff < 1.0 for >= 3 consecutive frames | every blow | {R["crop_run_ge3"]} / {R["hero_blows_measured"]} (median run {R["crop_run_median"]}) |',
      f'| ... and whole-frame diff >= 1.0 in those frames (the critic test) | every blow | **{R["good_run_ge3"]} / {R["hero_blows_measured"]}** (median run {R["good_run_median"]}) |',
      f'| whole-frame diff during the hero hold ({R["held_frames"]} held frames) | >= 1.0 | min {R["whole_diff_in_hold_min"]}, 10th percentile {R["whole_diff_in_hold_p10"]} |',
      f'| whole-frame frozen frames (diff < 0.3) | <= 3 % | **{R["whole_frozen_pct_30fps"]} % at 30 fps**, {R["whole_frozen_pct_60fps"]} % at 60 fps |',
      f'| red-orange flare area, peak over frames 0..6 | 1-3 % of the frame | min {R["flare_peak_min"]}, median {R["flare_peak_median"]}, max {R["flare_peak_max"]} %; {R["flare_in_1_3"]} / {R["hero_blows_measured"]} in 1-3 % |',
      f'| flare gone by frame 8 (of the pixels that show the flare at frame +3, at most 20 % still do at frame +8; frame +7 median {R["flare_f7_median"]}; measured against frame +10 because frame +8 versus the frame before the contact is dominated by moving red things such as the hero suit, the warning markers and aim lines) | every blow | {R["flare_gone_by_8"]} / {R["flare_uncrowded"]} blows without another contact within 9 frames (worst share left at frame 8: {R["flare_f8_max"]}) |',
      f'| camera hit shake | 2-4 px | max applied {R["shake_px_max"]} px (1080p) |',
      f'| victim pushed >= 0.5 m within 0.3 s (3D) | every blow | {rsum["push03_ge_0_5"]} / {rsum["hero_blows"]} (min {rsum["push03_min"]} m) |',
      f'| victim rotates >= 30 deg within 0.3 s | every blow | {rsum["rot03_ge_30"]} / {rsum["rot_measured"]} (min {rsum["rot03_min"]} deg) |',
      f'| heavy / finisher / launcher blows throw the victim >= 2 m (1.0 s) | every non-armoured heavy blow | {rsum["heavy_dmax1_ge_2"]} / {rsum["heavy_blows"]} (min {rsum["heavy_dmax1_min"]} m) |',
      '', '### Other tests (unchanged from r02)', '', '| test | target | measured |', '|---|---|---|',
      f'| longest gap between attack starts | <= 1.0 s | {R["max_attack_gap_s"]} s ({R["attack_starts"]} starts; first {R["first_attack_after_start_s"]} s after fight start) |',
      f'| warning lead before the blow / shot | >= 0.4 s | min {R["min_warning_lead_s"]} s (frames with a visible warning: {R["warn_frames_frac"]*100:.0f} %) |',
      f'| >= 5 standing enemies on screen | >= 80 % of frames | {R["enemies_ge5_frac"]*100:.1f} % (median {R["enemies_in_frame_median"]:.0f}) |',
      f'| hero box >= 5 % from every edge | 100 % of frames | {R["hero_margin_ge5_frac"]*100:.2f} % (min margin {R["hero_margin_min"]*100:.1f} %) |',
      f'| occluder in front of the hero | <= 15 % of frame | max {R["occluder_max_pct"]} % ({R["occluder_gt15_frames"]} frames > 15 %) |',
      f'| snaps (whole-frame diff > 25) | 0 | {len(snaps)} {snaps[:6]} |', '']
if res['variants']:
    md += ['## Experiment variants (`-WHCmbSweep=1`)', '', '| variant (px / Hz / flare K in the event log) | blows | crop_run>=3 | good_run>=3 | mean crop diff (5 frames) | mean whole diff (5 frames) | mean flare peak % |', '|---|---|---|---|---|---|---|']
    for k, x in sorted(res['variants'].items()): md.append(f'| {k} | {x["n"]} | {x["crop_run_ge3"]} | {x["good_run_ge3"]} | {x["crop_diff_mean"]} | {x["wdiff_mean"]} | {x["flare_peak_mean"]} |')
    md.append('')
md += ['## Per contact', '', 'Victim-crop diff and whole-frame diff for the 8 frames after the contact frame (each vs the previous frame); flare = red-orange area % of the frame at frames 0..9 '
       'after the contact frame.', '', '| rt s | contact | video frame | crop diffs | whole diffs | crop run | good run | flare % f0..f9 | variant |', '|---|---|---|---|---|---|---|---|---|']
for c in cres:
    if 'crop_run' not in c: md.append(f'| {c["rt"]} | {c["label"]} | - | {c["note"]} | | | | | |'); continue
    md.append(f'| {c["rt"]} | {c["label"]} | {c["frame"]} | {" ".join(str(x) for x in c["diffs"])} | {" ".join(f"{x:.1f}" for x in c["wdiffs"])} | {c["crop_run"]} | {c["good_run"]} | {" ".join(str(x) for x in c["flare"])} | {c["variant"] or ""} |')
md += ['', '## Reaction per hero blow (sim record; `react_metrics.py`)', '', '| rt s | kind | victim | push 0.3 s (m) | rotation 0.3 s (deg) | furthest in 1 s (m) | note |', '|---|---|---|---|---|---|---|']
for r_ in rres:
    md.append(f'| {r_["rt"]} | {r_["kind"]} | {r_["victim"]} | {r_["push03"]} | {r_["rot03"]} | {r_["dmax1"]} | {"ARMORED" if r_["armored"] else "heavy" if r_["heavy"] else ""} |')
open(out_md, 'w').write('\n'.join(md) + '\n')
print(json.dumps({k: v for k, v in res.items() if k not in ('contact_rows', 'reaction_rows', 'variants')}, indent=1))
if res['variants']: print(json.dumps(res['variants'], indent=1))

def strip(vstart, n, out):
    """tile n frames (480x270 each, 5 per row) starting at video frame vstart"""
    sel = '+'.join(f'eq(n\\,{vstart + i})' for i in range(n))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-vf', f"select='{sel}',scale=480:270,tile=5x{(n + 4) // 5}", '-frames:v', '1', '-q:v', '2', out], check=True)
if strips:
    os.makedirs(strips, exist_ok=True)
    seen = set(); k = 0
    for c in okc:
        if not c['hero_blow']: continue
        key = c['label'].split()[-1]
        if key in seen or k >= 8: continue
        seen.add(key); k += 1
        strip(c['frame'] - 1, 10, os.path.join(strips, f'hit_{c["rt"]:06.2f}_{key}.jpg'))
    print('strips ->', strips)

if sheet:  # box overlay check: 6 frames with the logged boxes drawn (validates the projection + lag)
    import tempfile
    tmp = tempfile.mkdtemp()
    picks = [per[int(i)] for i in np.linspace(0, N - 1, 6)]
    files = []
    for k, pk in enumerate(picks):
        v = pk['v']; r = byf[f_of(v)]
        fn = os.path.join(tmp, f'b{k}.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-vf', f'select=eq(n\\,{v}),scale=640:360', '-frames:v', '1', fn], check=True)
        dr = []
        def add(b, col):
            x0, y0, x1, y1 = [max(0, min(1, q)) for q in b]
            dr.append(f"drawbox=x={int(x0*640)}:y={int(y0*360)}:w={max(1,int((x1-x0)*640))}:h={max(1,int((y1-y0)*360))}:color={col}:t=2")
        add(r['hero'][3:7], 'cyan')
        for e in r['e']:
            if e[6] > -0.5 and e[12]: add(e[6:10], 'yellow' if e[2] in STAND else 'gray')
        fo = os.path.join(tmp, f'o{k}.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', fn, '-vf', ','.join(dr) + f",drawtext=text='v{v} rt {r['rt']:.2f}':x=8:y=8:fontcolor=white:fontsize=18", fo], check=True)
        files.append(fo)
    fargs = []
    for fo in files: fargs += ['-i', fo]
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + fargs + ['-filter_complex', '[0][1][2]hstack=3[a];[3][4][5]hstack=3[b];[a][b]vstack', '-q:v', '3', sheet], check=True)
    print('sheet', sheet)
