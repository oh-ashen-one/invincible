#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r03: victim-reaction numbers from a run's fight_frames.jsonl + fight_events.jsonl (video-free, any run mode, nullrhi included).
#   react_metrics.py <run_dir> [out.json]
# For every hero blow ('hit <kind> -> eN ...' event) at real time t (frame f):
#   push03   = 3D distance the victim's root moved between the frame BEFORE the contact and 0.3 s (real) after it   (target >= 0.5 m)
#   rot03    = largest visual yaw change (actor yaw + hit twist) within those 0.3 s, degrees                          (target >= 30)
#   dmax1    = furthest 3D distance from the pre-contact root within 1.0 s                                            (heavy / finisher / launcher >= 2 m)
# r04 adds tilt03 (largest change of the body's tilt = angle between its up axis and the vertical: the recoil lean about the knees + tumble, from the
# 16th enemy field of fight_frames.jsonl) and turn03 = max(rot03, tilt03): CB2 says "moves >= 0.5 m OR rotates >= 30 deg" (a rotation about any axis counts).
# 'heavy' = kind in ender / launch / strike / finisher / throw on a victim that was not ARMORED (armoured brutes take a flinch + push by design).
import json, os, sys
import numpy as np

HEAVY = {'ender', 'launch', 'strike', 'finisher', 'throw'}

def load(d):
    rows = [json.loads(l) for l in open(os.path.join(d, 'fight_frames.jsonl')) if l.strip()]
    ev = [json.loads(l) for l in open(os.path.join(d, 'fight_events.jsonl')) if l.strip()]
    return rows, ev

def enemy_rows(r):
    """tag -> dict(pos, yaw, held, alive, state) from one frame row (rows written before r03 have no yaw / held: yaw None)"""
    out = {}
    for e in r['e']:
        out[e[0]] = dict(pos=np.array(e[3:6]), yaw=e[13] if len(e) > 13 else None, held=e[14] if len(e) > 14 else 0, alive=e[12], state=e[2], tilt=e[15] if len(e) > 15 else None)
    return out

def wrap(a):
    return (a + 180.0) % 360.0 - 180.0

def analyse(rows, ev, win=0.3):
    rt = np.array([r['rt'] for r in rows]); byf = {i: r for i, r in enumerate(rows)}
    fr = [enemy_rows(r) for r in rows]
    res = []
    for e in ev:
        s = e['ev']
        if not (s.startswith('hit ') and '->' in s): continue
        kind = s.split()[1]; tag = s.split('->')[1].split()[0]
        armored = 'ARMORED' in s
        fc = int(np.argmin(np.abs(rt - e['rt'])))
        fb = max(0, fc - 1)
        if tag not in fr[fb]: continue
        p0, y0 = fr[fb][tag]['pos'], fr[fb][tag]['yaw']
        f03 = int(np.argmin(np.abs(rt - (rows[fb]['rt'] + win + 1 / 60.0))))   # 0.3 s after the pre-contact frame + the contact frame's own step
        f10 = int(np.argmin(np.abs(rt - (rows[fb]['rt'] + 1.0))))
        push = rot = tilt = None; dmax = 0.0
        t0 = fr[fb][tag].get('tilt')
        for f in range(fc, min(len(rows), f10 + 1)):
            if tag not in fr[f]: continue
            d = float(np.linalg.norm(fr[f][tag]['pos'] - p0)); dmax = max(dmax, d)
            if f <= f03:
                push = d
                if y0 is not None and fr[f][tag]['yaw'] is not None:
                    rot = max(rot or 0.0, abs(wrap(fr[f][tag]['yaw'] - y0)))
                if t0 is not None and fr[f][tag].get('tilt') is not None:
                    tilt = max(tilt or 0.0, abs(fr[f][tag]['tilt'] - t0))
        res.append(dict(rt=round(e['rt'], 3), kind=kind, victim=tag, armored=armored, heavy=(kind in HEAVY and not armored),
                        push03=None if push is None else round(push, 2), rot03=None if rot is None else round(rot, 1),
                        tilt03=None if tilt is None else round(tilt, 1), turn03=None if (rot is None and tilt is None) else round(max(rot or 0.0, tilt or 0.0), 1), dmax1=round(dmax, 2)))
    return res

def summarize(res):
    n = len(res)
    have_rot = [r for r in res if r['rot03'] is not None]
    hv = [r for r in res if r['heavy']]
    return dict(hero_blows=n,
                push03_ge_0_5=sum((r['push03'] or 0) >= 0.5 for r in res),
                rot03_ge_30=sum((r['rot03'] or 0) >= 30 for r in have_rot), rot_measured=len(have_rot),
                heavy_blows=len(hv), heavy_dmax1_ge_2=sum(r['dmax1'] >= 2.0 for r in hv),
                push03_min=min((r['push03'] for r in res if r['push03'] is not None), default=None),
                rot03_min=min((r['rot03'] for r in have_rot), default=None),
                heavy_dmax1_min=min((r['dmax1'] for r in hv), default=None),
                tilt03_ge_30=sum((r.get('tilt03') or 0) >= 30 for r in res), tilt03_median=float(np.median([r['tilt03'] for r in res if r.get('tilt03') is not None])) if any(r.get('tilt03') is not None for r in res) else None,
                turn03_ge_30=sum((r.get('turn03') or 0) >= 30 for r in res),
                move_or_turn=sum(((r['push03'] or 0) >= 0.5) or ((r.get('turn03') or 0) >= 30) for r in res),
                misses=[r for r in res if (r['push03'] or 0) < 0.5 or (r['rot03'] is not None and r['rot03'] < 30) or (r['heavy'] and r['dmax1'] < 2.0)])

if __name__ == '__main__':
    rows, ev = load(sys.argv[1])
    res = analyse(rows, ev)
    out = dict(summary=summarize(res), blows=res)
    print(json.dumps(out['summary'], indent=1))
    if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
