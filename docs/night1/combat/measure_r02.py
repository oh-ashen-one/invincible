#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat round 02: pixel + telemetry measurements of a recorded fight (run_fight.sh movie output dir).
#   measure_r02.py <movie_out_dir> <out.md> <out.json> [--sheet <boxes.jpg>]
# Inputs in <movie_out_dir>: fight.mp4 (1080p60, -dumpmovie fixed step), fight_frames.jsonl (per frame: camera + every character's
# screen box from all skeleton bones, computed in C++ with the frame's final camera), fight_events.jsonl.
# Frame alignment: the movie lags the simulation by the render pipeline. The offset L (video index v <-> sim frame f = v + 1 - L) is
# calibrated from the hit-stop freezes: frozen sim frames must show near-zero whole-frame change.
# Metrics (critic r01 tests):
#   contacts  : victim-crop mean abs diff (gray, 480x270) per frame after each contact; frames < 1.0 in a row (target >= 3);
#               flinch = victim-crop change INTO the contact frame; push = victim feet displacement 0.5 s after; spark = share of
#               the frame that turned near-white (+45 levels, > 200) in the contact frame, and still near-white 6 frames later.
#   attacks   : attack starts = 'threat' events (melee / brute wind-up, gun aim); longest gap (target <= 1.0 s); min warning lead.
#   enemies   : standing enemies whose box is on screen (centre inside, clipped height >= 5 % of frame height); share of frames >= 5.
#   hero      : min margin of the hero box to any frame edge; share of frames >= 5 %.
#   occluders : enemies nearer the lens than the hero, overlapping the hero box: largest clipped area share (target <= 15 %).
#   snaps     : whole-frame diff > 25 (critic r01 found one at 25.8).
import json, subprocess, sys, os
import numpy as np

d, out_md, out_json = sys.argv[1:4]
sheet = sys.argv[sys.argv.index('--sheet') + 1] if '--sheet' in sys.argv else None
W, H = 480, 270
vid = os.path.join(d, 'fight.mp4')
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', vid, '-vf', f'scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
fr = []
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    fr.append(np.frombuffer(b, np.uint8).reshape(H, W))
V = np.array(fr).astype(np.int16)
NV = len(V)
wd = np.zeros(NV); wd[1:] = np.abs(np.diff(V, axis=0)).mean(axis=(1, 2))
rows = [json.loads(l) for l in open(os.path.join(d, 'fight_frames.jsonl')) if l.strip()]
byf = {r['f']: r for r in rows}
ev = [json.loads(l) for l in open(os.path.join(d, 'fight_events.jsonl')) if l.strip()]
rt2f = sorted((r['rt'], r['f']) for r in rows)
def frame_at(rt):
    best = min(rt2f, key=lambda x: abs(x[0] - rt)); return best[1]

# ---- lag calibration
frz = [r['f'] + 1 for r in rows if r['frz']]   # frz is logged on the frame that requests the freeze: the next frames are frozen
best = None
for L in range(0, 6):
    vs = [f - 1 + L for f in frz if 1 <= f - 1 + L < NV]
    if not vs: continue
    m = float(np.mean(wd[vs]))
    if best is None or m < best[1]: best = (L, m)
L = best[0]
def v_of(f): return f - 1 + L
def f_of(v): return v + 1 - L

def crop_box(r, tag, pad=0.25):
    if tag == 'hero': b = r['hero'][3:7]
    else:
        e = [x for x in r['e'] if x[0] == tag]
        if not e: return None
        b = e[0][6:10]
    if b[0] < -0.5: return None
    x0, y0, x1, y1 = b; w, h = x1 - x0, y1 - y0
    x0 -= w * pad; x1 += w * pad; y0 -= h * pad; y1 += h * pad
    X0, X1 = int(max(0, x0 * W)), int(min(W, x1 * W)); Y0, Y1 = int(max(0, y0 * H)), int(min(H, y1 * H))
    if X1 - X0 < 12 or Y1 - Y0 < 12: return None
    return X0, Y0, X1, Y1

def epos(r, tag):
    if tag == 'hero': return np.array(r['hero'][0:3])
    e = [x for x in r['e'] if x[0] == tag]
    return np.array(e[0][3:6]) if e else None

# ---- contacts
contacts = []
for e in ev:
    s = e['ev']
    if s.startswith('hit ') and '->' in s:
        vt = s.split('->')[1].split()[0]; kind = s.split()[1]
        contacts.append((e['rt'], vt, 'hero->' + vt + ' ' + kind))
    elif s.startswith('hero hit by'):
        contacts.append((e['rt'], 'hero', s.split(' dmg')[0].replace('hero hit by ', '') + ' ->hero'))
