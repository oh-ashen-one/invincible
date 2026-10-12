"""Measure hero locomotion clips from the GLB keys (FK): step rate, head-to-hip lean, arm swing, foot drift.
Fan homage project; not official Marvel/Sony/Insomniac.  python3 measure_clip.py GLB clip [clip ...] [--json out]"""
import sys, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ganim import Doc

FWD = np.array([0, 0, 1.0]); UP = np.array([0, 1.0, 0])


def lean_deg(W, d):
    v = d.pos(W, 'head') - d.pos(W, 'hips')
    return float(np.degrees(np.arctan2(v @ FWD, v @ UP)))


def measure(d, name, fps=60):
    T = d.duration(name); tr = d.tracks(name)
    n = max(2, int(round(T * fps)))
    ts = np.linspace(0, T, n + 1)[:-1]
    rows = []
    for t in ts:
        W = d.world(d.sample(tr, t))
        rows.append(dict(t=float(t), lean=lean_deg(W, d),
                         neck_lean=float(np.degrees(np.arctan2(*(((d.pos(W, 'neck') - d.pos(W, 'hips')) @ FWD, (d.pos(W, 'neck') - d.pos(W, 'hips')) @ UP))))),
                         hipy=float(d.pos(W, 'hips')[1]),
                         fl=d.pos(W, 'foot.L').tolist(), fr=d.pos(W, 'foot.R').tolist(),
                         hl=float((d.pos(W, 'hand.L') - d.pos(W, 'hips')) @ FWD), hr=float((d.pos(W, 'hand.R') - d.pos(W, 'hips')) @ FWD)))
    lean = np.array([r['lean'] for r in rows])
    hipy = np.array([r['hipy'] for r in rows])
    # steps per cycle = number of hip-height minima (1 bob per step) over the loop
    hy = hipy - hipy.mean()
    mins = sum(1 for i in range(len(hy)) if hy[i] < hy[i - 1] and hy[i] <= hy[(i + 1) % len(hy)])
    flz = np.array([r['fl'][2] for r in rows]); frz = np.array([r['fr'][2] for r in rows])
    # foot crossings (passing frames) = sign changes of (L - R) z
    dz = flz - frz; cross = sum(1 for i in range(len(dz)) if np.sign(dz[i]) != np.sign(dz[i - 1]))
    hl = np.array([r['hl'] for r in rows]); hr = np.array([r['hr'] for r in rows])
    return dict(clip=name, duration=T, frames60=n, steps_per_cycle_bob=mins, steps_per_cycle_cross=cross,
                steps_per_s=cross / T, lean_head_hip_median=float(np.median(lean)), lean_min=float(lean.min()), lean_max=float(lean.max()),
                neck_hip_median=float(np.median([r['neck_lean'] for r in rows])),
                hip_bob_cm=float((hipy.max() - hipy.min()) * 100), hip_mean_m=float(hipy.mean()),
                hand_swing_L_cm=float((hl.max() - hl.min()) * 100), hand_swing_R_cm=float((hr.max() - hr.min()) * 100),
                foot_z_range_cm=float((flz.max() - flz.min()) * 100))


if __name__ == '__main__':
    a = sys.argv[1:]; out = None
    if '--json' in a:
        i = a.index('--json'); out = a[i + 1]; a = a[:i] + a[i + 2:]
    d = Doc(a[0]); res = [measure(d, c) for c in a[1:]]
    for r in res: print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}))
    if out: json.dump(res, open(out, 'w'), indent=1)
