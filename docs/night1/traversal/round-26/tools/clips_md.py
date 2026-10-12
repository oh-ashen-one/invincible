#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r26: round-26/CLIPS.md -- per clip: how it was captured (full run / split A+B), the build, the suit log line, frame / row counts,
# and whether the body path / camera equal r25 (round-24 for f4).
import csv, os, re, sys, glob
TD = '/Users/midir/sm2-n1/traversal/docs/night1/traversal'
RD = TD + '/round-26'; CAP = '/Users/midir/sm2-n1/_scratch/traversal/capture'; R = '/Users/midir/sm2-n1/_scratch/traversal/r26'
builds = dict(l.split(None, 1) for l in open(RD + '/tools/BUILDS.txt').read().strip().splitlines()) if os.path.exists(RD + '/tools/BUILDS.txt') else {}
def rows(p): return list(csv.DictReader(open(p))) if os.path.exists(p) else None
def diff(a, b, keys):
    n = min(len(a), len(b)); return max((abs(float(x[k]) - float(y[k])) for x, y in zip(a[:n], b[:n]) for k in keys), default=-1), n
out = ['# P3 round 26 -- clip provenance', '', '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
       'All movies: real `-game` (`Scripts/run_game.sh -movie`, offscreen, `/Game/Maps/Manhattan` golden), 1920x1080 output, internal resolution',
       '1920x1080 (`r.ScreenPercentage 100`), fixed 1/60 s step, 0.8 s pre-roll trimmed, H.264 <= 15 MB, every run inside `gpu_slot.sh capture`',
       '(background priority, shared GPU: no perf claim). Hero suit in every run: the log line `WH_TRAV hero suit` / `WH_SUIT start` below.',
       'Split = two deterministic runs of the same replay (A: frames up to tm + 0.5 s; B: `-WHMovieFrom=tm`, frames from tm), merged at tm after a',
       'pixel comparison of the 0.5 s overlap (`split/<clip>_OVERLAP.txt`). `-WHMovieAsync` = the same lossless PNG frames written off the game thread.', '',
       '| clip | capture | frames / rows | suit (log) | body path vs r25 | camera vs r25 |', '|---|---|---|---|---|---|']
for mp4 in sorted(glob.glob(RD + '/*.mp4')):
    n = os.path.basename(mp4)[:-4]
    tel = rows(f'{RD}/{n}_telemetry.csv')
    ov = f'{RD}/split/{n}_OVERLAP.txt'
    how = 'split ' + open(ov).read().split('\n')[0].split(' at ')[1].split(':')[0] if os.path.exists(ov) else 'full run'
    logs = [f'{CAP}/{n}_B/{n}.log', f'{CAP}/{n}/{n}.log']
    suit = '-'
    for L in logs:
        if os.path.exists(L):
            m = [re.sub(r'^.*Display: ', '', l.strip()) for l in open(L, errors='ignore') if 'WH_SUIT start' in l or 'WH_TRAV hero suit' in l]
            if m: suit = '; '.join(m[:2]); break
    ref = rows(f'{TD}/round-25/{n}_telemetry.csv') or rows(f'{TD}/round-24/{n}_telemetry.csv')
    if tel and ref:
        bp, k = diff(tel, ref, ('x_m', 'y_m', 'z_m')); cm, _ = diff(tel, ref, ('cam_x', 'cam_y', 'cam_z'))
        bps = 'SAME' if bp < 0.01 else f'DIFF {bp:.2f} m'; cms = 'SAME' if cm < 0.01 else f'differs (max {cm:.2f} m)'
    else: bps = cms = 'n/a'
    nf = '?'
    out.append(f'| {n} | {how}{" / " + builds.get(n, "") if builds.get(n) else ""} | {len(tel) if tel else "?"} rows | {suit} | {bps} | {cms} |')
open(RD + '/CLIPS.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