cres = []
for rt, tag, label in contacts:
    fc = frame_at(rt); vc0 = v_of(fc)
    if vc0 + 12 >= NV or vc0 < 3 or fc not in byf: continue
    r = byf[fc]; cb = crop_box(r, tag)
    if not cb: cres.append(dict(rt=rt, label=label, note='victim off screen')); continue
    X0, Y0, X1, Y1 = cb
    cdiff = lambda v: float(np.abs(V[v, Y0:Y1, X0:X1] - V[v - 1, Y0:Y1, X0:X1]).mean())
    # the contact frame = the frame (within -1 .. +3 of the calibrated one) where the victim crop changes most: the flinch appears there
    vc = max(range(vc0 - 1, vc0 + 4), key=cdiff)
    seq = [cdiff(v) for v in range(vc + 1, vc + 9)]
    run = 0; best_run = 0
    for x in seq[:6]:
        run = run + 1 if x < 1.0 else 0; best_run = max(best_run, run)
    flinch = cdiff(vc)
    p0 = epos(r, tag); f5 = fc + 30
    push = float(np.linalg.norm(epos(byf[f5], tag) - p0)) if f5 in byf and p0 is not None and epos(byf[f5], tag) is not None else None   # 3D: a launched victim rises
    newwhite = lambda v: float(((V[v] - V[vc - 1] > 45) & (V[v] > 200)).mean())
    cres.append(dict(rt=round(rt, 3), label=label, frame=vc, crop=[X0, Y0, X1, Y1], diffs=[round(x, 2) for x in seq], frozen_run=best_run,
                     flinch_diff=round(flinch, 2), push_m=None if push is None else round(push, 2),
                     spark_area=round(newwhite(vc) * 100, 2), spark_area_f6=round(newwhite(min(NV - 1, vc + 6)) * 100, 2)))
okc = [c for c in cres if 'frozen_run' in c]

# ---- attacks
t0 = next((e['rt'] for e in ev if e['ev'].startswith('fight start')), 0)
starts = [e['rt'] for e in ev if e['ev'].startswith('threat ')]
leads = [float(e['ev'].split('lead ')[1]) for e in ev if e['ev'].startswith('threat ')]
gaps = sorted([(round(b - a, 3), round(a, 2)) for a, b in zip(starts, starts[1:])], reverse=True)
first_gap = round(starts[0] - t0, 3) if starts else None

# ---- per frame: enemies in frame, hero margin, occluders
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
    hb = r['hero'][3:7]
    margin = min(hb[0], hb[1], 1 - hb[2], 1 - hb[3]) if hb[0] > -0.5 else -1
    n5 = 0; occ = 0.0; nwarn = 0
    for e in r['e']:
        tag, typ, st, x, y, z, bx0, by0, bx1, by1, dist, warn, alive = e
        if bx0 < -0.5: continue
        cw, ch = clipped([bx0, by0, bx1, by1])
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if alive and st in STAND and 0 <= cx <= 1 and 0 <= cy <= 1 and ch >= 0.05: n5 += 1
        if warn and 0 <= cx <= 1 and 0 <= cy <= 1: nwarn += 1
        if dist < r['hero'][7] - 0.3:
            ox = max(0, min(bx1, hb[2]) - max(bx0, hb[0])); oy = max(0, min(by1, hb[3]) - max(by0, hb[1]))
            if ox > 0 and oy > 0: occ = max(occ, cw * ch)
    per.append(dict(v=v, rt=r['rt'], n5=n5, margin=margin, occ=occ, warn=nwarn, cine=r.get('cine', 0), wd=float(wd[v])))
N = len(per)
n5s = np.array([p['n5'] for p in per]); mg = np.array([p['margin'] for p in per]); oc = np.array([p['occ'] for p in per])
wds = np.array([p['wd'] for p in per])
snaps = [(round(p['rt'], 2), round(p['wd'], 1)) for p in per if p['wd'] > 25]
res = dict(lag_frames=L, lag_calib_mean_diff=round(best[1], 3), frames_measured=N, fight_start_rt=t0,
           contacts=len(okc), contacts_frozen_ge3=sum(c['frozen_run'] >= 3 for c in okc),
           contacts_push_ge_0_3=sum((c['push_m'] or 0) >= 0.3 for c in okc if c['label'].startswith('hero->')),
           hero_contacts=sum(c['label'].startswith('hero->') for c in okc),
           spark_area_max_pct=max((c['spark_area'] for c in okc), default=None), spark_area_f6_max_pct=max((c['spark_area_f6'] for c in okc), default=None),
           attack_starts=len(starts), first_attack_after_start_s=first_gap, max_attack_gap_s=gaps[0][0] if gaps else None, top_gaps=gaps[:5],
           min_warning_lead_s=min(leads) if leads else None,
           enemies_ge5_frac=round(float((n5s >= 5).mean()), 3), enemies_in_frame_median=float(np.median(n5s)),
           hero_margin_ge5_frac=round(float((mg >= 0.05).mean()), 4), hero_margin_min=round(float(mg.min()), 3),
           occluder_max_pct=round(float(oc.max()) * 100, 1), occluder_gt15_frames=int((oc > 0.15).sum()),
           snaps=snaps, whole_diff_median=round(float(np.median(wds)), 2), warn_frames_frac=round(float(np.mean([p['warn'] > 0 for p in per])), 3),
           contact_rows=cres)
