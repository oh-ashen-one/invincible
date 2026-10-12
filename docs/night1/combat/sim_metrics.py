#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02 (r03: enemy rows may have 15 fields; frozen_frames = frames the HERO was held): the video-free half of the spec checks, from a run's fight_frames.jsonl + fight_events.jsonl (any run mode, nullrhi included).
#   sim_metrics.py <run_dir> [out.json]
# Screen boxes are computed in C++ by projecting every skeleton bone with the frame's final camera (16:9, horizontal fov), so hero margin,
# enemies in frame and occluders do not need pixels. measure_r02.py adds the pixel tests (hit-stop freeze, spark area, snaps) on the video.
import json, sys, os
import numpy as np
d = sys.argv[1]
rows = [json.loads(l) for l in open(os.path.join(d, 'fight_frames.jsonl')) if l.strip()]
ev = [json.loads(l) for l in open(os.path.join(d, 'fight_events.jsonl')) if l.strip()]
t0 = next((e['rt'] for e in ev if e['ev'].startswith('fight start')), 0)
STAND = {'hold', 'approach', 'attack', 'aim', 'fire', 'stagger', 'getup', 'webbed', 'yanked'}
def clipped(b): return max(0, min(1, b[2]) - max(0, b[0])), max(0, min(1, b[3]) - max(0, b[1]))
per = []
for r in rows:
    if r['rt'] < t0 + 0.5: continue
    hb = r['hero'][3:7]
    margin = min(hb[0], hb[1], 1 - hb[2], 1 - hb[3]) if hb[0] > -0.5 else -1
    n5 = 0; occ = 0.0; nwarn = 0; nbig = 0
    for e in r['e']:
        tag, typ, st, x, y, z, bx0, by0, bx1, by1, dist, warn, alive = e[:13]   # (r03 rows carry two more fields: visual yaw, held)
        if bx0 < -0.5: continue
        cw, ch = clipped([bx0, by0, bx1, by1]); cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if alive and st in STAND and 0 <= cx <= 1 and 0 <= cy <= 1 and ch >= 0.05: n5 += 1
        if alive and st in STAND and ch >= 0.55 and cw * ch >= 0.12: nbig += 1   # a foreground body filling >= 12 % of the frame
        if warn and 0 <= cx <= 1 and 0 <= cy <= 1: nwarn += 1
        if dist < r['hero'][7] - 0.3:
            ox = max(0, min(bx1, hb[2]) - max(bx0, hb[0])); oy = max(0, min(by1, hb[3]) - max(by0, hb[1]))
            if ox > 0 and oy > 0: occ = max(occ, cw * ch)
    cx, cy, cz, cp = r['cam'][0], r['cam'][1], r['cam'][2], r['cam'][3]
    hx, hy, hz = r['hero'][0], r['hero'][1], r['hero'][2] + 0.95
    per.append((r['rt'], n5, margin, occ, nwarn, r['frz'], r.get('cine', 0), ((cx - hx) ** 2 + (cy - hy) ** 2 + (cz - hz) ** 2) ** 0.5, -cp, cz - hz, nbig))
a = np.array(per)
starts = [e['rt'] for e in ev if e['ev'].startswith('threat ')]
gaps = sorted([(round(b - x, 2), round(x, 2)) for x, b in zip(starts, starts[1:])], reverse=True)
out = dict(frames=len(a), enemies_ge5_frac=round(float((a[:, 1] >= 5).mean()), 3), enemies_median=float(np.median(a[:, 1])),
           hero_margin_ge5_frac=round(float((a[:, 2] >= 0.05).mean()), 4), hero_margin_min=round(float(a[:, 2].min()), 3),
           occluder_max_pct=round(float(a[:, 3].max()) * 100, 1), occluder_gt15_frames=int((a[:, 3] > 0.15).sum()),
           fg_body_frames=int((a[:, 10] > 0).sum()), warn_frac=round(float((a[:, 4] > 0).mean()), 3), frozen_frames=int(a[:, 5].sum()),
           attack_starts=len(starts), max_attack_gap=gaps[0][0] if gaps else None, top_gaps=gaps[:4], first_start_after=round(starts[0] - t0, 2) if starts else None)
nc = a[a[:, 6] < 0.05]   # frames outside the finisher push-in
out['cam_dist_m'] = [round(float(np.percentile(nc[:, 7], q)), 2) for q in (5, 50, 95)]
out['cam_pitch_down_deg'] = [round(float(np.percentile(nc[:, 8], q)), 1) for q in (5, 50, 95)]
out['cam_height_over_hero_m'] = [round(float(np.percentile(nc[:, 9], q)), 2) for q in (5, 50, 95)]
low = a[a[:, 2] < 0.05]
if len(low): out['hero_margin_lt5_times'] = [round(float(x), 2) for x in low[::max(1, len(low) // 12), 0]]
few = a[a[:, 1] < 5]
if len(few): out['enemies_lt5_times'] = [round(float(x), 1) for x in few[::max(1, len(few) // 14), 0]]
print(json.dumps(out, indent=1))
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
