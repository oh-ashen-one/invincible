#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17 line-step instrument (critic r16 secondary 2: "every 40 px run of a sash or groove edge stays within 4 px of its line").

  python3 tools/ue_char/suits/line_step_r17.py CHEST.png [--out OVERLAY.jpg] [--json OUT.json] [--box x0,y0,x1,y1] [--gate 4] [--run 40] [--k 6]
  python3 tools/ue_char/suits/line_step_r17.py --selftest        (the r16 chest stills: the Ash shelf and the Verdant step must be found)

How: the chest box is segmented into flat colour regions (k-means in Lab on a sample, nearest centre per pixel, 3x3 opening against the stitching dashes); every region of >= 12000 px
gives its boundary (cv2.findContours) as a polygon (approxPolyDP eps 1.2 px).  A STRAIGHT RUN is a polygon edge >= RUN px long.  A JOG is the pattern run / short connector (3 - 90 px,
a different direction) / run, where the two runs are near-parallel (< 8 deg) and the second run's line lies GATE .. 70 px sideways of the first run's line (measured at the connector):
the edge is not within GATE px of ONE line over the two runs (the edge steps sideways by that much).  Edge steps below GATE are inside the budget.  Also reported: the longest
straight run per region and the number of runs.  PASS = no jog.
Limits: colour regions only (a groove cord of the same colour as the cloth on both sides, with no colour change, is not a region boundary; cords here are darker than the cloth, so the
sash border and the cord lines on the panels that segment as their own cluster are read; thin cords below the opening size are not).  The contour reads the edge of the colour change.
"""
import sys, json, math
import numpy as np, cv2


def regions(crop, k=6):
    small = cv2.resize(crop, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(cv2.GaussianBlur(crop, (0, 0), 1.5), cv2.COLOR_BGR2LAB)
    rs = np.random.RandomState(1)
    flat = cv2.cvtColor(cv2.GaussianBlur(small, (0, 0), 1.2), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    sel = flat[rs.choice(len(flat), min(200000, len(flat)), replace=False)]
    _, _, cen = cv2.kmeans(sel, k, None, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 2, cv2.KMEANS_PP_CENTERS)
    d = np.stack([np.linalg.norm(lab.astype(np.float32) - c[None, None, :], axis=2) for c in cen], 0)
    return np.argmin(d, 0).astype(np.uint8), cen


def poly_runs(cnt, eps, run):
    ap = cv2.approxPolyDP(cnt, eps, True).reshape(-1, 2).astype(float)
    n = len(ap)
    if n < 4: return []
    edges = []
    for i in range(n):
        p, q = ap[i], ap[(i + 1) % n]
        L = float(np.linalg.norm(q - p))
        edges.append((p, q, L, (q - p) / max(L, 1e-9)))
    return edges


def jogs(edges, gate, run):
    out = []
    n = len(edges)
    for i in range(n):
        a = edges[i]
        if a[2] < run: continue
        tot = 0.0; conn = []; b = None
        for k in range(1, 5):               # up to 4 polygon edges between two straight runs (a shelf is often 2 - 3 polygon edges)
            c = edges[(i + k) % n]
            ca = math.degrees(math.acos(max(-1.0, min(1.0, float(a[3] @ c[3])))))
            if c[2] >= run and ca <= 8.0 and conn: b = c; break           # the second run: long, SAME direction (an antiparallel pair is the two sides of a thin band)
            if tot + c[2] > 110.0: break
            conn.append(c); tot += c[2]
        if b is None or tot < 3.0: continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(a[3] @ b[3])))))
        nrm = np.array([-a[3][1], a[3][0]])
        off = abs(float((b[0] - a[1]) @ nrm))                 # b's start point against a's infinite line
        mid = (conn[0][0] + conn[-1][1]) / 2
        if gate < off <= 70.0:
            out.append(dict(step=round(off, 1), x=float(mid[0]), y=float(mid[1]), run_a=int(a[2]), run_b=int(b[2]), connector=int(tot), angle=round(ang, 1)))
    return out


def analyse(img, box, gate=4.0, run=40, k=6, min_area=12000):
    x0, y0, x1, y1 = box
    crop = img[y0:y1, x0:x1]
    lab, cen = regions(crop, k)
    ev = []; runs = 0; longest = 0.0
    kern = np.ones((3, 3), np.uint8)
    for c in range(k):
        m = (lab == c).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kern)
        n, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        for r in range(1, n):
            if st[r, cv2.CC_STAT_AREA] < min_area: continue
            mm = (cc == r).astype(np.uint8)
            cnts, _ = cv2.findContours(mm, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            for cnt in cnts:
                if len(cnt) < 200: continue
                edges = poly_runs(cnt, 1.2, run)
                runs += sum(1 for e in edges if e[2] >= run); longest = max([longest] + [e[2] for e in edges])
                for j in jogs(edges, gate, run):
                    j['x'] = int(j['x'] + x0); j['y'] = int(j['y'] + y0); ev.append(j)
    # de-duplicate (the same jog is the boundary of two neighbouring regions): merge events within 60 px
    ev.sort(key=lambda t: -t['step']); keep = []
    for e in ev:
        if all(math.hypot(e['x'] - f['x'], e['y'] - f['y']) > 60 for f in keep): keep.append(e)
    return dict(regions=k, straight_runs=runs, longest_run_px=int(longest), max_step_px=(keep[0]['step'] if keep else 0.0), n_jogs=len(keep), jogs=keep)


def main():
    if '--selftest' in sys.argv:
        for sid in ('ash', 'verdant', 'cinder', 'saffron'):
            p = 'docs/night1/characters/round-16/stills/skin_%s_chest_4k.jpg' % sid
            r = analyse(cv2.imread(p), [691, 259, 3148, 2095])
            print(sid, {k: v for k, v in r.items() if k != 'jogs'}, r['jogs'][:6])
        return
    p = sys.argv[1]
    img = cv2.imread(p, cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    gate = float(sys.argv[sys.argv.index('--gate') + 1]) if '--gate' in sys.argv else 4.0
    run = int(sys.argv[sys.argv.index('--run') + 1]) if '--run' in sys.argv else 40
    k = int(sys.argv[sys.argv.index('--k') + 1]) if '--k' in sys.argv else 6
    box = [int(v) for v in sys.argv[sys.argv.index('--box') + 1].split(',')] if '--box' in sys.argv else [int(W * 0.18), int(H * 0.12), int(W * 0.82), int(H * 0.97)]
    res = analyse(img, box, gate, run, k)
    res.update(image=p, gate=gate, run=run, box=box); res['pass'] = res['n_jogs'] == 0
    if '--out' in sys.argv:
        vis = img.copy()
        for t in res['jogs'][:40]:
            cv2.circle(vis, (t['x'], t['y']), 40, (0, 0, 255), 3); cv2.putText(vis, '%.1f' % t['step'], (t['x'] + 44, t['y']), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.imwrite(sys.argv[sys.argv.index('--out') + 1], cv2.resize(vis, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
    if '--json' in sys.argv: json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    print(json.dumps({k_: v for k_, v in res.items() if k_ != 'jogs'}), '\n jogs:', res['jogs'][:8])


if __name__ == '__main__':
    main()
