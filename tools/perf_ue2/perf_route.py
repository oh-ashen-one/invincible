#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F perf harness: the REAL game (Scripts/run_game.sh, offscreen -game, 3840x2160 back buffer) replaying piece C's
deterministic 30 s Manhattan swing route (-benchmark -fps=60 fixed game step, so every config sees the same frames),
one game process per config. Per config it records frame / game / render / RHI thread / GPU time, the per-pass GPU costs
(-csvGpuStats), the render-thread breakdown, draw calls, primitives, instance counts and the ACTUAL internal resolution.

MUST run inside the exclusive GPU lock (RULES.md / docs/night1/gpu/PROTOCOL.md):
  /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh perf --label perf --json <out>/perf_gpu.json -- \
      python3 tools/perf_ue2/perf_route.py --out <out> --configs base@67,tsr50@50,...

Config spec (comma separated list):  name@SP[+set:<override file stem>][+cvar=value][+flag:-GameFlag][+map:/Game/Path/Map][+variant:Cl15][+view:S2]...
  SP = r.ScreenPercentage (TSR on in every config). 'set:perf60' reads tools/perf_ue2/overrides/perf60.cvars.
  All cvars are applied at startup with -dpcvars (device-profile priority: above scalability / project settings, before
  the first frame), and runtime-safe ones are also re-applied with -ExecCmds. Example: nmpe2@67+r.Nanite.MaxPixelsPerEdge=2
