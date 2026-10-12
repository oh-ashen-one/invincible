#!/usr/bin/env python3
"""Round-05 results table (markdown) from the measurement files of one round dir. Homage fan game; not an official Marvel, Sony or Insomniac game.
usage: r05_table.py <round dir>"""
import json, os, sys
R = sys.argv[1]
J = lambda f: json.load(open(os.path.join(R, f))) if os.path.exists(os.path.join(R, f)) else None
cs = J('crown_stats.json'); ls = J('lawn_stats.json'); ts = J('tree_shadow_p4.json'); fq = J('flatquad_t4.json'); t5 = J('t5_ground_sd.json')
rows = []
if cs:
    s = cs['summary']; sil = {x['image']: x for x in cs['silhouette']}
    rows.append(('1. p1 crown crops sigma-3 SD (24 E8 boxes)', 'all >= 9, median >= 12', 'median **%.2f**, %d / 24 >= 9, min %.2f (r04 median 8.13, 9 / 24, min 5.67; r03 7.74, 5 / 24)' % (s['median_hp_sd'], s['crops_ge_9'], s['min_hp_sd']),
                 'median PASS, all-crops FAIL' if s['median_hp_sd'] >= 12 and s['min_hp_sd'] < 9 else ('PASS' if s['median_hp_sd'] >= 12 else 'FAIL')))
    rows.append(('2. median crown-crop saturation', '>= 0.65', '**%.3f** (same tool: r04 0.518, r03 0.522)' % s['median_hsv_sat'], 'PASS' if s['median_hsv_sat'] >= 0.65 else 'FAIL'))
    p10 = sil.get('p10_lawn_eye.jpg')
    if p10:
        segs = ', '.join('%.1f' % x['len_px'] for x in p10['longest'][:3])
        rows.append(('3. E9c longest straight crown silhouette, p10', '<= 42 px, no floating hull / saucer cards', 'tool **%.1f px** (top 3: %s; the longest is the stepped roof of a building at x 3630-3670, y 340: `e9c_longest_segment_building.jpg`); no hull balls or saucer cards (the LOD1 core pool is not built)' % (p10['longest_straight_px'], segs),
                     'PASS' if p10['longest_straight_px'] <= 42 else 'FAIL'))
if ts:
    s = ts['summary']
    rows.append(('4. isolated p4 trees: lawn shadow / lit lawn luma', '<= 0.6 each', '%d tree(s) measurable by geometry (`tree_shadow_auto.py`, isolation 12 m): ratio %s; no crown shadow visible on the p4 lawn (trunk / lamp shadows are)' % (s['trees_measured'], s['max_ratio']), 'FAIL'))
if ls:
    c = {x['label'].split(' (')[0]: x for x in ls['crops']}
    a, g, p = c.get('critic p10_lawn_eye'), c.get('guard p10'), c.get('critic p4_greatlawn')
    rows.append(('5. E1 reconciled: p10 critic / guard sigma-6, p10 R / G', '>= 8 / >= 8, 0.85-0.95', '**%.2f / %.2f**, R / G **%.3f** (r04 11.25 / 9.97, 0.77)' % (a['hp6_sd'], g['hp6_sd'], a['r_over_g']), 'PASS' if a['hp6_sd'] >= 8 and g['hp6_sd'] >= 8 and 0.85 <= a['r_over_g'] <= 0.95 else 'FAIL'))
    rows.append(('5. E1 reconciled: p4 critic box sigma-6 (aerial)', '<= 5', '**%.2f** (r04 10.85; the box holds a crown corner, an infield edge and a bench)' % p['hp6_sd'], 'PASS' if p['hp6_sd'] <= 5 else 'FAIL'))
    sats = ', '.join('%.3f' % x['mean_hsv_sat'] for x in ls['crops'])
    rows.append(('E10 (b) lawn-crop saturation (5 boxes)', '>= 0.70', sats, 'PASS' if min(x['mean_hsv_sat'] for x in ls['crops']) >= 0.70 else 'FAIL'))
if fq: rows.append(('E10 (c) flat quads > 100 px in t4 at 4 fps', 'none', '%d in %d frames' % (fq['components_wider_than_100px'], fq['frames_at_4fps']), 'PASS' if fq['pass'] else 'FAIL'))
if t5: rows.append(('E10 (d) t5 last 5 s, ground sigma-3 at 25-40 m', '>= 5', 'median %.2f, min %.2f in %d frames (r04 7.38 / 5.32)' % (t5['median_in_25_40m_band'], t5['min_in_25_40m_band'], t5['frames_in_25_40m_band']), 'PASS' if t5['pass_band_ge_5'] else 'FAIL'))
print('| target | wanted | measured | verdict |\n|---|---|---|---|')
for r in rows: print('| %s | %s | %s | %s |' % r)
