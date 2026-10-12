"""Planted-foot speed (natural ground speed) and foot slide per plant of a looping in-place clip in a glTF (hero skeleton).
Fan homage project; not official Marvel/Sony/Insomniac.   python3 foot_speed.py GLB clip [clip ...] [--speed m/s] [--json OUT]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ganim import Doc


def analyse(d, clip, speed=None, fps=120):
    T = d.duration(clip); tr = d.tracks(clip)
    ts = np.arange(int(round(T * fps))) / fps
    P = np.array([[d.pos(d.world(d.sample(tr, t)), f) for f in ('foot.L', 'foot.R')] for t in ts])
    y, z = P[..., 1], P[..., 2]
    dzf = np.roll(z, -1, 0) - z
    st = (y < y.min(0) + 0.012) & (dzf <= 0.0005)
    segs = []
    n = len(ts)
    for k in range(2):
        m = st[:, k]
        if m.all() or not m.any(): continue
        r = int(np.argmin(m)); mm = np.roll(m, -r); zz = np.roll(z[:, k], -r)
        idx = np.where(mm)[0]
        for run in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1):
            if len(run) > 2: segs.append((run / fps, zz[run]))
    v = float(np.median([-(zz[-1] - zz[0]) / (tt[-1] - tt[0]) for tt, zz in segs]))
    vv = v if speed is None else speed
    slide = [float((zz + vv * tt).max() - (zz + vv * tt).min()) for tt, zz in segs]
    return dict(clip=clip, duration=round(T, 4), natural_speed_mps=round(v, 3), eval_speed_mps=round(vv, 3),
                foot_slide_per_plant_cm_max=round(100 * max(slide), 2), foot_slide_per_plant_cm_median=round(100 * float(np.median(slide)), 2), plants=len(slide))


if __name__ == '__main__':
    a = sys.argv[1:]; sp = None; out = None
    if '--speed' in a: i = a.index('--speed'); sp = float(a[i + 1]); a = a[:i] + a[i + 2:]
    if '--json' in a: i = a.index('--json'); out = a[i + 1]; a = a[:i] + a[i + 2:]
    d = Doc(a[0]); res = [analyse(d, c, sp) for c in a[1:]]
    for r in res: print(json.dumps(r))
    if out: json.dump(res, open(out, 'w'), indent=1)
