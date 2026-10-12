#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: flat table of every perf_route.py run below the given roots (one row per config), oldest first, with the lock verdict of the
session it ran in (the perf_gpu.json sidecar next to the session folder). usage: make_table.py <root> [<root> ...] [--md out.md] [--json out.json]
A row is only evidence when its lock column says valid (gpu_slot.sh perf, exclusive, GPU calm before the run)."""
import argparse, csv, glob, json, os


def smooth_p95(csv_path):
    """p95 of the 2-frame rolling mean of FrameTime and of GPUTime. The offscreen fixed-step loop alternates long / short frame pairs (e.g. 27 + 11 ms
    around a 19 ms mean: the game thread runs one frame ahead and catches up) while the GPU time stays flat, so the raw frame p95 overstates what a
    paced (vsync / limiter) presentation would show; both numbers are reported, the raw one is the SPEC line."""
    try:
        rows = list(csv.reader(open(csv_path))); h = rows[0]; n = len(h) - 1; idx = {x: i - 1 for i, x in enumerate(h) if i > 0}
        ft, gp = [], []
        for r in rows[1:]:
            if len(r) < n + 1 or not r: continue
            try: a, b = float(r[1:n + 1][idx['FrameTime']] or 0), float(r[1:n + 1][idx['GPUTime']] or 0)
            except (ValueError, KeyError): continue
            if a > 0: ft.append(a); gp.append(b)
        sm = [(ft[i] + ft[i + 1]) / 2 for i in range(len(ft) - 1)]
        pct = lambda v, q: sorted(v)[min(len(v) - 1, int(len(v) * q / 100.0))] if v else None
        return pct(sm, 95), pct(sorted(x for x in gp if x > 0), 95)
    except Exception:
        return None, None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('roots', nargs='+'); ap.add_argument('--md'); ap.add_argument('--json')
    a = ap.parse_args()
    rows = []
    for root in a.roots:
        for rp in glob.glob(os.path.join(root, '**', 'result.json'), recursive=True):
            r = json.load(open(rp)); sess = os.path.dirname(os.path.dirname(rp))
            side = {}
            sj = os.path.join(sess, 'perf_gpu.json')
            if os.path.exists(sj):
                try: side = json.load(open(sj))
                except Exception: pass
            c, w = r.get('csv') or {}, r.get('wh_perf') or {}
            p95s, gp95 = smooth_p95(os.path.join(os.path.dirname(rp), 'csv.csv'))
            rows.append({'mtime': os.path.getmtime(rp), 'session': os.path.relpath(sess, os.path.dirname(root.rstrip('/'))), 'config': r['config'], 'sp': r['screen_percentage'],
                         'internal': '%sx%s' % (w.get('internal_w', '?'), w.get('internal_h', '?')), 'output': r.get('res'),
                         'map': r.get('map', '').replace('/Game/Maps/', ''), 'cvars': (r.get('spec', '').split('@', 1)[-1].split('+', 1)[-1].replace('+', ' ') if 'set:' in r.get('spec', '') else ' '.join('%s=%s' % kv for kv in (r.get('cvars') or {}).items())) + (' ' + ' '.join(r.get('flags') or []) if r.get('flags') else ''),
                         'p50': c.get('p50_ms'), 'p95': c.get('p95_ms'), 'p95_2f': p95s, 'gpu_p95': gp95, 'avg': c.get('avg_ms'), 'gpu': (c.get('gpu_ms') or {}).get('avg'), 'hitches': c.get('hitches'),
                         'valid': bool(side.get('perf_valid')), 'util_before': side.get('util_before'), 'error': r.get('error')})
    rows.sort(key=lambda x: x['mtime'])
    f = lambda x, n=2: ('%.*f' % (n, x)) if isinstance(x, (int, float)) else 'n/a'
    fps = lambda ms: f(1000.0 / ms, 1) if ms else 'n/a'
    L = ['| session | config | output / internal | p50 ms (fps) | p95 ms (fps) | p95 2-frame mean | avg ms | GPU ms (p95) | hitches | lock | settings |', '|' + '---|' * 11]
    for x in rows:
        L.append('| %s | %s | %s / %s | %s (%s) | %s (%s) | %s (%s) | %s | %s (%s) | %s | %s | %s |' % (
            x['session'], x['config'], x['output'], x['internal'], f(x['p50']), fps(x['p50']), f(x['p95']), fps(x['p95']), f(x['p95_2f']), fps(x['p95_2f']),
            f(x['avg']), f(x['gpu']), f(x['gpu_p95']), x['hitches'],
            'valid (util before %s %%)' % x['util_before'] if x['valid'] else 'NOT VALID', ('map %s; ' % x['map'] if x['map'] != 'Manhattan' else '') + (x['cvars'] or '-')))
    md = '\n'.join(L) + '\n'
    print(md)
    if a.md: open(a.md, 'w').write(md)
    if a.json: json.dump(rows, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
