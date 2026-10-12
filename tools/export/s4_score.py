#!/usr/bin/env python3
"""(r10) one-number objective for the S4 far-band sweeps: 0 = every test passes. usage: s4_score.py <frame>  -> one JSON line.
Penalty terms: T1 silhouette-top std (min of the 3 definitions of s4_far_check) below 12 px, T2 share of (0,150,1300,300) above Y 204 over 10 %, and the distance to the allowed range of C11-C15."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import s4_far_check as S, city_spec_check as C
cfg = json.load(open(C.REGFILE)); r = S.analyse(sys.argv[1], cfg)
t1 = min(r['T1_std'].values()); L = {k: v['value'] for k, v in r['lines'].items()}
def dist(v, lo=None, hi=None): return (max(0.0, lo - v) if lo is not None else 0.0) + (max(0.0, v - hi) if hi is not None else 0.0)
pen = {'T1': max(0.0, 12.0 - t1), 'T2': max(0.0, r['box_pct204'] - 10.0) * 0.5, 'C11': dist(L['C11 lap/sky'], lo=6.0) + dist(L['C11 flat8 %'], hi=40.0), 'C12': dist(L['C12 dBR'], -10, 10),
       'C13': dist(L['C13 far-sky Y'], -35, -25), 'C13b': dist(L['C13 far>near'], lo=0.0), 'C14': dist(L['C14 far-river Y'], 5, 35), 'C15': dist(L['C15 rms far/near'], .25, .45) * 60.0,
       'T4': max(0.0, r['T4']['flat_of_bright_pct'] - 10.0) * 0.1 + max(0.0, r['T4']['flat_of_all_pct'] - 10.0) * 0.2}   # (r11) flat bright 8x8 blocks in (540,110,900,260)
score = sum(pen.values()); allpass = bool(r['T1_pass'] and r['T2_pass'] and r['T4_pass'] and all(v['passed'] for v in r['lines'].values()))
print(json.dumps(dict(file=r['file'], score=round(score, 3), all_pass=allpass, T1=round(t1, 2), T2_pct=round(r['box_pct204'], 2), T4_bright=round(r['T4']['flat_of_bright_pct'], 1), T4_all=round(r['T4']['flat_of_all_pct'], 1), sky=round(r['sky_Y'], 1), far=round(r['far_Y'], 1), river=round(r['river_Y'], 1),
                      C13=round(L['C13 far-sky Y'], 1), C14=round(L['C14 far-river Y'], 1), C15=round(L['C15 rms far/near'], 3), pen={k: round(v, 2) for k, v in pen.items() if v > 0})))
