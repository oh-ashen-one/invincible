# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: search a crowd layout (lane offset dy + start x0 per walker) whose STRAIGHT-LINE paths never bring two walkers closer than MINSEP
(so the runtime avoidance has nothing to do in the shots), keeps the two-way flow (right-hand traffic: the +X stream on the +Y = camera side of
each lane pair) and a busy tracking / wide frame.  Both director shots are checked: tracking 8 s (camera follows x = 110 t) and wide 6 s
(restart at LineStart).  Output: the chosen table as JSON, printed as the python literal build_characters.py contains.

  python3 tools/ue_char/crowd/layout_search.py [--seed 1] [--iters 6000] [--minsep 115]
"""
import sys, json, math
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import avoid_sim as A

seed = 1; iters = 6000; MINSEP = 115.0
a = sys.argv[1:]
if '--seed' in a: seed = int(a[a.index('--seed') + 1])
if '--iters' in a: iters = int(a[a.index('--iters') + 1])
if '--minsep' in a: MINSEP = float(a[a.index('--minsep') + 1])
FLIP = '--flip' in a
DMIN = float(a[a.index('--dmin') + 1]) if '--dmin' in a else 11.0
OVW = float(a[a.index('--ovw') + 1]) if '--ovw' in a else 1.0
rng = np.random.default_rng(seed)

NAMES = [c for c, *_ in A.MID_R6 + A.NEAR_R6]
DIR0 = {c: d for c, _, _, d in A.MID_R6 + A.NEAR_R6}
X00 = {c: x for c, _, x, _ in A.MID_R6 + A.NEAR_R6}
NEAR = [c for c, *_ in A.NEAR_R6]
SPD = np.array([A.SPEED[A.STYLE[c]] for c in NAMES])
DIRS0 = np.array([DIR0[c] for c in NAMES], float)
DIRS = DIRS0.copy()
isnear = np.array([c in NEAR for c in NAMES])
TA = np.arange(0, 8.0, 1 / 30.0); TB = np.arange(0, 6.0, 1 / 30.0)
TAV = np.arange(0, 10.0, 1 / 30.0); TBV = np.arange(0, 8.0, 1 / 30.0)   # separation is checked 2 s beyond each shot (the avoidance look-ahead)
FOV_T = 64.0; CAMD_T = 1150.0; CAMH = 45.0   # tracking: distance to the tracked point on the mid lane centre line y = CY5
CAM_W = (-1400.0, A.CY5 + 420.0)             # wide camera


TAN_T = math.tan(math.radians(FOV_T / 2)); HALFW = 45.0          # silhouette half width incl. arms / stride, cm
WIDE_FOV = 50.0; WIDE_AIM = (500.0, A.CY5)


def screen_overlap(dy, x0, dirs=None):
    """(mean visible count, mean near count, fraction of frames with >= 1 overlapping pair of screen silhouettes, mean overlapping pairs,
    near-near pair-frames per frame, near-any pair-frames per frame) in the tracking shot"""
    dirs = DIRS if dirs is None else dirs
    Xc = x0[:, None] + (dirs * SPD)[:, None] * TA[None, :] - 110.0 * TA[None, :]            # x relative to the camera
    depth = (CAMD_T - dy)[:, None] * np.ones_like(Xc)
    u = Xc / (depth * TAN_T); hw = HALFW / (depth * TAN_T)
    vis = (np.abs(u) < 1.0)
    lo, hi = u - hw, u + hw
    ov = np.zeros(len(TA), bool); npair = 0; nn = 0; nm = 0
    n = len(dy)
    for i in range(n):
        for j in range(i + 1, n):
            o = vis[i] & vis[j] & (lo[i] < hi[j]) & (lo[j] < hi[i])
            ov |= o; npair += int(o.sum())
            if isnear[i] and isnear[j]: nn += int(o.sum())
            elif isnear[i] or isnear[j]: nm += int(o.sum())
    return vis.sum(0).mean(), (vis & isnear[:, None]).sum(0).mean(), float(ov.mean()), npair / len(TA), nn / len(TA), nm / len(TA)


def wide_count(dy, x0, dirs=None):
    dirs = DIRS if dirs is None else dirs
    cam = np.array(CAM_W); aim = np.array(WIDE_AIM); f = aim - cam; yaw0 = math.atan2(f[1], f[0])
    X = x0[:, None] + (dirs * SPD)[:, None] * TB[None, :]; Y = (A.CY5 + dy)[:, None] * np.ones_like(X)
    ang = np.arctan2(Y - cam[1], X - cam[0]) - yaw0
    return (np.abs(ang) < math.radians(WIDE_FOV / 2 - 3)).sum(0).mean()


def cost(dy, x0, dirs):
    """violations (pair-frames below MINSEP) + soft terms"""
    v = 0.0; minall = 1e9
    for T in (TAV, TBV):
        X = x0[:, None] + (dirs * SPD)[:, None] * T[None, :]              # (n, T)
        dx = X[:, None, :] - X[None, :, :]                                # (n, n, T)
        dyy = (dy[:, None] - dy[None, :])[:, :, None]
        d = np.sqrt(dx * dx + dyy * dyy)
        iu = np.triu_indices(len(dy), 1)
        dd = d[iu]                                                        # (pairs, T)
        v += float(np.maximum(MINSEP - dd, 0.0).sum()) / 30.0
        minall = min(minall, float(dd.min()))
    dens, near_vis, ovf, npair, nn, nm = screen_overlap(dy, x0, dirs)
    return v, minall, dens, near_vis, ovf, npair, wide_count(dy, x0, dirs), nn, nm


def penalty(dy, x0, dirs):
    v, mn, dens, nv, ovf, npair, wc, nn, nm = cost(dy, x0, dirs)
    p = v * 5.0
    p += max(0.0, DMIN - dens) * 8.0                                     # want >= DMIN people in the tracking frame on average
    p += max(0.0, 3.0 - nv) * 8.0                                        # want >= 3 near-lane walkers in frame
    p += max(0.0, 13.0 - wc) * 4.0                                       # wide shot
    p += nn * 25.0 * OVW + nm * 2.0 * OVW + (npair - nn - nm) * 1.0 * OVW  # silhouette overlaps: near-near (the big ones) hurt most
    return p, (v, mn, dens, nv, ovf, npair, wc, nn, nm)


def lo_hi(c, d):
    return (690, 820) if c in NEAR and d > 0 else ((560, 670) if c in NEAR else (-340, 340))


dy = np.array([dd for c, dd, _, _ in A.MID_R6 + A.NEAR_R6], float)
x0 = np.array([X00[c] for c in NAMES], float)
dirs = DIRS0.copy()
best = (1e18, None)
cur_p, cur_m = penalty(dy, x0, dirs)
T0 = 30.0
for it in range(iters):
    i = rng.integers(len(NAMES)); c = NAMES[i]
    ndy = dy.copy(); nx0 = x0.copy(); nd = dirs.copy()
    r = rng.random()
    if r < 0.5:
        lo, hi = lo_hi(c, nd[i]); ndy[i] = np.clip(round((dy[i] + rng.normal(0, 60)) / 10) * 10, lo, hi)
    elif r < 0.93:
        nx0[i] = np.clip(round((x0[i] + rng.normal(0, 250)) / 10) * 10, X00[c] - 1600, X00[c] + 1600)
    elif FLIP and c in NEAR:
        nd[i] = -nd[i]; lo, hi = lo_hi(c, nd[i]); ndy[i] = np.clip(ndy[i], lo, hi)
    p, m = penalty(ndy, nx0, nd)
    temp = T0 * (1 - it / iters) + 0.05
    if p < cur_p or rng.random() < math.exp(-(p - cur_p) / temp):
        dy, x0, dirs, cur_p, cur_m = ndy, nx0, nd, p, m
        if p < best[0]: best = (p, (dy.copy(), x0.copy(), dirs.copy(), m))
p, (dy, x0, dirs, m) = best
print('penalty %.1f  violations %.2f  min pair distance %.1f cm  tracking density %.2f  near in frame %.2f  frames with a screen overlap %.2f  mean overlapping pairs %.2f  wide count %.2f  near-near %.2f near-any %.2f' % ((p,) + m))
rows = [(c, int(dy[i]), int(x0[i]), int(dirs[i])) for i, c in enumerate(NAMES)]
mid = [r for r in rows if r[0] not in NEAR]; near = [r for r in rows if r[0] in NEAR]
print('MID =', mid); print('NEAR =', near)
json.dump(dict(mid=mid, near=near, minsep=MINSEP, min_pair_cm=m[1], density=m[2], overlap_frames=m[4], wide=m[6], near_near=m[7], near_any=m[8]), open('/Users/midir/sm2-n1/_scratch/characters/r7/layout_b_seed%d.json' % seed, 'w'))
