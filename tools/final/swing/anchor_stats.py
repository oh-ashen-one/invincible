#!/usr/bin/env python3
"""Anchor geometry at every attach (strand tip landed): elevation of anchor above the hero (deg), horizontal angle between the anchor direction and the travel heading (deg).
usage: anchor_stats.py <telemetry.csv>"""
import csv, math, sys
R = list(csv.DictReader(open(sys.argv[1])))
f = lambda r, k: float(r[k]) if r[k] not in ('', 'nan') else 0.0
el, lat = [], []
for i in range(1, len(R)):
    if R[i]['mode'] == 'swing' and R[i - 1]['mode'] != 'swing':
        r = R[i]; d = (f(r, 'fw_s0_ax') - f(r, 'x_m'), f(r, 'fw_s0_ay') - f(r, 'y_m'), f(r, 'fw_s0_az') - f(r, 'z_m'))
        h = math.hypot(d[0], d[1]); el.append(math.degrees(math.atan2(d[2], h)))
        vx, vy = f(r, 'vx'), f(r, 'vy')
        if math.hypot(vx, vy) > 1: lat.append(abs((math.degrees(math.atan2(d[1], d[0]) - math.atan2(vy, vx)) + 180) % 360 - 180))
print('anchors %d: elevation median %.0f deg (min %.0f); horizontal angle to travel median %.0f deg, > 45 deg: %d of %d' % (len(el), sorted(el)[len(el) // 2], min(el), sorted(lat)[len(lat) // 2] if lat else -1, sum(1 for a in lat if a > 45), len(lat)))
