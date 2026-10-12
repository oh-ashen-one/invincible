#!/usr/bin/env python3
"""Round 09: measure the scripted fight from the bone log of the REAL game run (-WHBoneLog, written by the capture director) and the clip.

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

  python3 tools/ue_char/fight/fight_check.py <fight_bones.csv> <out.json> [--t0 8 --t1 16] [--script tools/ue_char/fight/fight_script.json] [--video clip.mp4 --video-t0 8.05]

Per walker and per 1 s window it reads the bone positions (pelvis, spine2, head, hands, feet; cm, world) and reports
  * activity: the fastest of head / hands / feet (cm/s) and the actor's own travel speed; 'active' = any bone > ACTIVE_CMS or travel > 20 cm/s;
    guard idle breathing stays below ~25 cm/s (measured on the first second of the run, before anyone moves);
  * knockdown: spine2 height < DOWN_CM and pelvis < DOWN_CM + 15 (torso on the ground); the longest run per walker;
  * reactions: for every scripted reaction beat (fight:hit*, hero:hitReact on an enemy, fight:down) the peak displacement of spine2 / head within
    0.7 s of the beat start relative to its position at the start (cm) and whether it exceeds REACT_CM (a visible reaction);
  * idle windows: every 1 s window (start step 0.1 s) in [t0, t1] where ALL walkers are inactive (must be 0).
If --video is given: per 1 s window the mean absolute frame difference (% of pixels with |delta| > 12 / 255 on the luma), for comparison with round 08's 1.2 - 2.0 %.
"""
import sys, os, json, csv, math
import numpy as np

ACTIVE_CMS = 60.0      # a bone moving faster than this (cm/s, 1 s window maximum of the 0.1 s speed) is 'active'
DOWN_CM = 45.0         # spine2 below this height = torso on the ground
REACT_CM = 12.0        # spine2 displacement within 0.7 s that counts as a visible reaction


def load(path):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            k = (r['label'], r['bone'])
            rows.setdefault(k, []).append((float(r['time']), float(r['bx']), float(r['by']), float(r['bz']), float(r['x']), float(r['y']), float(r['yaw'])))
    out = {}
    for (lbl, bone), v in rows.items():
        a = np.array(sorted(v)); out.setdefault(lbl, {})[bone] = a
    return out


def speeds(a, dt=0.1):
    """Speed (cm/s) of a bone track at every sample, over a +-dt/2 baseline."""
    t = a[:, 0]; p = a[:, 1:4]
    i0 = np.searchsorted(t, t - dt / 2); i1 = np.minimum(np.searchsorted(t, t + dt / 2), len(t) - 1)
    i0 = np.clip(i0, 0, len(t) - 1)
    d = np.linalg.norm(p[i1] - p[i0], axis=1) / np.maximum(1e-6, t[i1] - t[i0])
    return d


