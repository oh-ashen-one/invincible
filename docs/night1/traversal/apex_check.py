#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 12: per trick (flip program), where it starts and plays relative to the rooftops (critic r11: "start every release trick
# from an apex >= 3 m above the tallest roof within 30 m"), plus the flip camera's searched view. Engine side, from telemetry:
# sky_tall_m / sky_peak_want_m (what the launch solver found / aimed for, m over the street), z_m (body centre; feet = z - 0.95),
# flipcam_* (searched yaw offset from behind, look-up elevation, ring sky share predicted by the raycast search).
# usage: apex_check.py <telemetry.csv> <label>
import csv, sys
import numpy as np
R = list(csv.DictReader(open(sys.argv[1]))); lab = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
f = lambda r, k, d=0.0: float(r[k]) if r.get(k, '') not in ('', None) else d
segs = []; cur = None
for i, r in enumerate(R):
    on = r['sub'] == 'trick' and r.get('flip_prog', '') != ''
    if on and cur is None: cur = [i, i]
    elif on: cur[1] = i
    elif cur is not None: segs.append(cur); cur = None
if cur is not None: segs.append(cur)
print('== %s: %d flip programs' % (lab, len(segs)))
launches = [i for i in range(1, len(R)) if f(R[i], 'sky_peak_want_m') != f(R[i - 1], 'sky_peak_want_m')]
for a, b in segs:
    ra, rb = R[a], R[b]
    # release = last row before a that was swinging
    rel = max([j for j in range(a) if R[j]['mode'] == 'swing'] or [a])
    feet = np.array([f(R[j], 'z_m') - 0.95 for j in range(a, b + 1)])
    street = f(ra, 'z_m') - 0.95 - f(ra, 'height_above_floor_m')
    tall = f(ra, 'sky_tall_m', -1); want = f(ra, 'sky_peak_want_m', 0)
    sky = [f(R[j], 'flipcam_sky', -1) for j in range(a, b + 1)]
    el = [f(R[j], 'flipcam_elev_deg') for j in range(a, b + 1)]; yw = [f(R[j], 'flipcam_yaw_deg') for j in range(a, b + 1)]
    print(' %s %.2f-%.2f s (release %.2f, +%.2f s): feet over street start %.1f / max %.1f / end %.1f m; solver tallest roof %.1f m, peak want %.1f -> start %+.1f m over that roof'
          % (ra['flip_prog'], f(ra, 't'), f(rb, 't'), f(R[rel], 't'), f(ra, 't') - f(R[rel], 't'), feet[0] - street, feet.max() - street, feet[-1] - street,
             tall, want, (feet[0] - street) - tall if tall > -0.5 else float('nan')))
    print('    flip cam: yaw off p50 %.0f deg, look-up elev p50 %.0f deg (max %.0f), predicted ring sky share min %.2f p50 %.2f' % (np.median(yw), np.median(el), max(el), min(sky), np.median(sky)))
    nxt = next((j for j in range(b, len(R)) if R[j]['mode'] == 'swing'), None)
    print('    next web: %s' % ('%.2f s (%.2f s after the program)' % (f(R[nxt], 't'), f(R[nxt], 't') - f(rb, 't')) if nxt else 'none in clip'))
