# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""CH19 (round 05): gait-phase spread of the Char_Crowd walkers from the build script's own parameters (AnimOffset golden-ratio seed, clip cycle
length per walk style, natural ground speed = natural clip rate so the phase advances at the clip rate).
  python3 gait_phase.py [t_seconds ...]  -> JSON with the phases (cycles) at each time and the spread measures"""
import json, sys, itertools
import numpy as np
LEN = {'walk': 32 / 30, 'walkF': 30 / 30, 'walkBrisk': 29 / 30, 'walkStroll': 38 / 30, 'walkOld': 40 / 30}   # people.json clip lengths / 30 fps (s per cycle)
# same order as build_characters.py 'maps5' (mid lane 12, near lane 6; anim_offset = (0.61803 * n) % 1, n = 1 .. 18)
MID = ['03_white_tee:walk', '12_sundress_mom:walkF', '13_construction_worker:walkStroll', '15_executive:walkBrisk', '04_blue_sweatshirt:walkF',
       '19_marathon_runner:walkBrisk', '10_silver_tie:walk', '14_teen_skater:walk', '01_retired_gent:walkOld', '20_punk_artist:walkF', '18_dapper_elder:walkOld',
       '08_black_suit:walkBrisk']
NEAR = ['02_leather_jacket:walk', '06_chrome_shades:walkStroll', '16_lumberjack_hipster:walkStroll', '05_black_tee:walkBrisk', '17_hijabi_student:walkF',
        '09_kurta_waistcoat:walk']
ts = [float(a) for a in sys.argv[1:]] or [0.0, 5.5, 11.5]
walkers = MID + NEAR
out = dict(walkers=walkers, times={})
for t in ts:
    ph = np.array([((0.61803 * (i + 1)) % 1.0 + t / LEN[w.split(':')[1]]) % 1.0 for i, w in enumerate(walkers)])
    z = np.exp(2j * np.pi * ph)
    d = [min(abs(a - b), 1 - abs(a - b)) for a, b in itertools.combinations(ph, 2)]
    zn = np.exp(2j * np.pi * ph[12:])
    out['times'][str(t)] = dict(phases=[round(float(x), 3) for x in ph], resultant_length_R=round(float(abs(z.mean())), 3),
                                pairwise_circular_diff_min=round(float(min(d)), 3), pairwise_median=round(float(np.median(d)), 3),
                                near_lane_R=round(float(abs(zn.mean())), 3),
                                largest_gap_cycles=round(float(np.max(np.diff(np.r_[np.sort(ph), np.sort(ph)[0] + 1]))), 3))
print(json.dumps(out, indent=1))