Outputs: <out>/<name>/{result.json,csv.csv,run.txt,*.log}, <out>/summary.json, <out>/TABLE.md"""
import argparse, csv, glob, json, os, re, shutil, statistics, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..'))
UE = os.path.join(WT, 'unreal', 'WebHomage')
RUN_GAME = os.path.join(UE, 'Scripts', 'run_game.sh')
CSV_DIR = os.path.join(UE, 'Saved', 'Profiling', 'CSV')
ROUTE = os.path.join(WT, 'docs', 'night1', 'manhattan', 'scripts', 'route_30s_warmup15.json')
sys.path.insert(0, os.path.join(WT, 'tools', 'perf_ue'))
from run_perf import analyse_csv, pct  # noqa: E402  (P4's CSV reader, unchanged)


def read_set(stem):
    p = os.path.join(HERE, 'overrides', stem + '.cvars')
    out = []
    for l in open(p):
        l = l.split('#', 1)[0].strip()
        if not l: continue
        if l.startswith('set:'): out += read_set(l[4:]); continue
        k, v = [x.strip() for x in l.split('=', 1)]
        out.append((k, v))
    return out


def parse_cfg(spec):
    parts = spec.split('+')
    name, sp = parts[0].split('@') if '@' in parts[0] else (parts[0], '67')   # sp may be 'ini' (no r.ScreenPercentage / dpcvars from the command line)
    cv = []
    for p in parts[1:]:
        if p.startswith('set:'): cv += read_set(p[4:])
        elif p.startswith('variant:'): cv.append((p, '1'))  # local map variant /Game/PerfF/<tag>/ (make_variants.py): the run's map (--map) is taken from that folder
        elif p.startswith('flag:') or p.startswith('map:') or p.startswith('view:'): cv.append((p, '1'))  # game command-line flag (flag:-WHTravMask) / map override (map:/Game/PerfF/Cl15/Manhattan); both kept out of the cvar lists in main
        else:
            k, v = p.split('=', 1); cv.append((k, v))
    d = {}
    for k, v in cv: d[k] = v  # later wins
    return name, sp, list(d.items())


def rt_breakdown(path):
    """extra columns of the CsvProfiler file: render-thread exclusive stats, draw calls, primitives, instances, lights"""
    rows = list(csv.reader(open(path)))
    hdr = rows[0]; n = len(hdr) - 1
    data = []
    for r in rows[1:]:
        if len(r) < n + 1: continue
        try: data.append([float(x) if x != '' else 0.0 for x in r[1:n + 1]])
        except ValueError: continue
    idx = {h: i - 1 for i, h in enumerate(hdr) if i > 0}
    mean = lambda h: statistics.mean([d[idx[h]] for d in data]) if h in idx and data else None
    rt = {h.split('/', 2)[2]: mean(h) for h in hdr if h.startswith('Exclusive/RenderThread/')}
    gt = {h.split('/', 2)[2]: mean(h) for h in hdr if h.startswith('Exclusive/GameThread/')}
    aw = {h.split('/', 2)[2]: mean(h) for h in hdr if h.startswith('Exclusive/AllWorkers/')}
    dc = {h.split('/', 1)[1]: mean(h) for h in hdr if h.startswith('DrawCall/')}
    keys = ['RHI/DrawCalls', 'RHI/PrimitivesDrawn', 'GPUSceneInstanceCount', 'SceneCulling/NumDynamicInstances', 'SceneCulling/NumStaticInstances',
            'SceneCulling/NumUpdatedInstances', 'RenderThreadIdle/Total', 'RenderThreadIdle/CriticalPath', 'RenderThreadIdle/SwapBuffer',
            'RenderThreadIdle/GPUQuery', 'RenderThreadIdle/NonCriticalPath', 'RenderThreadTime_CriticalPath', 'GameThreadTime_CriticalPath',
            'ShadowCacheUsageMB', 'LightCount/UpdatedShadowMaps', 'RDGCount/Passes', 'DrawSceneCommand_StartDelay', 'Scheduler/Oversubscription']
    top = lambda d, k=14: dict(sorted(((a, round(b, 3)) for a, b in d.items() if b is not None), key=lambda kv: -kv[1])[:k])
    return {'render_thread_exclusive_ms': top(rt), 'game_thread_exclusive_ms': top(gt, 8), 'all_workers_exclusive_ms': top(aw, 10),
            'drawcalls_by_pass': top(dc, 10), 'counters': {k: (round(mean(k), 3) if mean(k) is not None else None) for k in keys}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--configs', required=True)
    ap.add_argument('--map', default='/Game/Maps/Manhattan')
    ap.add_argument('--script', default=ROUTE, help="traversal script; 'none' for a static view map (e.g. /Game/Maps/Manhattan_View_S2)")
    ap.add_argument('--res', default='3840x2160')
    ap.add_argument('--window', default='15:45', help='game seconds; the route runs 15..45 (15 s standing warm-up first)')
    ap.add_argument('--timeout', type=int, default=900)
    ap.add_argument('--trace', default='', help='Unreal Insights channels for a -trace run (e.g. cpu,gpu,frame); writes <name>/trace.utrace')
    ap.add_argument('--budget-s', type=int, default=780, help='skip remaining configs when the next one would pass this many seconds (lock max hold 15 min)')
    a = ap.parse_args()
    out = os.path.abspath(a.out); os.makedirs(out, exist_ok=True)
    summary, t_start, last = [], time.time(), 0.0
    for spec in a.configs.split(','):
        name, sp, cv = parse_cfg(spec)
        flags = [k[5:] for k, v in cv if k.startswith('flag:')]; maps = [k[4:] for k, v in cv if k.startswith('map:')]
        var = [k[8:] for k, v in cv if k.startswith('variant:')]; views = [k[5:] for k, v in cv if k.startswith('view:')]
        cv = [(k, v) for k, v in cv if not k.startswith(('flag:', 'map:', 'variant:', 'view:'))]
        base_map, cfg_script = a.map, a.script
        if views: base_map, cfg_script = '/Game/Maps/Manhattan_View_' + views[-1], 'none'   # static view config (P3): no route script
        cfg_map = maps[-1] if maps else ('/Game/PerfF/%s/%s' % (var[-1], os.path.basename(base_map)) if var else base_map)
        if last and time.time() - t_start + last * 1.1 > a.budget_s:
            print('SKIP (lock budget)', name, flush=True); summary.append({'config': name, 'skipped': 'lock budget'}); continue
        d = os.path.join(out, name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        started = time.time()
        execs = ([] if sp == 'ini' else ['r.ScreenPercentage %s' % sp]) + ['%s %s' % (k, v) for k, v in cv]   # SP 'ini' = the shipped path: the preset comes from Config/Mac/MacEngine.ini (build_map.py step perf_preset), nothing on the command line
        # no -WHTravMask: the hero-mask / scene-depth telemetry captures stay off (they re-render the scene every frame)
        extra = (['-WHTravScript=' + cfg_script, '-WHTravCsv=' + os.path.join(d, 'trav_telemetry.csv')] if cfg_script not in ('', 'none') else []) \
            + ['-csvGpuStats', '-benchmark', '-fps=60', '-notraceserver']
        extra += flags
        if cv: extra.append('-dpcvars=' + ','.join('%s=%s' % (k, v) for k, v in cv))
        if a.trace: extra += ['-trace=' + a.trace, '-tracefile=' + os.path.join(d, 'trace.utrace')]
        cmd = [RUN_GAME, d, '-map', cfg_map, '-res', a.res, '-perf', a.window, '-name', name, '-timeout', str(a.timeout),
               '-exec', ','.join(execs), '--'] + extra
        r = subprocess.run(cmd, capture_output=True, text=True)
        open(os.path.join(d, 'run.txt'), 'w').write(' '.join(cmd) + '\n\n' + r.stdout + '\n' + r.stderr)
        rec = {'config': name, 'spec': spec, 'screen_percentage': sp, 'cvars': dict(cv), 'flags': flags, 'map': cfg_map, 'res': a.res, 'window_s': a.window,
               'script': os.path.relpath(cfg_script, WT) if cfg_script not in ('', 'none') else 'none', 'wall_s': round(time.time() - started, 1),
               'command': ' '.join(x.replace(WT, '<wt>') for x in cmd)}
        pj = os.path.join(d, name + '_perf.json')
        if os.path.exists(pj): rec['wh_perf'] = json.load(open(pj))
        else: rec['error'] = 'no perf json (run failed or timed out): see run.txt'
        csvs = [c for c in sorted(glob.glob(os.path.join(CSV_DIR, 'Profile*.csv')), key=os.path.getmtime) if os.path.getmtime(c) >= started - 1]
        if csvs:
            shutil.move(csvs[-1], os.path.join(d, 'csv.csv'))
            rec['csv'] = analyse_csv(os.path.join(d, 'csv.csv'))
            rec['breakdown'] = rt_breakdown(os.path.join(d, 'csv.csv'))
        lg = os.path.join(d, name + '.log')
        if os.path.exists(lg):  # which -dpcvars the engine actually accepted / rejected
            txt = open(lg, errors='replace').read()
            rec['dpcvar_log'] = sorted(set(re.findall(r'(?:Setting Device Profile CVar|Setting CVar|DPCVar)[^\n]{0,160}', txt)))[:60]
            rec['cvar_warnings'] = sorted(set(l.split('LogConsoleManager: ')[-1][:200] for l in txt.splitlines() if 'LogConsoleManager' in l and 'Warning' in l))[:30]
        json.dump(rec, open(os.path.join(d, 'result.json'), 'w'), indent=1)
        summary.append(rec); last = time.time() - started
        c = rec.get('csv') or {}
        print('%-14s sp %-3s avg %s p50 %s p95 %s gpu %s rt %s  (%.0f s)' % (name, sp, fmt(c.get('avg_ms')), fmt(c.get('p50_ms')), fmt(c.get('p95_ms')),
              fmt((c.get('gpu_ms') or {}).get('avg')), fmt((c.get('render_thread_ms') or {}).get('avg')), last), flush=True)
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    open(os.path.join(out, 'TABLE.md'), 'w').write(table(summary))
    print(table(summary))


def fmt(x, n=2): return ('%.*f' % (n, x)) if isinstance(x, (int, float)) else 'n/a'


def table(summary):
    L = ['| config | SP | internal | avg ms (fps) | p50 ms (fps) | p95 ms (fps) | p99 | hitches | GPU ms | RT ms | GT ms | RHI ms | draw calls | cvars |',
         '|' + '---|' * 14]
    for r in summary:
        if r.get('skipped'): L.append('| %s | skipped (%s) |' % (r['config'], r['skipped'])); continue
        c, w, b = r.get('csv') or {}, r.get('wh_perf') or {}, (r.get('breakdown') or {}).get('counters') or {}
        f1 = lambda ms: '%s (%s)' % (fmt(ms), fmt(1000.0 / ms, 1) if ms else 'n/a')
        L.append('| %s | %s | %sx%s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r['config'], r['screen_percentage'], w.get('internal_w', '?'), w.get('internal_h', '?'), f1(c.get('avg_ms')), f1(c.get('p50_ms')),
            f1(c.get('p95_ms')), fmt(c.get('p99_ms')), c.get('hitches', 'n/a'), fmt((c.get('gpu_ms') or {}).get('avg')),
            fmt((c.get('render_thread_ms') or {}).get('avg')), fmt((c.get('game_thread_ms') or {}).get('avg')), fmt((c.get('rhi_thread_ms') or {}).get('avg')),
            fmt(b.get('RHI/DrawCalls'), 0), ' '.join('%s=%s' % kv for kv in r.get('cvars', {}).items()) or '-'))
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    main()
