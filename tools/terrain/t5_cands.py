#!/usr/bin/env python3
"""r04: candidate routes for docs/night1/terrain/scripts/t5_avenue_to_park.json (headless telemetry probes pick the one whose last 5 s cross the park at 25-40 m).
Writes <outdir>/*.json (traversal scripts: spawn + keys; north = -y, 5th Av at x = 250, the park rectangle x -234..234, y -2151..-569).
usage: t5_cands.py <outdir> [refine | refine3]"""
import json, os, sys
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
def script(name, note, spawn, keys, tune=None):
    d = {'name': 't5_avenue_to_park', 'note': note, 'seed': 1234, 'spawn': spawn, 'keys': keys}
    if tune: d['tune'] = tune
    json.dump(d, open(os.path.join(out, name + '.json'), 'w'), indent=1)
def auto(t, sky, repress, tricks=0, **kw): return dict({'t': t, 'swing': True, 'autoChain': True, 'releasePhase': 0.55, 'gap': 0.8, 'repressVz': repress, 'trickEvery': tricks, 'skyEvery': sky, 'skyTricks': 1, 'skyRepressH': 30, 'skyPhase': 0.8, 'skyMax': 2.8}, **kw)
FOOT = lambda y0: {'pos': [250, y0, 0.95], 'yaw': -90, 'camPitch': 0.14}
AIR = lambda y0, z: {'pos': [250, y0, z], 'yaw': -90, 'camPitch': 0.12, 'vel': [0, -22, 0]}
def foot_keys(sky, th, hd, repress=99.0): return [{'t': 0.0, 'move': [0, 1], 'heading': -90, 'sprint': True}, {'t': 1.8, 'jump': True}, {'t': 2.2, 'jump': False}, auto(2.6, sky, repress)] + ([{'t': th, 'heading': hd}] if th else [])
def air_keys(sky, th, hd, repress=99.0): return [{'t': 0.0, 'move': [0, 1], 'heading': -90, 'swing': False}, dict(auto(0.4, sky, repress), swing=None)] + ([{'t': th, 'heading': hd}] if th else [])
for k in [air_keys(0, 0, 0)]:
    for kk in k:
        for key in [x for x, v in kk.items() if v is None]: del kk[key]
