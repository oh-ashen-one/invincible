#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Piece C route check on a P3 traversal telemetry CSV (-WHTravScript run in the Manhattan map).
#   fall-through : hero feet below the street (z < -0.3 m) or below the floor under him (height_above_floor < -0.3 m)
#   stuck        : longest stretch after the route start with horizontal speed < 1 m/s (standing is only allowed before t0)
#                  + longest stretch in one mode other than swing / air / ground
#   T-pose       : anim weight < 0.5 or no anim node (same rule as docs/night1/traversal/anim_check.py, one-row shift)
#   bounds       : hero inside the detailed city block (UE x -256..512, y -512..256 m) the whole time
# usage: route_check.py <telemetry.csv> [--t0 0] [--json out.json]
import csv, sys, json, math, argparse
ap = argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--t0', type=float, default=0.0); ap.add_argument('--json')
a = ap.parse_args()
rows = list(csv.DictReader(open(a.csv)))
for i in range(len(rows) - 1):  # anim / pose columns are sampled at the start of the next frame (P3 telemetry quirk)
    for k in ('anim_node', 'anim_clip', 'anim_weight', 'pose_sig'):
        if k in rows[i + 1]: rows[i][k] = rows[i + 1][k]
rows = rows[:-1]
f = lambda r, k: float(r[k])
T = [f(r, 't') for r in rows]
res = {'csv': a.csv.split('/')[-1], 'frames': len(rows), 't_first': T[0], 't_last': T[-1], 'duration_s': round(T[-1] - T[0], 3), 't0': a.t0}
zs = [f(r, 'z_m') for r in rows]; hf = [f(r, 'height_above_floor_m') for r in rows]
res['min_z_m'] = round(min(zs), 3); res['min_height_above_floor_m'] = round(min(hf), 3)
ft = [T[i] for i in range(len(rows)) if zs[i] < -0.3 or hf[i] < -0.3]
res['fall_through_frames'] = len(ft); res['fall_through_first_t'] = ft[0] if ft else None
# path
xs = [f(r, 'x_m') for r in rows]; ys = [f(r, 'y_m') for r in rows]
res['start_xy'] = [round(xs[0], 1), round(ys[0], 1)]; res['end_xy'] = [round(xs[-1], 1), round(ys[-1], 1)]
res['path_length_m'] = round(sum(math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(len(rows) - 1)), 1)
res['max_z_m'] = round(max(zs), 1)
oob = [T[i] for i in range(len(rows)) if not (-256 <= xs[i] <= 512 and -512 <= ys[i] <= 256)]
res['out_of_detail_block_frames'] = len(oob); res['out_of_detail_block_first_t'] = oob[0] if oob else None
# stuck
best = cur = 0.0; best_at = None; start = None
for i, r in enumerate(rows):
    if T[i] < a.t0 + 0.5: continue
    if f(r, 'hspeed_mps') < 1.0:
        if start is None: start = T[i]
        cur = T[i] - start
        if cur > best: best, best_at = cur, start
    else:
        start = None
res['longest_slow_stretch_s'] = round(best, 3); res['longest_slow_stretch_at'] = best_at
# pinned / hanging: net horizontal displacement < 10 m over any 3 s window after the route start (P3 turn / hang bugs keep speed > 1 m/s
# while going nowhere, e.g. circling against a facade)
lp = [T[i] for i in range(len(rows)) if T[i] >= a.t0 + 2.5 for j in [next((k for k in range(i, len(rows)) if T[k] >= T[i] + 3.0), None)]
      if j is not None and math.hypot(xs[j] - xs[i], ys[j] - ys[i]) < 10.0]
res['low_progress_3s_windows'] = len(lp); res['low_progress_first_t'] = lp[0] if lp else None
modes = {}; seg = []; m0 = rows[0]['mode']; s0 = T[0]
for i, r in enumerate(rows + [None]):
    m = r['mode'] if r else None
    if m != m0:
        seg.append((m0, s0, T[i - 1] if r is None else T[i])); m0 = m; s0 = T[i] if r else None
for m, s, e in seg: modes[m] = round(modes.get(m, 0.0) + (e - s), 2)
res['mode_seconds'] = modes
other = [(m, round(e - s, 2), s) for m, s, e in seg if m not in ('swing', 'air', 'ground') and e - s > 3.0]
res['long_other_mode_segments'] = other
res['attaches'] = sum(1 for i in range(1, len(rows)) if rows[i]['mode'] == 'swing' and rows[i - 1]['mode'] != 'swing')
res['max_speed_mps'] = round(max(f(r, 'speed_mps') for r in rows), 1)
# anim
tp = [T[i] for i, r in enumerate(rows) if 'anim_weight' in r and (float(r['anim_weight'] or 0) < 0.5 or r['anim_node'] in ('none', 'None', ''))]
res['tpose_frames'] = len(tp); res['tpose_first_t'] = tp[0] if tp else None
res['anim_nodes'] = sorted(set(r.get('anim_node', '') for r in rows))[:60]
if 'cam_in_geometry' in rows[0]: res['cam_in_geometry_frames'] = sum(1 for r in rows if r['cam_in_geometry'] not in ('0', '', 'false', 'False'))
if 'hero_occl' in rows[0]:
    try: res['hero_occluded_frames'] = sum(1 for r in rows if float(r['hero_occl'] or 0) > 0.02)
    except ValueError: pass
res['pass'] = {'no_fall_through': res['fall_through_frames'] == 0, 'no_stuck': res['longest_slow_stretch_s'] < 1.5 and not other and not lp,
               'no_tpose': res['tpose_frames'] == 0, 'in_detail_block': res['out_of_detail_block_frames'] == 0}
print(json.dumps(res, indent=1))
if a.json: json.dump(res, open(a.json, 'w'), indent=1)
