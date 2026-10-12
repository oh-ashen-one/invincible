#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: per-window statistics of perf_route CSVs (csv.csv or csv.csv.gz): frame p50 / p95 and the mean of chosen GPU passes over
the first N / middle / last N frames of the route window (default N = 600 of 1800). Answers "where in the route does the frame go over budget".
usage: windows.py <result dir or csv> [...] [--n 600] [--md out.md] [--json out.json] [--passes GPU/VolumetricCloud,GPU/NaniteVisBuffer,...]
A dir argument is a perf_route session dir: every <config>/csv.csv[.gz] under it is read."""
import argparse, csv, glob, gzip, json, os, statistics

PASSES = ['GPU/VolumetricCloud', 'GPU/VolCloudReconstruction', 'GPU/VolCloudComposeOverScene', 'GPU/NaniteVisBuffer', 'GPU/NaniteBasePass',
          'GPU/ShadowDepths', 'GPU/Lumen', 'GPU/LumenSceneLighting', 'GPU/LumenReflections', 'GPU/DiffuseIndirectAndAO', 'GPU/Postprocessing',
          'GPU/RayTracingScene', 'GPU/RayTracingGeometry', 'GPU/BasePass', 'GPU/Prepass', 'GPU/Translucency']


def pct(a, p):
    a = sorted(a)
    if not a: return None
    i = (len(a) - 1) * p / 100.0; lo = int(i); hi = min(lo + 1, len(a) - 1)
    return a[lo] + (a[hi] - a[lo]) * (i - lo)


def load(path):
    op = gzip.open if path.endswith('.gz') else open
    rows = list(csv.reader(op(path, 'rt')))
    hdr = rows[0]; n = len(hdr) - 1
    data = []
    for r in rows[1:]:
        if len(r) < n + 1 or not r: continue
        try: data.append([float(x) if x != '' else 0.0 for x in r[1:n + 1]])
        except ValueError: continue
    idx = {h: i - 1 for i, h in enumerate(hdr) if i > 0}
    return hdr, idx, data


def window(idx, data, lo, hi, passes):
    ft = [r[idx['FrameTime']] for r in data[lo:hi] if r[idx['FrameTime']] > 0]
    out = {'frames': len(ft), 'p50': pct(ft, 50), 'p95': pct(ft, 95), 'mean': statistics.mean(ft) if ft else None, 'over_18_18': sum(1 for x in ft if x > 18.18)}
    ps = {}
    for p in passes:
        if p in idx: ps[p.split('/', 1)[1]] = statistics.mean([r[idx[p]] for r in data[lo:hi]]) if data[lo:hi] else None
    out['passes'] = ps
    return out


def analyse(path, n, passes):
    hdr, idx, data = load(path)
    ft = [r[idx['FrameTime']] for r in data]
    N = len(data)
    w = {'all': window(idx, data, 0, N, passes), 'first': window(idx, data, 0, n, passes), 'mid': window(idx, data, n, max(n, N - n), passes),
         'last': window(idx, data, max(0, N - n), N, passes)}
    cl = ['GPU/VolumetricCloud', 'GPU/VolCloudReconstruction', 'GPU/VolCloudComposeOverScene']
    for k, (lo, hi) in {'first': (0, n), 'last': (max(0, N - n), N)}.items():
        w[k]['cloud_all_passes'] = sum(statistics.mean([r[idx[c]] for r in data[lo:hi]]) for c in cl if c in idx and data[lo:hi])
    return {'csv': path, 'frames': N, 'windows': w}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('paths', nargs='+'); ap.add_argument('--n', type=int, default=600)
    ap.add_argument('--md'); ap.add_argument('--json'); ap.add_argument('--passes', default=','.join(PASSES))
    a = ap.parse_args(); passes = a.passes.split(',')
    files = []
    for p in a.paths:
        if os.path.isdir(p): files += sorted(glob.glob(os.path.join(p, '*', 'csv.csv*')) + glob.glob(os.path.join(p, 'csv.csv*')))
        else: files.append(p)
    res = {}
    for f in files:
        name = os.path.basename(os.path.dirname(f)) or f
        try: res[name] = analyse(f, a.n, passes)
        except Exception as e: res[name] = {'csv': f, 'error': str(e)}
    L = ['| config | frames | p50 all | p95 all | p50 first%d | p95 first | p50 last%d | p95 last | >18.18 ms last | cloud last (VolumetricCloud) | cloud last (3 passes) | cloud first | NaniteVisBuffer first / last |' % (a.n, a.n), '|' + '---|' * 13]
    f2 = lambda x: ('%.2f' % x) if isinstance(x, (int, float)) else 'n/a'
    for k, v in res.items():
        if 'error' in v: L.append('| %s | error %s |' % (k, v['error'])); continue
        w = v['windows']
        L.append('| %s | %d | %s | %s | %s | %s | %s | %s | %d | %s | %s | %s | %s / %s |' % (
            k, v['frames'], f2(w['all']['p50']), f2(w['all']['p95']), f2(w['first']['p50']), f2(w['first']['p95']), f2(w['last']['p50']), f2(w['last']['p95']),
            w['last']['over_18_18'], f2(w['last']['passes'].get('VolumetricCloud')), f2(w['last'].get('cloud_all_passes')), f2(w['first']['passes'].get('VolumetricCloud')),
            f2(w['first']['passes'].get('NaniteVisBuffer')), f2(w['last']['passes'].get('NaniteVisBuffer'))))
    txt = '\n'.join(L) + '\n'
    print(txt)
    if a.md: open(a.md, 'w').write(txt)
    if a.json: json.dump(res, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