json.dump(res, open(out_json, 'w'), indent=1)

md = ['# P5 combat r02: measurements (`measure_r02.py`)', '',
      '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
      f'Video `fight.mp4` ({NV} frames, 1080p60 fixed step), analysed at {W}x{H} gray. Sim-to-video lag: **{L} frames** '
      f'(calibrated: mean whole-frame diff over frozen sim frames {best[1]:.2f}). Measured window: fight start {t0:.2f} s + 0.5 s to the end ({N} frames).', '',
      '## Summary', '', '| test (critic r01) | target | measured |', '|---|---|---|',
      f'| contacts with victim-crop diff < 1.0 for >= 3 frames | every contact | {res["contacts_frozen_ge3"]} / {res["contacts"]} |',
      f'| hero blows: victim root displaced >= 0.3 m (3D) within 0.5 s | every contact | {res["contacts_push_ge_0_3"]} / {res["hero_contacts"]} |',
      f'| spark: new near-white area in the contact frame | <= 3 % | max {res["spark_area_max_pct"]} % |',
      f'| spark: still near-white 6 frames later | ~0 | max {res["spark_area_f6_max_pct"]} % |',
      f'| longest gap between attack starts | <= 1.0 s | {res["max_attack_gap_s"]} s ({res["attack_starts"]} starts; first {res["first_attack_after_start_s"]} s after fight start) |',
      f'| warning lead before the blow / shot | >= 0.4 s | min {res["min_warning_lead_s"]} s (frames with a visible warning: {res["warn_frames_frac"]*100:.0f} %) |',
      f'| >= 5 standing enemies on screen (>= 5 % frame height) | >= 80 % of frames | {res["enemies_ge5_frac"]*100:.1f} % (median {res["enemies_in_frame_median"]:.0f}) |',
      f'| hero box >= 5 % from every edge | 100 % of frames | {res["hero_margin_ge5_frac"]*100:.2f} % (min margin {res["hero_margin_min"]*100:.1f} %) |',
      f'| occluder in front of the hero | <= 15 % of frame | max {res["occluder_max_pct"]} % ({res["occluder_gt15_frames"]} frames > 15 %) |',
      f'| snaps (whole-frame diff > 25) | 0 | {len(snaps)} {snaps[:6]} |', '',
      'Top attack-start gaps (gap s, at rt s): ' + ', '.join(f'{g} @ {a}' for g, a in gaps[:5]), '',
      '## Per contact', '', 'Victim-crop diff for the 8 frames after the contact frame (each vs the previous frame). Frozen run = longest run < 1.0. '
      'Flinch = crop change into the contact frame. Push = victim feet displacement after 0.5 s (real).', '',
      '| rt s | contact | video frame | diffs after contact | frozen run | flinch | push m | spark % | spark % @+6 |', '|---|---|---|---|---|---|---|---|---|']
for c in cres:
    if 'frozen_run' not in c: md.append(f'| {c["rt"]} | {c["label"]} | - | {c["note"]} | | | | | |'); continue
    md.append(f'| {c["rt"]} | {c["label"]} | {c["frame"]} | {" ".join(str(x) for x in c["diffs"])} | {c["frozen_run"]} | {c["flinch_diff"]} | {c["push_m"]} | {c["spark_area"]} | {c["spark_area_f6"]} |')
open(out_md, 'w').write('\n'.join(md) + '\n')
print(json.dumps({k: v for k, v in res.items() if k != 'contact_rows'}, indent=1))

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
    args = []
    for fo in files: args += ['-i', fo]
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args + ['-filter_complex', '[0][1][2]hstack=3[a];[3][4][5]hstack=3[b];[a][b]vstack', '-q:v', '3', sheet], check=True)
    print('sheet', sheet)
