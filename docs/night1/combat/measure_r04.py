#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat round 04: the round target (critic r03 "biggest gap"), measured on pixels + the sim record.
#   measure_r04.py <A_dir> <A_measure_r03.json> <out.md> <out.json> [--noflare <B_dir>] [--video <A.mp4>] [--strips <dir>] [--w 960]
#   measure_r04.py --selftest
# A_dir  = run_fight.sh movie output with the starburst on (fight.mp4 master, fight_frames.jsonl, fight_events.jsonl)
# B_dir  = the SAME frozen fight rendered with -WHCmbFlare=0 (no starburst). The sim, the camera, the hit shake and every other effect are identical (the
#          flare has its own RNG stream), so |A - B| per frame is EXACTLY the flare: no guessing from colours and no confusion with moving bodies.
# A_measure_r03.json = measure_r03.py output for the same A master (trim 0): it supplies the lag calibration and the calibrated contact frame of every blow.
# Per contact (frames v = contact .. contact + 7, decoded at --w x --w*9/16, default 960x540):
#   flare mask     |A - B| > 28 (max channel) inside a window around the flare (without --noflare: red-orange pixels against the frame before the contact)
#   streaks        angular runs of the mask in the annulus [0.35 Rb, Rb] (Rb = furthest mask pixel from the mask centroid); target 4-8
#   streak length  tip radius (share of the frame width) and tip radius minus the core radius; target >= 8 % of the frame width
#   fill           mask area / (pi Rb^2); target <= 35 %
#   retention      Sobel energy of the victim box (tight box + 10 %) in contact frames 1..5 / the same box in the frame before the contact ("critic" ratio) and
#                  / the same frame of the no-flare run (pure flare effect); target >= 0.60
#   reaction       react_metrics.py numbers from the sim record: push03 >= 0.5 m OR turn03 (yaw or tilt) >= 30 deg within 0.3 s (CB2)
import json, math, os, subprocess, sys, gzip
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import react_metrics as RM


# ------------------------------------------------------------------------------------------------ analysis primitives
def flare_mask_diff(a, b, thr=28):
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    return d


def clean(mask):
    m = mask.astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return m.astype(bool)


def isolate(mask, win_frac=0.22):
    """keep the mask pixels within win_frac x frame width of the strongest blob (the flare), drop specks elsewhere"""
    H, W = mask.shape
    if mask.sum() < 20: return mask
    blur = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 6)
    cy, cx = np.unravel_index(int(blur.argmax()), blur.shape)
    yy, xx = np.ogrid[:H, :W]
    win = (xx - cx) ** 2 + (yy - cy) ** 2 <= (win_frac * W) ** 2
    return mask & win


def shape(mask, W):
    """streak count, tip / length shares of the frame width, fill of the bounding circle, for one flare mask (bool image, width W)"""
    ys, xs = np.nonzero(mask)
    if len(xs) < 30: return None
    cx, cy = xs.mean(), ys.mean()
    r = np.hypot(xs - cx, ys - cy); ang = np.arctan2(ys - cy, xs - cx)
    Rb = float(r.max())
    fill = float(len(xs)) / (math.pi * Rb * Rb)
    nb = 180
    sel = r >= 0.35 * Rb
    hist, _ = np.histogram(ang[sel], bins=nb, range=(-math.pi, math.pi))
    occ = hist > 0
    # circular closing of 1-bin gaps, then runs
    occ2 = occ.copy()
    for i in range(nb):
        if not occ[i] and occ[i - 1] and occ[(i + 1) % nb]: occ2[i] = True
    runs = []
    if occ2.all():
        runs = [(0, nb)]
    else:
        start = int(np.argmin(occ2))   # a False bin: walk from there
        i = 0
        cur = None
        for k in range(nb):
            b = (start + k) % nb
            if occ2[b]:
                if cur is None: cur = [b, 1]
                else: cur[1] += 1
            else:
                if cur is not None: runs.append(tuple(cur)); cur = None
        if cur is not None: runs.append(tuple(cur))
    streaks = []
    for b0, n in runs:
        bins = [(b0 + k) % nb for k in range(n)]
        cnt = int(sum(hist[b] for b in bins))
        if cnt < 6: continue
        lo = -math.pi + b0 * 2 * math.pi / nb - 0.03; span = n * 2 * math.pi / nb + 0.06
        rel = (ang - lo) % (2 * math.pi)
        inrun = (rel <= span) & sel
        tip = float(r[inrun].max()) if inrun.any() else 0.0
        streaks.append(dict(bin0=b0, nbins=n, count=cnt, tip=tip, centre=lo + span / 2, lo=lo, span=span))
    # core radius: furthest pixel outside every streak sector
    inany = np.zeros(len(xs), bool)
    for s in streaks:
        inany |= ((ang - s['lo']) % (2 * math.pi)) <= s['span']
    rc = float(r[~inany].max()) if (~inany).any() else 0.0
    rc = max(rc, 0.0)
    tips = [s['tip'] for s in streaks]
    lens = []   # per streak: tip radius minus the radius where its own pixels start beyond the core (a hollow centre leaves a gap between core and streak)
    for s in streaks:
        insec = ((ang - s['lo']) % (2 * math.pi)) <= s['span']
        beyond = r[insec & (r > rc + 2)]
        r_in = float(beyond.min()) if len(beyond) else rc
        lens.append(s['tip'] - r_in)
    return dict(n_streaks=len(streaks), Rb_px=Rb, Rb_share=Rb / W, fill=fill, area_px=int(len(xs)), area_share=len(xs) / (W * W * 9 / 16),
                core_r_px=rc, tip_share_min=min(tips) / W if tips else 0.0, tip_share_max=max(tips) / W if tips else 0.0,
                len_share_min=min(lens) / W if lens else 0.0, centre=(float(cx), float(cy)))


