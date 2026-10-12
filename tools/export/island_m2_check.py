#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""(island r03) pass lines of the M2 route (swing held, autoChain gap 0.3 s, starting at y ~1010 over the new tiles):

    python3 tools/export/island_m2_check.py <export_dir> <telemetry.csv> --out <check.json> [--rc <route_check.json>] [--stills a.jpg b.jpg ...]
                                            [--r02-overlap N] [--t-end 30]

  swing      0 unanswered release, max re-web gap <= 1.5 s, >= 60 % of the gaps <= 0.5 s     (island_r2_check.py)
  ground     0 ground / land frames after t = 1 s                                            (island_r2_check.py)
  drawn      0 webs on nothing, 0 fall-through, 0 stuck, 0 mid-air (drawn), 0 wall-air (drawn) (island_route_check.py)
  road band  for every still named *_t<S>s_*: lane paint >= 1 % and luminance std >= 35      (island_road_band.py)
  overlap    capsule-overlap frames (feet_overlap_frames) reported next to --r02-overlap (the round-02 number to stay under)
If --rc is missing, island_route_check.py is run on the CSV first (route check json written beside --out).
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import island_r2_check, island_road_band


def main(a):
    def opt(name, default=None, n=1):
        if name in a:
            i = a.index(name); v = a[i + 1:i + 1 + n]; del a[i:i + 1 + n]
            return v if n > 1 else v[0]
        return default
    out = opt('--out'); rc = opt('--rc'); t_end = float(opt('--t-end', 30.0)); r02 = opt('--r02-overlap')
    stills = []
    if '--stills' in a:
        i = a.index('--stills'); stills = a[i + 1:]; a = a[:i]
    export, csv_path = a[0], a[1]
    if not rc:
        rc = os.path.splitext(out)[0] + '_route_check.json'
        subprocess.run([sys.executable, os.path.join(HERE, 'island_route_check.py'), export, csv_path, '--out', rc], check=True, stdout=subprocess.DEVNULL)
    res = island_r2_check.check(csv_path, rc, t_end)
    R = json.load(open(rc))['routes'][0]; D = R['drawn']
    res['fall_through'] = R['fall_through']; res['stuck'] = R['stuck']
    res['mid_air_drawn_frames'] = D['mid_air_drawn_frames']; res['wall_air_drawn_frames'] = D['wall_air_drawn_frames']
    res['feet_overlap_frames'] = D['feet_overlap_frames']; res['feet_overlap_by_kind'] = D['feet_overlap_by_kind']
    res['feet_point_inside_frames'] = D['feet_point_inside_frames']
    res['r02_overlap_frames'] = None if r02 is None else int(r02)
    res['pass_overlap_le_r02'] = None if r02 is None else D['feet_overlap_frames'] <= int(r02)
    res['pass_no_fall_stuck_midair_wallair'] = (R['fall_through'] == 0 and R['stuck'] == 0 and D['mid_air_drawn_frames'] == 0 and D['wall_air_drawn_frames'] == 0)
    res['modes'] = R['modes']; res['start'] = R['start']
    bands = []
    for p in stills:
        b = island_road_band.band_stats(p); bands.append(b)
    res['road_band'] = bands
    res['pass_road_band_all'] = bool(bands) and all(b['pass_paint_ge_1pct'] and b['pass_std_ge_35'] for b in bands)
    keys = ['pass_no_unanswered_release', 'pass_max_gap_le_1_5', 'pass_gaps_60pct_le_0_5', 'pass_no_ground_after_1s', 'pass_anchors_on_drawn',
            'pass_no_fall_stuck_midair_wallair', 'pass_road_band_all']
    if r02 is not None: keys.append('pass_overlap_le_r02')
    res['pass_all_m2'] = all(res[k] for k in keys)
    if out: json.dump(res, open(out, 'w'), indent=1)
    s = lambda k: '%s=%s' % (k, 'PASS' if res[k] else 'FAIL')
    print('unanswered', res['unanswered_release_at_s'], '| max gap', res['max_reweb_gap_s'], '| gaps<=0.5 %.1f %% of %d' % (100 * res['frac_gaps_le_0_5'], res['n_gaps']),
          '| ground/land after 1 s', res['ground_land_frames_after_1s'], '(first %s)' % res['first_ground_land_t'], '| anchors on nothing', res['web_air_drawn'],
          '| fall/stuck/midair/wallair', res['fall_through'], res['stuck'], res['mid_air_drawn_frames'], res['wall_air_drawn_frames'], '| overlap', res['feet_overlap_frames'], 'vs r02', r02,
          '| path %.0f m' % (res['path_m'] or 0), '| end', res['end'])
    for b in bands: print('  road band %-60s paint %5.2f %%  std %5.1f' % (os.path.basename(b['frame'])[:60], b['lane_paint_pct'], b['luma_std']))
    print(' '.join(s(k) for k in keys), 'ALL=%s' % res['pass_all_m2'])
    return res


if __name__ == '__main__':
    main(sys.argv[1:])
