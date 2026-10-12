#!/usr/bin/env python3
"""Swing-chain statistics of a telemetry CSV: web-on share of frames, longest stretch without a live strand, attach gaps (release -> next strand on), swing-bottom heights over the floor, unpowered falls > 0.8 s.
usage: chain_stats.py <telemetry.csv> [--case NAME]"""
import csv, sys
a = sys.argv[1:]
case = a[a.index('--case') + 1] if '--case' in a else None
R = [r for r in csv.DictReader(open(a[0])) if not case or r.get('case') == case]
f = lambda r, k: float(r[k]) if r[k] not in ('', 'nan') else 0.0
N = len(R); DT = 1 / 60
live = [f(r, 'fw_s0_on') > 0.5 and f(r, 'fw_s0_rel') < 0 for r in R]
gaps, run = [], 0
for l in live:
    if not l: run += 1
    elif run: gaps.append(run * DT); run = 0
if run: gaps.append(run * DT)
bot = []
i = 0
while i < N:
    if R[i]['mode'] == 'swing':
        j = i
        while j < N and R[j]['mode'] == 'swing': j += 1
        bot.append(min(f(R[k], 'height_above_floor_m') for k in range(i, j))); i = j
    else: i += 1
print('rows %d (%.1f s): web-on %.1f %%; longest no-strand stretch %.2f s; stretches > 0.8 s: %d of %d (%s); swing-bottom height over the floor min %.1f median %.1f m (%d swings)' % (
    N, N * DT, 100.0 * sum(live) / N, max(gaps) if gaps else 0, sum(1 for g in gaps if g > 0.8), len(gaps), ' '.join('%.2f' % g for g in gaps[:12]), min(bot) if bot else -1, sorted(bot)[len(bot) // 2] if bot else -1, len(bot)))