def main():
    a = sys.argv[1:]
    src, out = a[0], a[1]
    t0 = float(a[a.index('--t0') + 1]) if '--t0' in a else 8.0
    t1 = float(a[a.index('--t1') + 1]) if '--t1' in a else 16.0
    D = load(src)
    res = {'source': src, 'window': [t0, t1], 'walkers': {}}
    times = None
    act = {}
    for lbl, bones in D.items():
        t = bones['hips'][:, 0]; times = t
        sp = {b: speeds(bones[b]) for b in ('head', 'hand.L', 'hand.R', 'foot.L', 'foot.R', 'hips')}
        trav = speeds(np.column_stack([t, bones['hips'][:, 4], bones['hips'][:, 5], np.zeros_like(t)]))   # the actor origin's ground speed
        fast = np.max(np.stack([sp['head'], sp['hand.L'], sp['hand.R'], sp['foot.L'], sp['foot.R']]), axis=0)
        active = (fast > ACTIVE_CMS) | (trav > 20.0)
        act[lbl] = (t, active, fast, trav)
        sz = bones['spine2'][:, 3]; hz = bones['hips'][:, 3]
        down = (sz < DOWN_CM) & (hz < DOWN_CM + 15)
        runs = []; s = None
        for i, dflag in enumerate(down):
            if dflag and s is None: s = t[i]
            if (not dflag or i == len(down) - 1) and s is not None:
                runs.append((round(float(s), 3), round(float(t[i]), 3))); s = None
        baseline = float(np.percentile(fast[(t > 0.15) & (t < 1.0)], 95)) if ((t > 0.15) & (t < 1.0)).any() else None
        res['walkers'][lbl] = {'knockdown_runs_s': runs, 'longest_knockdown_s': round(max([b - a_ for a_, b in runs], default=0.0), 3),
                               'guard_baseline_cms_p95_first_second': None if baseline is None else round(baseline, 1),
                               'peak_bone_cms': round(float(fast.max()), 1), 'active_fraction_window': round(float(active[(t >= t0) & (t < t1)].mean()), 3)}
    # idle windows: all walkers inactive during a whole 1 s window?
    starts = np.arange(t0, t1 - 1.0 + 1e-6, 0.1)
    idle_windows = []; min_active = 99; per_window = []
    for s0 in starts:
        n = 0
        for lbl, (t, active, fast, trav) in act.items():
            m = (t >= s0) & (t < s0 + 1.0)
            if m.any() and active[m].mean() > 0.15: n += 1
        per_window.append((round(float(s0), 2), n))
        min_active = min(min_active, n)
        if n == 0: idle_windows.append(round(float(s0), 2))
    res['idle_windows_all_walkers_inactive'] = idle_windows
    res['min_walkers_active_in_any_1s_window'] = int(min_active)
    res['active_walkers_per_window_start'] = per_window[::5]
    # reactions from the script
    sc = json.load(open(a[a.index('--script') + 1] if '--script' in a else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fight_script.json')))
    reacts = []
    for lbl, d in sc['actors'].items():
        if lbl == 'Fight_Hero' or lbl not in D: continue
        b = D[lbl]; t = b['spine2'][:, 0]
        for bt in d['beats']:
            if not (bt['clip'].startswith('fight:hit') or bt['clip'] == 'hero:hitReact' or bt['clip'] == 'fight:down'): continue
            m = (t >= bt['start']) & (t <= bt['start'] + 0.7)
            if not m.any(): continue
            p = b['spine2'][m][:, 1:4]; h = b['head'][m][:, 1:4]
            ds = float(np.linalg.norm(p - p[0], axis=1).max()); dh = float(np.linalg.norm(h - h[0], axis=1).max())
            reacts.append({'walker': lbl, 'clip': bt['clip'], 'start': bt['start'], 'spine2_peak_cm': round(ds, 1), 'head_peak_cm': round(dh, 1), 'visible': bool(max(ds, dh) > REACT_CM),
                           'in_window': bool(t0 <= bt['start'] < t1)})
    res['reactions'] = reacts
    w = [r for r in reacts if r['in_window']]
    res['window_summary'] = {'reactions': len(w), 'visible': sum(r['visible'] for r in w), 'distinct_clips': sorted(set(r['clip'] for r in w if r['visible'])),
                             'knockdowns_ge_1s_in_window': [(l, r) for l, v in res['walkers'].items() for r in v['knockdown_runs_s'] if min(r[1], t1) - max(r[0], t0) >= 1.0]}
    # optional video check
    if '--video' in a:
        import subprocess
        vid = a[a.index('--video') + 1]; vt0 = float(a[a.index('--video-t0') + 1]) if '--video-t0' in a else 0.0
        raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', vid, '-vf', 'scale=480:270,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, 270, 480).astype(np.int16)
        diff = (np.abs(np.diff(fr, axis=0)) > 12).mean(axis=(1, 2)) * 100
        fps = 60.0
        vw = [(round(vt0 + i / fps, 2), round(float(diff[i:i + 60].mean()), 2)) for i in range(0, len(diff) - 59, 30)]
        res['video_frame_diff_pct_per_1s_window'] = vw
        res['video_frame_diff_pct_min_window'] = min(v for _, v in vw) if vw else None
    # optional pixel check per walker: project the bone log into the clip's camera and measure the frame difference inside each walker's box, per 1 s window
    if '--video' in a and '--cam' in a:
        cx, cy, cz, ax, ay, az_, fov = [float(x) for x in a[a.index('--cam') + 1].split(',')]
        cam = np.array([cx, cy, cz]); fw = np.array([ax, ay, az_]) - cam; fw /= np.linalg.norm(fw)
        rt = np.cross([0, 0, 1.0], fw); rt /= np.linalg.norm(rt); up_ = np.cross(fw, rt)
        tf = math.tan(math.radians(fov) / 2); VW, VH = 480, 270
        def proj(p):
            v = p - cam; z = v @ fw
            return (VW / 2 + (VW / 2) * (v @ rt) / (z * tf), VH / 2 - (VW / 2) * (v @ up_) / (z * tf))
        t_vid = vt0 + np.arange(len(diff) + 1) / fps
        per = {}
        d_full = np.abs(np.diff(fr, axis=0)) > 12       # (n-1, 270, 480)
        for lbl, bones in D.items():
            ts_ = bones['hips'][:, 0]; rows_ = []
            for s0 in np.arange(max(t0, vt0), min(t1, vt0 + len(diff) / fps) - 1.0 + 1e-6, 0.5):
                i0 = int((s0 - vt0) * fps); i1 = i0 + 60
                pts = []
                for b in ('hips', 'spine2', 'head', 'hand.L', 'hand.R', 'foot.L', 'foot.R'):
                    k = int(np.argmin(np.abs(bones[b][:, 0] - (s0 + 0.5)))); pts.append(proj(bones[b][k, 1:4]))
                pts = np.array(pts); x0_, x1_ = int(max(0, pts[:, 0].min() - 12)), int(min(VW, pts[:, 0].max() + 12)); y0_, y1_ = int(max(0, pts[:, 1].min() - 12)), int(min(VH, pts[:, 1].max() + 12))
                if x1_ - x0_ < 4 or y1_ - y0_ < 4: rows_.append((round(float(s0), 2), None)); continue
                rows_.append((round(float(s0), 2), round(float(d_full[i0:i1, y0_:y1_, x0_:x1_].mean() * 100), 2)))
            per[lbl] = rows_
        res['video_box_frame_diff_pct'] = per
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('idle_windows_all_walkers_inactive', 'min_walkers_active_in_any_1s_window', 'window_summary')}, indent=1))
    for lbl, v in res['walkers'].items():
        print('%-14s knockdown runs %s   longest %.2f s   baseline %s cm/s   peak %s cm/s' % (lbl, v['knockdown_runs_s'], v['longest_knockdown_s'], v['guard_baseline_cms_p95_first_second'], v['peak_bone_cms']))


if __name__ == '__main__':
    main()