def sobel_map(gray, box):
    x0, y0, x1, y1 = box
    g = gray[y0:y1, x0:x1].astype(np.float32)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    return np.hypot(gx, gy)


def sobel_energy(gray, box):
    """total Sobel edge energy in the box (what a plain critic test computes; NOTE a hard-edged overlay can raise it)"""
    x0, y0, x1, y1 = box
    if (x1 - x0) * (y1 - y0) < 100: return 0.0
    return float(sobel_map(gray, box).sum())


def retained(gray_a, gray_ref, box):
    """share of the reference edges that survive in A: sum(min(SA, SRef)) / sum(SRef): an overlay can only lower it (never inflated by new edges)"""
    sa, sr = sobel_map(gray_a, box), sobel_map(gray_ref, box)
    t = float(sr.sum())
    return float(np.minimum(sa, sr).sum()) / t if t > 0 else 1.0


def pad_box(b, W, H, pad=0.10):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    X0 = int(max(0, (x0 - w * pad) * W)); X1 = int(min(W, (x1 + w * pad) * W)); Y0 = int(max(0, (y0 - h * pad) * H)); Y1 = int(min(H, (y1 + h * pad) * H))
    return (X0, Y0, X1, Y1) if X1 - X0 >= 12 and Y1 - Y0 >= 12 else None


# ------------------------------------------------------------------------------------------------ self test
def selftest():
    W, H = 960, 540
    rng = np.random.default_rng(3)
    bg = rng.integers(20, 120, (H, W, 3), dtype=np.uint8)
    bg = cv2.GaussianBlur(bg, (0, 0), 3)
    for n in (4, 6, 8):
        a = bg.astype(np.float32).copy()
        cx, cy = 480, 250
        layer = np.zeros((H, W), np.float32)
        Lp = 0.105 * W
        for i in range(n):
            ang = 0.4 + i * 2 * math.pi / n
            for j in range(4):
                w = 0.0095 * W * (1.0, 0.75, 0.52, 0.32)[j]
                r0 = 0.030 * W + Lp * j / 4; r1 = 0.030 * W + Lp * (j + 1) / 4
                p0 = (int(cx + r0 * math.cos(ang)), int(cy + r0 * math.sin(ang))); p1 = (int(cx + r1 * math.cos(ang)), int(cy + r1 * math.sin(ang)))
                cv2.line(layer, p0, p1, 1.0, max(1, int(w)))
        cv2.circle(layer, (cx, cy), int(0.0175 * W), 1.0, -1)
        a += layer[..., None] * np.array([190, 120, 30], np.float32)
        a = np.clip(a, 0, 255).astype(np.uint8)
        m = isolate(clean(flare_mask_diff(a, bg) > 28))
        s = shape(m, W)
        print('selftest streaks planted', n, '->', s['n_streaks'], 'tip %.3f len %.3f fill %.2f' % (s['tip_share_min'], s['len_share_min'], s['fill']))
        assert s['n_streaks'] == n, s
        assert 0.12 < s['tip_share_min'] < 0.16, s
        assert 0.085 < s['len_share_min'] < 0.115, s
        assert s['fill'] < 0.35, s
    # retention of an opaque disc vs streaks over a textured body
    body = bg.copy(); cv2.rectangle(body, (440, 200), (520, 400), (60, 60, 200), -1); body = cv2.GaussianBlur(body, (0, 0), 1)
    box = (440, 200, 520, 400)
    disc = body.copy(); cv2.circle(disc, (480, 280), 90, (30, 170, 250), -1)
    g0 = cv2.cvtColor(body, cv2.COLOR_RGB2GRAY); g1 = cv2.cvtColor(disc, cv2.COLOR_RGB2GRAY)
    print('selftest opaque disc: total energy ratio %.2f (a hard rim inflates it), retained edges %.2f' % (sobel_energy(g1, box) / sobel_energy(g0, box), retained(g1, g0, box)))
    assert retained(g1, g0, box) < 0.6
    lay = body.astype(np.float32); cv2.line(lay, (440, 260), (520, 300), (0, 0, 0), 1)
    stk = np.clip(lay + 0, 0, 255).astype(np.uint8); cv2.line(stk, (400, 280), (560, 280), (250, 200, 60), 5)
    gs = cv2.cvtColor(stk, cv2.COLOR_RGB2GRAY)
    print('selftest one streak across the body: retained edges %.2f' % retained(gs, g0, box))
    assert retained(gs, g0, box) > 0.7
    print('selftest OK')