REFINE = len(sys.argv) > 2 and sys.argv[2] == 'refine'
REFINE3 = len(sys.argv) > 2 and sys.argv[2] == 'refine3'   # r04 hold 2: variants around the hold-1 winner s5_y290_sky1_hang25 (59 % of the last 5 s over the park at 25-40 m, 78 % over the park, lands at 15.0 s)
T0 = 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.25,SkyHangVz=9'
CR = [
 ('w0_s5_again', 'hold-1 winner (control)', FOOT(-290), foot_keys(1, 9.0, -130), T0),
 ('w1_y300_hang15', 'foot start y -300 (park entry ~0.3 s earlier), hang 0.15', FOOT(-300), foot_keys(1, 9.0, -130), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.15,SkyHangVz=9'),
 ('w2_y290_hang10', 'hang 0.10, hang band |vz| < 12', FOOT(-290), foot_keys(1, 9.0, -130), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.10,SkyHangVz=12'),
 ('w3_y290_peak34_40', 'apex 34-40 m with hang 0.15', FOOT(-290), foot_keys(1, 9.0, -130), 'SkyPeakMin=34,SkyPeakMax=40,SkyHangK=0.15,SkyHangVz=10'),
 ('w4_y300_h140', 'heading -140 from 9 s, hang 0.15', FOOT(-300), foot_keys(1, 9.0, -140), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.15,SkyHangVz=9'),
 ('w5_y310_hang12', 'foot start y -310, hang 0.12, apex 32-38 m', FOOT(-310), foot_keys(1, 9.5, -130), 'SkyPeakMin=32,SkyPeakMax=38,SkyHangK=0.12,SkyHangVz=10'),
 ('w6_y290_t95', 'heading change at 9.5 s, hang 0.15', FOOT(-290), foot_keys(1, 9.5, -130), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.15,SkyHangVz=9'),
 ('w7_y320_hang10', 'foot start y -320, hang 0.10, apex 32-38 m', FOOT(-320), foot_keys(1, 9.0, -125), 'SkyPeakMin=32,SkyPeakMax=38,SkyHangK=0.10,SkyHangVz=12'),
]
# r04 hold 3: variants around the hold-2 winners (w5_y310_hang12: foot y -310, heading -130 from 9.5 s, sky launches with a 32-38 m apex and hang 0.12 = 89 % of the last 5 s over the park at 20-45 m, never below 27 m;
# w6_y290_t95: 72 % at 25-40 m but dives to 11 m at the end)
CR3 = [
 ('x1_w5_again', 'hold-2 w5 (control)', FOOT(-310), foot_keys(1, 9.5, -130), 'SkyPeakMin=32,SkyPeakMax=38,SkyHangK=0.12,SkyHangVz=10'),
 ('x2_peak30_36', 'w5 with a 30-36 m apex', FOOT(-310), foot_keys(1, 9.5, -130), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.12,SkyHangVz=10'),
 ('x3_y305', 'w5 from y -305', FOOT(-305), foot_keys(1, 9.5, -130), 'SkyPeakMin=32,SkyPeakMax=38,SkyHangK=0.12,SkyHangVz=10'),
 ('x4_y315', 'w5 from y -315', FOOT(-315), foot_keys(1, 9.5, -130), 'SkyPeakMin=32,SkyPeakMax=38,SkyHangK=0.12,SkyHangVz=10'),
 ('x5_t10', 'w5 with the heading change at 10 s', FOOT(-310), foot_keys(1, 10.0, -130), 'SkyPeakMin=32,SkyPeakMax=38,SkyHangK=0.12,SkyHangVz=10'),
 ('x6_hang15_peak31_37', 'w5 with hang 0.15, apex 31-37 m', FOOT(-310), foot_keys(1, 9.5, -130), 'SkyPeakMin=31,SkyPeakMax=37,SkyHangK=0.15,SkyHangVz=10'),
]
C = [
 ('f2_y290_h130_sky1', 'foot start y -290, heading -130 from 9 s, sky launches', FOOT(-290), foot_keys(1, 9.0, -130)),
 ('f3_y250_h125_sky1', 'foot start y -250, heading -125 from 8 s, sky launches', FOOT(-250), foot_keys(1, 8.0, -125)),
 ('a1_y200_h130_sky1', 'airborne start (250, -200, 26), heading -130 from 8.5 s, sky launches, re-press at -12 m/s', AIR(-200, 26), air_keys(1, 8.5, -130, -12.0)),
 ('a3_y240_h120_sky1', 'airborne start (250, -240, 26), heading -120 from 9.5 s, sky launches', AIR(-240, 26), air_keys(1, 9.5, -120)),
 ('a4_y160_h135_sky2', 'airborne start (250, -160, 26), heading -135 from 7.5 s, every 2nd release a sky launch', AIR(-160, 26), air_keys(2, 7.5, -135, -12.0)),
 ('s1_y200_sky1_peak40', 'airborne start (250, -200, 26), heading -130 from 8.5 s, sky launches capped at a 26-40 m peak', AIR(-200, 26), air_keys(1, 8.5, -130, -12.0), 'SkyPeakMin=26,SkyPeakMax=40,SkyLaunchVzMax=42'),
 ('s2_y290_sky1_peak40', 'foot start y -290, heading -130 from 9 s, sky launches capped at a 26-40 m peak', FOOT(-290), foot_keys(1, 9.0, -130), 'SkyPeakMin=26,SkyPeakMax=40,SkyLaunchVzMax=42'),
 ('s4_y200_sky1_hang25', 'airborne start (250, -200, 26), heading -130 from 8.5 s, sky launches capped at a 30-36 m peak with a long apex hang', AIR(-200, 26), air_keys(1, 8.5, -130, -12.0), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.25,SkyHangVz=9'),
 ('s5_y290_sky1_hang25', 'foot start y -290, heading -130 from 9 s, sky launches capped at a 30-36 m peak with a long apex hang', FOOT(-290), foot_keys(1, 9.0, -130), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.25,SkyHangVz=9'),
 ('s6_y260_sky1_hang25', 'airborne start (250, -260, 26), heading -120 from 9 s, sky launches capped at a 30-36 m peak with a long apex hang', AIR(-260, 26), air_keys(1, 9.0, -120), 'SkyPeakMin=30,SkyPeakMax=36,SkyHangK=0.25,SkyHangVz=9'),
 ('s3_y240_sky1_hang', 'airborne start (250, -240, 26), heading -120 from 9.5 s, sky launches 30-45 m peak with more hang', AIR(-240, 26), air_keys(1, 9.5, -120), 'SkyPeakMin=30,SkyPeakMax=45,SkyHangK=0.4'),
]
for c in (CR3 if REFINE3 else CR if REFINE else C):
    n, note, sp, ks = c[:4]
    for kk in ks:
        for key in [x for x, v in kk.items() if v is None]: del kk[key]
    script(n, note, sp, ks, c[4] if len(c) > 4 else None)
print('%d candidates in %s' % (len(CR3 if REFINE3 else CR if REFINE else C), out))
