#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02 (r03: reaction misses cost 1.5 each): choose the record seed automatically from a sweep (sim-only metrics of the -nullrhi record runs).
#   pick_seed.py <sweep_dir>            prints the chosen seed number
# Hard requirements (a seed failing one is skipped): 3 launchers, 9 air hits, 2 finishers, >= 4 web hits, longest attack gap <= 0.95 s,
# no frame with an occluder > 15 %. Score: hits - foreground-body frames / 20 - occluder max % / 5 - damage / 40.
import glob, json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); best = None
import react_metrics as RM
for d in sorted(glob.glob(os.path.join(sys.argv[1], 'seed[0-9]*'))):
    if not os.path.isdir(d): continue
    try:
        S = json.load(open(os.path.join(d, 'fight_summary.json')))
        M = json.loads(subprocess.run([sys.executable, os.path.join(here, 'sim_metrics.py'), d], capture_output=True, text=True).stdout)
    except Exception: continue
    if S['launches'] < 3 or S['air_hits'] < 9 or S['finishers'] < 2 or S['web_hits'] < 4 or (M['max_attack_gap'] or 9) > 0.95 or M['occluder_gt15_frames'] > 0: continue
    try:
        rr = RM.summarize(RM.analyse(*RM.load(d)))   # r03: every blow must push >= 0.5 m and turn >= 30 deg within 0.3 s, heavy ones >= 2 m
    except Exception: continue
    if rr['hero_blows'] < 25: continue
    sc = S['hits'] - M['fg_body_frames'] / 20 - M['occluder_max_pct'] / 5 - S['damage_taken'] / 40 - 1.5 * len(rr['misses'])
    if best is None or sc > best[0]: best = (sc, int(os.path.basename(d)[4:]))
print(best[1] if best else 23)
