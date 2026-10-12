"""Crowd walk clips (people.bin baked matrices): time-warp so the planted foot moves at a CONSTANT speed, natural ground speed,
and foot slide per plant for a walker moving at that speed. Fan homage project; not official Marvel/Sony/Insomniac.

The shipped in-place walks move the stance ankle non-uniformly (slow after heel strike, fast mid-stance): a walker moving at any
constant speed skates up to ~22 cm per plant. warp_times() re-times the keys (same poses, same loop length) so that the planted
ankle's backward displacement is proportional to time; citizen_rig.build() keys the FBX actions at these times.
  python3 tools/ue_char/eval/crowd_gait.py [--json OUT]"""
import json, sys, os
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
NPC = os.path.join(ROOT, 'public/assets/city/npc')
CLIPS = ['walk', 'walkF', 'walkBrisk', 'walkStroll', 'walkOld']


def load():
    p = json.load(open(os.path.join(NPC, 'people.json')))
    A = np.frombuffer(open(os.path.join(NPC, 'people.bin'), 'rb').read(), np.float32, p['frames'] * p['nb'] * 12, p['anim']).reshape(p['frames'], p['nb'], 3, 4)
    return p, A


def feet_pos(p, A, c):
    cl = p['clips'][c]; n = cl['len']
    feet = [i for i, b in enumerate(p['bones']) if b['name'] in ('footL', 'footR')]
    return np.array([[A[cl['row'] + f, b] @ np.r_[p['bones'][b]['head'], 1.0] for b in feet] for f in range(n)])


def stance(y, z):
    """planted: ankle within 1.2 cm of its lowest point AND not moving forward (excludes the end of the swing)."""
    dzf = np.roll(z, -1, 0) - z
    return (y < y.min(0) + 0.012) & (dzf <= 0.002)


def warp_times(p, A, c, blend=0.85):
    """new key time (in frames, float, 0..n) for each original frame 0..n (n = loop end = frame 0). blend<1 keeps a little of
    the original timing so the swing never gets too fast."""
    pos = feet_pos(p, A, c); n = len(pos)
    y, z = pos[..., 1], pos[..., 2]
    zz = np.concatenate([z, z[:1]]); yy = np.concatenate([y, y[:1]])
    dz = -(zz[1:] - zz[:-1])                                  # backward displacement per interval, per foot
    low = stance(y, z)                                        # planted during the interval i -> i+1
    d = np.where(low, np.maximum(dz, 0), np.nan)
    di = np.nanmean(np.where(low.any(1, keepdims=True), d, np.nan), 1)
    di = np.where(np.isfinite(di), di, np.nanmean(di))
    di = np.maximum(di, 0.25 * np.nanmean(di))
    w = blend * di / di.sum() + (1 - blend) / n
    return np.concatenate([[0], np.cumsum(w)]) * n


def _runs(m, n):
    idx = np.where(m)[0]
    runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    if len(runs) > 1 and m[0] and m[-1]:                         # stance wraps the loop seam: join (indices > n continue the next loop)
        runs = [np.concatenate([runs[-1], runs[0] + n])] + runs[1:-1]
    return [r for r in runs if len(r) >= 2]


def measure(p, A, c, times=None):
    cl = p['clips'][c]; fps = cl['fps']
    pos = feet_pos(p, A, c); n = len(pos)
    t = (np.arange(n + 1) if times is None else np.asarray(times, float)) / fps     # key time of original frame 0..n (n == 0)
    T = t[-1]
    y, z = pos[..., 1], pos[..., 2]
    low = stance(y, z)
    at = lambda i: (t[i] if i < n else t[i - n] + T)
    segs = []
    for k in range(2):
        for r in _runs(low[:, k], n):
            tt = np.array([at(i) for i in r]); zz = np.array([z[i % n, k] for i in r])
            segs.append((tt, zz))
    v = float(np.median([-(zz[-1] - zz[0]) / (tt[-1] - tt[0]) for tt, zz in segs]))
    slide = [float((zz + v * tt).max() - (zz + v * tt).min()) for tt, zz in segs]
    return dict(frames=n, period_s=round(float(T), 4), natural_speed_mps=round(v, 4), foot_slide_per_plant_cm_max=round(100 * max(slide), 2),
                foot_slide_per_plant_cm_median=round(100 * float(np.median(slide)), 2), plants=len(slide), cadence_steps_per_s=round(2 / T, 3))


def main():
    p, A = load()
    out = {}
    for c in CLIPS:
        out[c] = {'original': measure(p, A, c), 'warped': measure(p, A, c, warp_times(p, A, c))}
    print(json.dumps(out, indent=1))
    if '--json' in sys.argv: json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)


if __name__ == '__main__':
    main()
