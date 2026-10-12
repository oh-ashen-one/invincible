#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 11 UV-seam check of the generated hero suits (spec CH18 / PLAN section 4 Skins: 'no seam > 40 px at 4K').

A UV seam is a mesh edge whose two triangles share the 3D edge but use different UV islands.  Along every such edge the base colour is sampled on BOTH sides
(bilinear, exactly on the edge) every 0.5 mm of surface; where the two sides differ by more than DE (CIE Lab, default 18) the point is 'open'.  A seam
RUN is a stretch of consecutive open points; its length is converted to screen pixels at the CH1 ground framing (hero 0.55 of a 2160 px frame over 1.8 m = 660 px/m;
PX_PER_M) and the worst run per suit is reported (limit 40 px).  Also writes the share of seam length that is open.

  python3 tools/ue_char/eval/suit_seams.py MAPS_DIR OUT.json [--ids a,b] [--de 18] [--px-per-m 660]
"""
import sys, os, json
import numpy as np
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'suit8')); sys.path.insert(0, os.path.join(HERE, '..'))
import meshio  # noqa: E402


def seam_pairs(m):
    P, UV, F = m['P'], m['UV'], m['F']
    key = lambda a, b: tuple(sorted((tuple(np.round(P[a], 5)), tuple(np.round(P[b], 5)))))
    d = {}
    for fi, f in enumerate(F):
        for k in range(3):
            a, b = f[k], f[(k + 1) % 3]
            d.setdefault(key(a, b), []).append((a, b))
    pairs = []
    for k, v in d.items():
        if len(v) != 2: continue
        (a1, b1), (a2, b2) = v
        pa1 = tuple(np.round(P[a1], 5))
        # order the second edge so that its first vertex sits at the same 3D point as a1
        if tuple(np.round(P[a2], 5)) != pa1: a2, b2 = b2, a2
        u1a, u1b, u2a, u2b = UV[a1], UV[b1], UV[a2], UV[b2]
        if np.abs(u1a - u2a).max() < 1e-4 and np.abs(u1b - u2b).max() < 1e-4: continue   # same island: not a seam
        L = float(np.linalg.norm(P[b1] - P[a1]))
        if L < 1e-5: continue
        pairs.append((u1a, u1b, u2a, u2b, L))
    return pairs


def sample(img, uv):
    h, w = img.shape[:2]
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001); y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0 = x.astype(int); y0 = y.astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx) * (1 - fy) + (img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx) * fy


def check(path, pairs, de_thr, px_per_m):
    im = cv2.imread(path)[..., ::-1].astype(np.float32) / 255
    lab = cv2.cvtColor(im, cv2.COLOR_RGB2LAB)
    worst = 0.0; nruns40 = 0; open_len = 0.0; tot_len = 0.0; worst_at = None; runs = []
    for (u1a, u1b, u2a, u2b, L) in pairs:
        n = max(2, int(L / 0.0005))
        t = np.linspace(0, 1, n)[:, None]
        s1 = sample(lab, u1a + (u1b - u1a) * t); s2 = sample(lab, u2a + (u2b - u2a) * t)
        de = np.linalg.norm(s1 - s2, axis=1)
        opn = de > de_thr
        tot_len += L; open_len += L * opn.mean()
        if not opn.any(): continue
        # runs of consecutive open points, in metres -> pixels
        d = np.diff(np.concatenate([[0], opn.astype(int), [0]]))
        for a, b in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]):
            run_px = (b - a) / n * L * px_per_m
            if run_px > 1.0: runs.append(run_px)
            if run_px > worst: worst = run_px; worst_at = [float(x) for x in u1a]
            if run_px > 40: nruns40 += 1
    return dict(worst_run_px=round(worst, 1), runs_gt_40px=nruns40, runs_gt_10px=int(sum(1 for r in runs if r > 10)), open_share=round(open_len / max(tot_len, 1e-9), 4),
                seam_len_m=round(tot_len, 2), worst_uv=worst_at)


def main():
    maps, out = sys.argv[1], sys.argv[2]
    a = sys.argv
    de = float(a[a.index('--de') + 1]) if '--de' in a else 18.0
    ppm = float(a[a.index('--px-per-m') + 1]) if '--px-per-m' in a else 660.0
    ids = a[a.index('--ids') + 1].split(',') if '--ids' in a else [s['id'] for s in json.load(open(os.path.join(HERE, '..', 'suits', 'suits.json')))['suits']]
    m = meshio.load_body()
    pairs = seam_pairs(m)
    print('seam edges', len(pairs), 'total %.1f m' % sum(p[4] for p in pairs))
    res = {}
    for sid in ids:
        p = '%s/%s_basecolor.png' % (maps, sid)
        if not os.path.exists(p): print('skip', sid); continue
        res[sid] = check(p, pairs, de, ppm)
        print('%-8s worst run %6.1f px   runs > 40 px: %d   runs > 10 px: %d   open share %.4f' % ((sid,) + tuple(res[sid][k] for k in ('worst_run_px', 'runs_gt_40px', 'runs_gt_10px', 'open_share'))))
    json.dump(dict(de_threshold=de, px_per_m=ppm, seam_edges=len(pairs), suits=res, pass_all=all(r['runs_gt_40px'] == 0 for r in res.values())), open(out, 'w'), indent=1)
    print('PASS (no run > 40 px)' if all(r['runs_gt_40px'] == 0 for r in res.values()) else 'FAIL')


if __name__ == '__main__':
    main()
