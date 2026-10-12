#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""(island r03) the round-03 pass lines for route 2 (swing held, autoChain gap 0.3 s), from the telemetry CSV + island_route_check.py's json:

    python3 tools/export/island_r2_check.py <telemetry.csv> <route_check.json> [--json out.json] [--t-end 30]

  * no unanswered release through t = t_end (drawn.swing.unanswered_release_at_s is None or > t_end)
  * max re-web gap <= 1.5 s, >= 60 % of the gaps <= 0.5 s (drawn.swing.gaps: [release t, gap s])
  * every anchor on a drawn facade: drawn.web_air_drawn == 0
  * 0 ground / land frames after t = 1 s (telemetry 'mode')
"""
import sys, csv, json


def check(csv_path, rc_path, t_end=30.0):
    rc = json.load(open(rc_path))
    r = rc['routes'][0] if isinstance(rc.get('routes'), list) else rc
    sw = r['drawn']['swing']
    gaps = [g[1] for g in sw['gaps'] if g[0] <= t_end]
    rows = list(csv.DictReader(open(csv_path)))
    gl = [float(x['t']) for x in rows if float(x['t']) > 1.0 and float(x['t']) <= t_end + 0.4 and x['mode'] in ('ground', 'land')]
    ua = sw.get('unanswered_release_at_s')
    res = {
        'csv': csv_path, 'route_check': rc_path, 't_end': t_end,
        'unanswered_release_at_s': ua, 'pass_no_unanswered_release': ua is None or ua > t_end,
        'n_gaps': len(gaps), 'max_reweb_gap_s': max(gaps) if gaps else None, 'pass_max_gap_le_1_5': bool(gaps) and max(gaps) <= 1.5,
        'frac_gaps_le_0_5': round(sum(g <= 0.5 for g in gaps) / len(gaps), 3) if gaps else 0.0,
        'web_air_drawn': r['drawn']['web_air_drawn'], 'pass_anchors_on_drawn': r['drawn']['web_air_drawn'] == 0,
        'distinct_swing_anchors': sw.get('distinct_swing_anchors'),
        'ground_land_frames_after_1s': len(gl), 'first_ground_land_t': gl[0] if gl else None, 'pass_no_ground_after_1s': not gl,
        'path_m': r.get('path_m'), 'end': r.get('end'), 'facadeLod_min_dist_m': r.get('facadeLod_min_dist_m'),
    }
    res['pass_gaps_60pct_le_0_5'] = res['frac_gaps_le_0_5'] >= 0.6
    res['pass_all'] = all(v for k, v in res.items() if k.startswith('pass_') and k != 'pass_all')
    return res


if __name__ == '__main__':
    a = sys.argv[1:]; out = None; t_end = 30.0
    if '--json' in a: i = a.index('--json'); out = a[i + 1]; del a[i:i + 2]
    if '--t-end' in a: i = a.index('--t-end'); t_end = float(a[i + 1]); del a[i:i + 2]
    res = check(a[0], a[1], t_end)
    print(json.dumps(res, indent=1))
    if out: json.dump(res, open(out, 'w'), indent=1)