# ------------------------------------------------------------------------------------------------ main
def grab(video, idxs, W, H):
    idxs = sorted(set(int(i) for i in idxs if i >= 0))
    rng = []   # merged index ranges: one between(n,a,b) term each (a long eq() chain exceeds ffmpeg's expression limits)
    for i in idxs:
        if rng and i == rng[-1][1] + 1: rng[-1][1] = i
        else: rng.append([i, i])
    sel = '+'.join(f'between(n\\,{a}\\,{b})' for a, b in rng)
    cmd = ['ffmpeg', '-v', 'error', '-i', video, '-vf', f"select='{sel}',scale={W}:{H}:flags=area", '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    data = subprocess.run(cmd, capture_output=True).stdout
    n = len(data) // (W * H * 3)
    arr = np.frombuffer(data[:n * W * H * 3], np.uint8).reshape(n, H, W, 3)
    return {i: arr[k] for k, i in enumerate(idxs[:n])}


def load_rows(d):
    p = os.path.join(d, 'fight_frames.jsonl')
    if os.path.exists(p): return [json.loads(l) for l in open(p) if l.strip()]
    return [json.loads(l) for l in gzip.open(p + '.gz', 'rt') if l.strip()]


def main():
    args = sys.argv[1:]
    dA, jA, out_md, out_json = args[0:4]
    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default
    dB = opt('--noflare'); W = int(opt('--w', 960)); H = W * 9 // 16
    vidA = opt('--video', os.path.join(dA, 'fight.mp4')); vidB = os.path.join(dB, 'fight.mp4') if dB else None
    strips = opt('--strips')
    M = json.load(open(jA)); L = M['lag_frames']
    rows = load_rows(dA); byf = {r['f']: r for r in rows}
    ev = [json.loads(l) for l in open(os.path.join(dA, 'fight_events.jsonl')) if l.strip()]
    contacts = [c for c in M['contact_rows'] if 'crop_run' in c]
    K = 10   # frames 0..9 after the contact frame (the fade is checked at frame 8)
    need = set()
    for c in contacts:
        for k in range(-1, K): need.add(c['frame'] + k)
    FA = grab(vidA, need, W, H)
    FB = grab(vidB, need, W, H) if vidB else None
    # reaction from the sim record
    rres = RM.analyse(rows, ev)
    rby = {(r['rt'], r['victim']): r for r in rres}
    out = []
    for c in contacts:
        vc = c['frame']; rt = c['rt']
        tag = c['label'].split('->')[1].split()[0] if c['hero_blow'] else 'hero'
        fc = vc - 1 + 1 - L if False else None
        # sim frame of the contact: nearest frame record to rt
        f = min(byf, key=lambda i: abs(byf[i]['rt'] - rt))
        r = byf[f]
        if tag == 'hero': b = r['hero'][3:7]
        else:
            e = [x for x in r['e'] if x[0] == tag]
            b = e[0][6:10] if e else None
        box = pad_box(b, W, H) if b and b[0] > -0.5 else None
        res = dict(rt=rt, label=c['label'], hero_blow=c['hero_blow'], frame=vc)
        shapes = []; ret_pre = []; ret_ab = []; ret_pre_strict = []; ret_ab_tot = []; cover = []; areas = []
        if all(v in FA for v in range(vc - 1, vc + K)) and (FB is None or all(v in FB for v in range(vc - 1, vc + K))):
            gpre = cv2.cvtColor(FA[vc - 1], cv2.COLOR_RGB2GRAY)
            epre = sobel_energy(gpre, box) if box else None
            for k in range(0, K):
                v = vc + k
                if FB is not None:
                    m = isolate(clean(flare_mask_diff(FA[v], FB[v]) > 28))
                else:  # fallback: red-orange pixels against the frame before the contact
                    dd = FA[v].astype(np.int16) - FA[vc - 1].astype(np.int16)
                    m = isolate(clean((dd[..., 0] >= 45) & (dd[..., 0] - dd[..., 2] >= 35) & (dd[..., 0] >= dd[..., 1])))
                areas.append(round(float(m.sum()) / (W * H) * 100, 3))
                s = shape(m, W) if 1 <= k <= 5 else None
                if s: shapes.append(s)
                if 1 <= k <= 5 and box:
                    ga = cv2.cvtColor(FA[v], cv2.COLOR_RGB2GRAY)
                    ea = sobel_energy(ga, box)
                    if epre: ret_pre.append(ea / epre)
                    ret_pre_strict.append(retained(ga, gpre, box))
                    if FB is not None:
                        gb = cv2.cvtColor(FB[v], cv2.COLOR_RGB2GRAY)
                        ret_ab.append(retained(ga, gb, box)); ret_ab_tot.append(ea / max(1.0, sobel_energy(gb, box)))
                    x0, y0, x1, y1 = box
                    cover.append(float(m[y0:y1, x0:x1].mean()))
            pk = max(areas[1:6]); a15 = areas[1:6]
            res.update(area_pct=areas, static_var=round((max(a15) - min(a15)) / pk, 3) if pk > 0 else None, f8_pct_of_peak=round(areas[8] / pk * 100, 1) if pk > 0 else None,
                       gone_by_8=bool(areas[8] <= max(0.05, 0.2 * pk)))
            if shapes:
                res.update(n_streaks=int(np.median([s['n_streaks'] for s in shapes])), n_streaks_min=min(s['n_streaks'] for s in shapes), n_streaks_max=max(s['n_streaks'] for s in shapes),
                           tip_share_min=round(min(s['tip_share_min'] for s in shapes), 4), len_share_min=round(min(s['len_share_min'] for s in shapes), 4),
                           fill_max=round(max(s['fill'] for s in shapes), 3), fill_median=round(float(np.median([s['fill'] for s in shapes])), 3),
                           Rb_share_median=round(float(np.median([s['Rb_share'] for s in shapes])), 4))
            if ret_pre: res.update(ret_pre_min=round(min(ret_pre), 3), ret_pre_mean=round(float(np.mean(ret_pre)), 3))
            if ret_pre_strict: res.update(ret_pre_strict_min=round(min(ret_pre_strict), 3), ret_pre_strict_mean=round(float(np.mean(ret_pre_strict)), 3))
            if ret_ab: res.update(ret_ab_min=round(min(ret_ab), 3), ret_ab_mean=round(float(np.mean(ret_ab)), 3), ret_ab_tot_min=round(min(ret_ab_tot), 3))
            if cover: res.update(victim_covered_pct=round(max(cover) * 100, 1))
        else:
            res['note'] = 'frames missing'
        rr = rby.get((round(rt, 3), tag))
        if rr: res.update(push03=rr['push03'], rot03=rr['rot03'], tilt03=rr.get('tilt03'), turn03=rr.get('turn03'), dmax1=rr['dmax1'], kind=rr['kind'], armored=rr['armored'])
        out.append(res)
    hb = [o for o in out if o['hero_blow'] and 'n_streaks' in o]
    allc = [o for o in out if 'n_streaks' in o]
    def cnt(lst, fn): return sum(1 for o in lst if fn(o))
    summ = dict(contacts=len(out), hero_blows=len([o for o in out if o['hero_blow']]), flare_measured=len(allc), has_noflare=FB is not None,
                streaks_4_8=cnt(allc, lambda o: 4 <= o['n_streaks_min'] and o['n_streaks_max'] <= 8), streaks_4_8_median=cnt(allc, lambda o: 4 <= o['n_streaks'] <= 8),
                len_ge_8pct=cnt(allc, lambda o: o['len_share_min'] >= 0.08), tip_ge_8pct=cnt(allc, lambda o: o['tip_share_min'] >= 0.08),
                fill_le_35=cnt(allc, lambda o: o['fill_max'] <= 0.35), gone_by_8=cnt(allc, lambda o: o.get('gone_by_8')), static_max=max((o['static_var'] for o in allc if o.get('static_var') is not None), default=None),
                ret_pre_ge_60=cnt([o for o in allc if 'ret_pre_min' in o], lambda o: o['ret_pre_min'] >= 0.6), ret_pre_measured=len([o for o in allc if 'ret_pre_min' in o]),
                ret_pre_ge_60_mean=cnt([o for o in allc if 'ret_pre_mean' in o], lambda o: o['ret_pre_mean'] >= 0.6),
                ret_ab_ge_60=cnt([o for o in allc if 'ret_ab_min' in o], lambda o: o['ret_ab_min'] >= 0.6), ret_ab_measured=len([o for o in allc if 'ret_ab_min' in o]),
                ret_pre_min=min((o['ret_pre_min'] for o in allc if 'ret_pre_min' in o), default=None), ret_ab_min=min((o['ret_ab_min'] for o in allc if 'ret_ab_min' in o), default=None),
                n_streaks_min=min((o['n_streaks_min'] for o in allc), default=None), n_streaks_max=max((o['n_streaks_max'] for o in allc), default=None),
                len_share_min=min((o['len_share_min'] for o in allc), default=None), tip_share_min=min((o['tip_share_min'] for o in allc), default=None),
                fill_max=max((o['fill_max'] for o in allc), default=None),
                area_pct_median=float(np.median([max(o['area_pct'][1:6]) for o in allc])) if allc else None,
                move_or_turn=cnt([o for o in out if o['hero_blow'] and 'push03' in o], lambda o: (o['push03'] or 0) >= 0.5 or (o.get('turn03') or o['rot03'] or 0) >= 30),
                move_or_turn_of=len([o for o in out if o['hero_blow'] and 'push03' in o]),
                push_ge_05=cnt([o for o in out if o['hero_blow'] and 'push03' in o], lambda o: (o['push03'] or 0) >= 0.5),
                turn_ge_30=cnt([o for o in out if o['hero_blow'] and 'push03' in o], lambda o: (o.get('turn03') or o['rot03'] or 0) >= 30),
                tilt_ge_30=cnt([o for o in out if o['hero_blow'] and 'push03' in o], lambda o: (o.get('tilt03') or 0) >= 30),
                turn_min=min((o.get('turn03') or o['rot03'] for o in out if o['hero_blow'] and 'push03' in o and (o.get('turn03') or o['rot03']) is not None), default=None),
                push_min=min((o['push03'] for o in out if o['hero_blow'] and 'push03' in o and o['push03'] is not None), default=None))
    json.dump(dict(summary=summ, contacts=out), open(out_json, 'w'), indent=1)
    md = ['# P5 combat r04: round-target measurements (`measure_r04.py`)', '', '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
          f'A = `{os.path.basename(vidA)}` (starburst on), B = {"`" + os.path.basename(os.path.dirname(vidB)) + "/fight.mp4` (same fight, `-WHCmbFlare=0`): flare mask = |A - B|" if vidB else "none: flare mask = red-orange pixels against the frame before the contact (heuristic)"}. '
          f'Decoded at {W}x{H}; contact frames from `measure_r03.py` (lag {L} frames). {summ["contacts"]} contacts ({summ["hero_blows"]} hero blows, the rest hits on the hero).', '',
          '## Summary', '', '| test | target | measured |', '|---|---|---|',
          f'| starburst: 4-8 radial streaks (frames 1-5, every frame) | 4-8 | {summ["streaks_4_8"]} / {summ["flare_measured"]} contacts (range {summ["n_streaks_min"]}-{summ["n_streaks_max"]}; by median {summ["streaks_4_8_median"]}) |',
          f'| streak length, tip radius minus core radius, share of the frame width | >= 8 % | {summ["len_ge_8pct"]} / {summ["flare_measured"]} (min {summ["len_share_min"]:.3f}); tip radius alone >= 8 %: {summ["tip_ge_8pct"]} / {summ["flare_measured"]} (min {summ["tip_share_min"]:.3f}) |' if summ['flare_measured'] else '| starburst | - | not measured |',
          f'| fill of the bounding circle (max over frames 1-5) | <= 35 % | {summ["fill_le_35"]} / {summ["flare_measured"]} (max {summ["fill_max"]}) |' if summ['flare_measured'] else None,
          f'| flare static through the hold (area spread over frames 1-5) and gone by frame 8 (area <= max(0.05 %, 20 % of the peak)) | static, gone | spread max {summ["static_max"]}; gone by frame 8: {summ["gone_by_8"]} / {summ["flare_measured"]} |' if summ['flare_measured'] else None,
          f'| victim Sobel energy in contact frames 1-5 vs the frame before the contact (every frame) | >= 60 % | {summ["ret_pre_ge_60"]} / {summ["ret_pre_measured"]} (min {summ["ret_pre_min"]}); by 5-frame mean {summ["ret_pre_ge_60_mean"]} / {summ["ret_pre_measured"]} |' if summ['flare_measured'] else None,
          f'| ... edges retained, same frame without the flare: sum(min(SA, SB)) / sum(SB) (pure flare effect, cannot be inflated by the flare edges) | >= 60 % | {summ["ret_ab_ge_60"]} / {summ["ret_ab_measured"]} (min {summ["ret_ab_min"]}) |' if summ['has_noflare'] else None,
          f'| flare share of the frame (peak over frames 1-5, median) | (info) | {summ["area_pct_median"]} % |' if summ['flare_measured'] else None,
          f'| CB2: victim moves >= 0.5 m OR rotates >= 30 deg within 0.3 s (hero blows) | every blow | **{summ["move_or_turn"]} / {summ["move_or_turn_of"]}** (moves >= 0.5 m: {summ["push_ge_05"]}, min {summ["push_min"]} m; turns >= 30 deg: {summ["turn_ge_30"]}, min {summ["turn_min"]} deg; body tilt >= 30 deg: {summ["tilt_ge_30"]}) |',
          '', '## Per contact', '', '| rt s | contact | streaks (min-max) | tip / length min (% W) | fill max | flare % of frame f1..f5 (f8 % of peak) | Sobel vs pre (min / mean) | vs no-flare (min) | victim px covered % | push m | turn deg | tilt deg |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for o in out:
        if 'n_streaks' not in o:
            md.append(f'| {o["rt"]} | {o["label"]} | - | {o.get("note", "no flare measured")} | | | | | | | | |'); continue
        md.append(f'| {o["rt"]} | {o["label"]} | {o["n_streaks_min"]}-{o["n_streaks_max"]} | {o["tip_share_min"]*100:.1f} / {o["len_share_min"]*100:.1f} | {o["fill_max"]*100:.0f} % | {" ".join(str(x) for x in o["area_pct"][1:6])} ({o.get("f8_pct_of_peak", "-")} %) | '
                  f'{o.get("ret_pre_min", "-")} / {o.get("ret_pre_mean", "-")} | {o.get("ret_ab_min", "-")} | {o.get("victim_covered_pct", "-")} | {o.get("push03", "-")} | {o.get("rot03", "-")} | {o.get("tilt03", "-")} |')
    open(out_md, 'w').write('\n'.join(x for x in md if x is not None) + '\n')
    print(json.dumps(summ, indent=1))
    if strips:
        os.makedirs(strips, exist_ok=True)
        # side-by-side strips: A frames contact-1 .. contact+7 (victim box drawn) for up to 8 contacts of different kinds
        seen = set(); n = 0
        for o in out:
            if not o['hero_blow'] or 'n_streaks' not in o: continue
            kind = o['label'].split()[-1]
            if kind in seen or n >= 8: continue
            seen.add(kind); n += 1
            v0 = o['frame'] - 1
            sel = '+'.join(f'eq(n\\,{v0 + i})' for i in range(10))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vidA, '-vf', f"select='{sel}',scale=480:270,tile=5x2", '-frames:v', '1', '-q:v', '2', os.path.join(strips, f'hit_{o["rt"]:06.2f}_{kind}.jpg')], check=True)


if __name__ == '__main__':
    if '--selftest' in sys.argv: selftest()
    else: main()
