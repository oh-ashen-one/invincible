#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: attributed probe table. Reads every <dir>/*/result.json written by perf_route.py (any number of lock sessions), groups
the configs by screen percentage, and prints for each probe the delta vs the base config of the same SP (name 'base<SP>' by default):
frame avg / p50 / p95, GPU ms, render-thread ms, and the GPU passes that moved most. Also prints the gpu_slot.sh sidecar verdict
of the session each run belongs to. usage: attribute.py <session_dir> [<session_dir> ...] [--md out.md] [--json out.json]"""
import argparse, glob, json, os


def load(dirs):
    runs = {}
    for d in dirs:
        side = {}
        for sj in glob.glob(os.path.join(d, 'perf_gpu*.json')):
            try: side = json.load(open(sj))
            except Exception: pass
        for rp in sorted(glob.glob(os.path.join(d, '*', 'result.json'))):
            r = json.load(open(rp))
            r['_session'] = os.path.basename(os.path.abspath(d))
            r['_lock'] = {k: side.get(k) for k in ('perf_valid', 'exclusive', 'contaminated', 'util_before', 'util_after', 'util_during', 'instances_before')}
            runs[r['config']] = r
    return runs


def g(r, *ks):
    x = r
    for k in ks:
        x = (x or {}).get(k) if isinstance(x, dict) else None
    return x


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('dirs', nargs='+'); ap.add_argument('--md'); ap.add_argument('--json')
    a = ap.parse_args()
    runs = load(a.dirs)
    rows = []
    for name, r in runs.items():
        sp = r['screen_percentage']
        base = runs.get('base%s' % sp)
        c, cb = r.get('csv') or {}, (base or {}).get('csv') or {}
        row = {'config': name, 'sp': sp, 'session': r['_session'], 'perf_valid': r['_lock'].get('perf_valid'),
               'internal': '%sx%s' % (g(r, 'wh_perf', 'internal_w'), g(r, 'wh_perf', 'internal_h')), 'cvars': r.get('cvars'),
               'avg': c.get('avg_ms'), 'p50': c.get('p50_ms'), 'p95': c.get('p95_ms'), 'gpu': g(c, 'gpu_ms', 'avg'), 'rt': g(c, 'render_thread_ms', 'avg'),
               'frames': c.get('csv_frames'), 'error': r.get('error')}
        if base and name != 'base%s' % sp and c and cb:
            for k, kk in (('avg', 'avg_ms'), ('p50', 'p50_ms'), ('p95', 'p95_ms')): row['d_' + k] = (cb.get(kk) or 0) - (c.get(kk) or 0)
            row['d_gpu'] = (g(cb, 'gpu_ms', 'avg') or 0) - (g(c, 'gpu_ms', 'avg') or 0)
            pa, pb = c.get('gpu_passes_avg_ms') or {}, cb.get('gpu_passes_avg_ms') or {}
            dd = {k.replace('GPU/', ''): round(pb.get(k, 0) - pa.get(k, 0), 2) for k in set(pa) | set(pb)}
            row['passes_saved'] = dict(sorted(dd.items(), key=lambda kv: -abs(kv[1]))[:5])
        rows.append(row)
    rows.sort(key=lambda r: (int(r['sp']), not r['config'].startswith('base'), r['config']))
    f = lambda x, n=2: ('%.*f' % (n, x)) if isinstance(x, (int, float)) else 'n/a'
    L = ['| config | SP (internal) | p50 ms (fps) | p95 ms (fps) | GPU ms | saved vs base: p50 / p95 / GPU ms | biggest pass changes (ms saved) | lock |',
         '|---|---|---|---|---|---|---|---|']
    for r in rows:
        fps = lambda ms: f(1000.0 / ms, 1) if ms else 'n/a'
        sv = ('%s / %s / %s' % (f(r.get('d_p50')), f(r.get('d_p95')), f(r.get('d_gpu')))) if 'd_gpu' in r else ('baseline' if r['config'].startswith('base') else '-')
        ps = ', '.join('%s %+.2f' % kv for kv in (r.get('passes_saved') or {}).items())
        L.append('| %s | %s (%s) | %s (%s) | %s (%s) | %s | %s | %s | %s %s |' % (
            r['config'], r['sp'], r['internal'], f(r['p50']), fps(r['p50']), f(r['p95']), fps(r['p95']), f(r['gpu']), sv, ps,
            r['session'], 'valid' if r['perf_valid'] else 'CONTAMINATED/unknown'))
    md = '\n'.join(L) + '\n'
    print(md)
    if a.md: open(a.md, 'w').write(md)
    if a.json: json.dump(rows, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
