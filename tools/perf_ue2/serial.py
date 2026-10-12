#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F (round 03, spec line P8): how serialised are the CPU and the GPU in a perf run? Trace-free (no Unreal Insights / trace server):
everything comes from the CSV profiler file of the run (csv.csv / csv.csv.gz).
  gap      = mean(FrameTime - GPUTime)   (P8 line: <= 1.0 ms). A frame that is purely GPU-bound has gap ~ 0; a positive gap is time in which the GPU idles.
  chain    = least-squares fit  FrameTime[n] = a + b * GPUTime[n-1] + c * GPUTime[n]  over the window. A frame chained to the PREVIOUS frame's GPU time
             (b ~ 1, c ~ 0, high R2) means the render thread could not start frame n before the GPU had finished frame n-1: no CPU / GPU overlap.
             `a` is then the CPU-side work that is serialised behind the GPU (render-thread prep + submission latency).
  rt       = mean exclusive render-thread time per scope (CSV `Exclusive/RenderThread/*`), the biggest ones (EventWait/Visibility = the render thread blocked in InitViews).
usage: serial.py <run dir | csv[.gz]> [...] [--from 0] [--to 1800] [--json out.json]"""
import argparse, csv, glob, gzip, json, os, statistics as st
import numpy as np


def load(p):
    if os.path.isdir(p):
        c = [x for x in glob.glob(os.path.join(p, 'csv.csv*'))]
        if not c: raise SystemExit('no csv in ' + p)
        p = c[0]
    rows = list(csv.reader(gzip.open(p, 'rt') if p.endswith('.gz') else open(p)))
    h = rows[0][1:]; d = []
    for r in rows[1:]:
        try: d.append([float(x) if x != '' else 0.0 for x in r[1:len(h) + 1]])
        except ValueError: continue
    return h, np.array(d)


def analyse(p, a=0, b=None):
    h, d = load(p); d = d[a:b]; ix = {k: i for i, k in enumerate(h)}
    F, G = d[:, ix['FrameTime']], d[:, ix['GPUTime']]
    out = {'file': p, 'frames': len(F), 'frame_ms': round(float(F.mean()), 3), 'gpu_ms': round(float(G.mean()), 3), 'gap_ms': round(float((F - G).mean()), 3),
           'gap_p95_ms': round(float(np.percentile(F - G, 95)), 3), 'p50_ms': round(float(np.percentile(F, 50)), 3), 'p95_ms': round(float(np.percentile(F, 95)), 3)}
    for k, n in (('GameThreadTime', 'game_ms'), ('RenderThreadTime', 'render_ms'), ('RHIThreadTime', 'rhi_ms')):
        if k in ix: out[n] = round(float(d[:, ix[k]].mean()), 3)
    X = np.c_[np.ones(len(F) - 1), G[:-1], G[1:]]; y = F[1:]
    co = np.linalg.lstsq(X, y, rcond=None)[0]
    out['chain'] = {'a_ms': round(float(co[0]), 3), 'b_prev_gpu': round(float(co[1]), 3), 'c_this_gpu': round(float(co[2]), 3),
                    'r2': round(float(1 - ((y - X @ co) ** 2).sum() / ((y - y.mean()) ** 2).sum()), 3)}
    rt = sorted(((float(d[:, i].mean()), k.split('/', 2)[2]) for k, i in ix.items() if k.startswith('Exclusive/RenderThread/')), reverse=True)[:6]
    out['rt_top'] = {k: round(v, 3) for v, k in rt}
    for k, n in (('GPU/RayTracingScene', 'gpu_rt_scene_ms'), ('GPU/RayTracingDynamicGeometry', 'gpu_rt_dyn_ms'), ('GPU/RayTracingGeometry', 'gpu_rt_geom_ms'),
                 ('GPU/LumenReflections', 'gpu_lumen_refl_ms'), ('GPU/Unaccounted', 'gpu_unaccounted_ms')):
        if k in ix: out[n] = round(float(d[:, ix[k]].mean()), 3)
    out['P8_pass'] = out['gap_ms'] <= 1.0
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('runs', nargs='+'); ap.add_argument('--from', dest='a', type=int, default=0); ap.add_argument('--to', dest='b', type=int, default=None)
    ap.add_argument('--json'); ap.add_argument('--md')
    a = ap.parse_args()
    res = [analyse(r, a.a, a.b) for r in a.runs]
    for r in res:
        print('%-60s frame %.2f gpu %.2f gap %.2f (p95 %.2f) | p50 %.2f p95 %.2f | chain a %.2f b %.2f c %.2f R2 %.2f | RT %s' % (
            os.path.relpath(r['file']) if len(r['file']) < 200 else r['file'], r['frame_ms'], r['gpu_ms'], r['gap_ms'], r['gap_p95_ms'], r['p50_ms'], r['p95_ms'],
            r['chain']['a_ms'], r['chain']['b_prev_gpu'], r['chain']['c_this_gpu'], r['chain']['r2'], r['rt_top']))
    if a.json: json.dump(res, open(a.json, 'w'), indent=1)
    if a.md:
        L = ['| run | frame | GPU | **gap** (P8 <= 1.0) | p50 | p95 | chain a / b(prev GPU) / c(this GPU), R2 | RT top |', '|---|---|---|---|---|---|---|---|']
        for r in res:
            L.append('| %s | %.2f | %.2f | **%.2f** | %.2f | %.2f | %.2f / %.2f / %.2f, %.2f | %s |' % (os.path.basename(os.path.dirname(r['file'])) if r['file'].endswith(('.gz', '.csv')) else r['file'], r['frame_ms'], r['gpu_ms'], r['gap_ms'],
                     r['p50_ms'], r['p95_ms'], r['chain']['a_ms'], r['chain']['b_prev_gpu'], r['chain']['c_this_gpu'], r['chain']['r2'], ', '.join('%s %.1f' % kv for kv in list(r['rt_top'].items())[:3])))
        open(a.md, 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
