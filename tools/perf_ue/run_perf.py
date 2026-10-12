#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P4 perf harness: runs the REAL game (Scripts/run_game.sh: offscreen -game, true back-buffer size, the traversal hero replaying
a scripted swing chain through the city, -WHTravScript) once per resolution-scale config and records, per run:
  frame-time stats (avg / p50 / p95 / p99 / max, hitch count) from the CSV profiler and from the WH_PERF window,
  GPU frame time, the ACTUAL internal (pre-TSR) resolution, the top GPU pass costs (-csvGpuStats), and the GPU utilisation
  (`ioreg ... Device Utilization`) sampled before and during the run. A run is flagged CONTAMINATED when other processes
  were using the GPU (utilisation before the run >= --dirty-pct, or foreign Unreal / Blender / Chrome processes running).

usage: tools/perf_ue/run_perf.py --out <dir> [--map /Game/Tests/Look/Look_Midtown] [--script tools/perf_ue/scripts/city_swing_avenue.json]
         [--configs tsr50,tsr67,native100] [--res 3840x2160] [--window 22:52] [--extra "-exec-cmds ..."] [--wait-idle 0]
Configs (r.ScreenPercentage): tsr50 = 50, tsr67 = 67, native100 = 100 (all use TSR; 100 = TSR at native = anti-aliasing only).
Any config may carry extra console variables: name=SP[+cvar=val+cvar=val], e.g. sw_lumen=50+r.Lumen.HardwareRayTracing=0
Outputs in <out>: <config>/{run.txt,*.log,*_perf.json,csv.csv}, summary.json, PERF_TABLE.md"""
import argparse, csv, json, os, re, shutil, statistics, subprocess, sys, threading, time, glob

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..'))
UE = os.path.join(WT, 'unreal', 'WebHomage')
RUN_GAME = os.path.join(UE, 'Scripts', 'run_game.sh')
CSV_DIR = os.path.join(UE, 'Saved', 'Profiling', 'CSV')
MINE = WT + '/unreal/WebHomage/WebHomage.uproject'
GPU_SLOT = os.environ.get('GPU_SLOT', '/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh')   # docs/night1/gpu/PROTOCOL.md: perf runs are EXCLUSIVE (waits for GPU < 15 % for 10 s); anything else is contaminated

def gpu_util():
    try:
        s = subprocess.run("ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '\"Device Utilization %\"=[0-9]*'", shell=True, capture_output=True, text=True).stdout
        m = re.findall(r'=(\d+)', s)
        return int(m[0]) if m else None
    except Exception:
        return None

def foreign_procs():
    """other agents' heavy GPU users right now (anything Unreal / Blender / Chrome that is not this worktree's project)"""
    out = subprocess.run(['ps', '-axo', 'pid=,%cpu=,command='], capture_output=True, text=True).stdout.splitlines()
    res = []
    for l in out:
        if MINE in l: continue
        if re.search(r'UnrealEditor|/Blender|Google Chrome|Roblox|Unity', l) and 'Helper' not in l and 'CrashReport' not in l and 'UnrealEditorServices' not in l:
            f = l.split(None, 2)
            if float(f[1]) >= 5.0: res.append({'pid': int(f[0]), 'cpu': float(f[1]), 'cmd': f[2][:120].replace(WT, '<wt>')})
    return res

class Sampler(threading.Thread):
    """1 Hz GPU utilisation of the whole device while the game runs"""
    def __init__(self, period=1.0):
        super().__init__(daemon=True); self.p = period; self.v = []; self.stop = False
    def run(self):
        while not self.stop:
            t = time.time(); u = gpu_util()
            if u is not None: self.v.append(u)
            time.sleep(max(0.0, self.p - (time.time() - t)))

def pct(a, p):
    a = sorted(a); i = (len(a) - 1) * p / 100.0; lo = int(i); hi = min(lo + 1, len(a) - 1)
    return a[lo] + (a[hi] - a[lo]) * (i - lo)

def analyse_csv(path):
    """frame stats + GPU pass table from a CsvProfiler file: header 'EVENTS,<stat>,...' + one row per frame. The first (EVENTS)
    column is free text; rows are aligned from the left (a few rows carry extra trailing fields)."""
    rows = list(csv.reader(open(path)))
    hdr = rows[0]; n = len(hdr) - 1
    data = []
    for r in rows[1:]:
        if len(r) < n + 1 or not r: continue
        v = r[1:n + 1]  # column 0 = EVENTS text; rows may carry extra trailing fields (columns the profiler discovered late): ignored
        try: data.append([float(x) if x != '' else 0.0 for x in v])
        except ValueError: continue
    idx = {h: i - 1 for i, h in enumerate(hdr) if i > 0}
    col = lambda name: [r[idx[name]] for r in data] if name in idx else []
    ft = [x for x in col('FrameTime') if x > 0]
    out = {'csv_frames': len(ft)}
    if ft:
        med = statistics.median(ft)
        out.update({'avg_ms': statistics.mean(ft), 'p50_ms': pct(ft, 50), 'p95_ms': pct(ft, 95), 'p99_ms': pct(ft, 99), 'max_ms': max(ft),
                    'fps_avg': 1000.0 / statistics.mean(ft), 'over_16_7ms': sum(1 for x in ft if x > 16.67), 'over_33_3ms': sum(1 for x in ft if x > 33.33),
                    'hitches': sum(1 for x in ft if x > 2.0 * med and x > 25.0), 'hitch_rule': 'frame > 25 ms and > 2x the median frame'})
    if ft:  # 5 s blocks: other processes can only add time, so the fastest sustained block bounds the uncontended cost from above
        blocks, acc, k = [], 0.0, 0
        for i, v in enumerate(ft):
            acc += v
            if acc >= 5000.0: blocks.append(round(statistics.mean(ft[k:i + 1]), 2)); k = i + 1; acc = 0.0
        out['blocks_5s_avg_ms'] = blocks
        if blocks: out['best_5s_block_ms'] = min(blocks)
    for nme, key in (('GameThreadTime', 'game_thread_ms'), ('RenderThreadTime', 'render_thread_ms'), ('GPUTime', 'gpu_ms'), ('RHIThreadTime', 'rhi_thread_ms')):
        c = [x for x in col(nme) if x > 0]
        if c: out[key] = {'avg': statistics.mean(c), 'p95': pct(c, 95), 'max': max(c)}
    gp = {}
    for h in hdr:
        if h.startswith('GPU/'):
            c = col(h)
            if c: gp[h] = statistics.mean(c)
    out['gpu_passes_avg_ms'] = dict(sorted(gp.items(), key=lambda kv: -kv[1])[:25])
    return out

def parse_cfg(c):
    parts = c.split('+'); name, sp = parts[0].split('=') if '=' in parts[0] else (parts[0], None)
    defaults = {'tsr50': '50', 'tsr67': '67', 'native100': '100'}
    sp = sp or defaults.get(name)
    return name, sp, parts[1:]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True); ap.add_argument('--map', default='/Game/Tests/Look/Look_Midtown')
    ap.add_argument('--script', default=os.path.join(HERE, 'scripts', 'city_swing_avenue.json'))
    ap.add_argument('--configs', default='tsr50,tsr67,native100'); ap.add_argument('--res', default='3840x2160')
    ap.add_argument('--window', default='22:52', help='perf window in game seconds (after warm-up)')
    ap.add_argument('--dirty-pct', type=int, default=10); ap.add_argument('--wait-idle', type=int, default=0, help='wait up to N s for an idle GPU before each run')
    ap.add_argument('--timeout', type=int, default=900); ap.add_argument('--gpu-stats', action='store_true', default=True)
    ap.add_argument('--reanalyze', action='store_true', help='recompute the CSV statistics of an existing --out directory'); ap.add_argument('--name', default='perf'); ap.add_argument('--fixed-step', action='store_true', help='-benchmark -fps=60: fixed 1/60 s game step, so the hero replays the SAME path in every config (frame times are still wall-clock)')
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    import ensure_boxes
    if not ensure_boxes.ensure(): sys.exit('traversal boxes are stale (see above): capture / perf would run against boxes of an older city')
    out = os.path.abspath(a.out); os.makedirs(out, exist_ok=True)
    frm, to = a.window.split(':')
    summary = []
    if a.reanalyze:
        for cfg in a.configs.split(','):
            name = parse_cfg(cfg)[0]; rp = os.path.join(out, name, 'result.json'); rec = json.load(open(rp))
            if os.path.exists(os.path.join(out, name, 'csv.csv')): rec['csv'] = analyse_csv(os.path.join(out, name, 'csv.csv'))
            json.dump(rec, open(rp, 'w'), indent=1); summary.append(rec)
        json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
        open(os.path.join(out, 'PERF_TABLE.md'), 'w').write(table(summary)); print(table(summary)); return
    for cfg in a.configs.split(','):
        name, sp, cvars = parse_cfg(cfg)
        d = os.path.join(out, name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        t0 = time.time()
        quiet = 0                                  # wait for a quiet window: 6 consecutive samples (2 s apart) below --dirty-pct and no busy foreign process
        while a.wait_idle and time.time() - t0 < a.wait_idle:
            if (gpu_util() or 0) < a.dirty_pct and not foreign_procs(): quiet += 1
            else: quiet = 0
            if quiet >= 6: break
            time.sleep(2)
        waited = round(time.time() - t0)
        pre = [gpu_util()]; time.sleep(1.5); pre.append(gpu_util()); time.sleep(1.5); pre.append(gpu_util())
        pre = [x for x in pre if x is not None]
        foreign = foreign_procs()
        cmds = ['r.ScreenPercentage %s' % sp] + [c.replace('=', ' ', 1) for c in cvars]
        started = time.time()
        smp = Sampler(); smp.start()
        cmd = [RUN_GAME, d, '-map', a.map, '-res', a.res, '-perf', a.window, '-name', name, '-timeout', str(a.timeout), '-exec', ','.join(cmds),
               '--'] + (['-WHTravScript=' + a.script, '-WHTravCsv=' + os.path.join(d, 'trav_telemetry.csv')] if a.script not in ('', 'none') else ['-WHNoMouseCapture'])
        if a.gpu_stats: cmd += ['-csvGpuStats']
        if a.fixed_step: cmd += ['-benchmark', '-fps=60']
        if os.path.exists(GPU_SLOT):
            cmd = [GPU_SLOT, 'perf', '--label', 'look', '--json', os.path.join(d, 'perf_gpu.json'), '--'] + cmd
        r = subprocess.run(cmd, capture_output=True, text=True)
        smp.stop = True; smp.join(timeout=4)
        open(os.path.join(d, 'run.txt'), 'w').write(' '.join(cmd) + '\n\n' + r.stdout + '\n' + r.stderr)
        rec = {'config': name, 'screen_percentage': sp, 'extra_cvars': cvars, 'map': a.map, 'script': (os.path.relpath(a.script, WT) if a.script not in ('', 'none') else None), 'res': a.res, 'window_s': a.window,
               'command': ' '.join(x.replace(WT, '<wt>') for x in cmd), 'gpu_util_before_pct': pre, 'gpu_util_during_pct': {'mean': (statistics.mean(smp.v) if smp.v else None), 'max': (max(smp.v) if smp.v else None), 'n': len(smp.v)},
               'foreign_gpu_procs': foreign, 'waited_for_idle_s': waited}
        pj = os.path.join(d, name + '_perf.json')
        if os.path.exists(pj):
            rec['wh_perf'] = json.load(open(pj))

        else:
            rec['error'] = 'no perf json (run failed or hit the timeout): see run.txt'
        csvs = sorted(glob.glob(os.path.join(CSV_DIR, 'Profile*.csv')), key=os.path.getmtime)
        csvs = [c for c in csvs if os.path.getmtime(c) >= started - 1]
        if csvs:
            shutil.copy(csvs[-1], os.path.join(d, 'csv.csv')); rec['csv'] = analyse_csv(csvs[-1])
        rec['contaminated'] = bool((pre and max(pre) >= a.dirty_pct) or foreign)
        rec['contamination_reason'] = ('GPU utilisation before the run %s %% (>= %d)' % (pre, a.dirty_pct) if pre and max(pre) >= a.dirty_pct else '') + ('; foreign processes: %d' % len(foreign) if foreign else '')
        gj = os.path.join(d, 'perf_gpu.json')
        if os.path.exists(gj):   # the GPU lock's verdict replaces the local guess
            try:
                g = json.load(open(gj)); rec['gpu_slot'] = g
                rec['contaminated'] = not g.get('perf_valid', False)
                rec['contamination_reason'] = '; '.join(g.get('contaminated_reasons') or []) if rec['contaminated'] else ''
            except Exception as e:
                rec['gpu_slot_error'] = str(e)
        tv = os.path.join(d, 'trav_telemetry.csv')
        if os.path.exists(tv):
            try:
                rr = list(csv.DictReader(open(tv)))
                rec['hero'] = {'rows': len(rr), 'columns': list(rr[0].keys())[:40] if rr else []}
            except Exception: pass
        summary.append(rec); json.dump(rec, open(os.path.join(d, 'result.json'), 'w'), indent=1)
        print(name, 'sp', sp, 'avg', (rec.get('csv') or {}).get('avg_ms'), 'gpu_pre', pre, 'contaminated', rec['contaminated'], flush=True)
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    with open(os.path.join(out, 'PERF_TABLE.md'), 'w') as f:
        f.write(table(summary))
    print(table(summary))

def table(summary):
    L = ['| config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches (>25 ms & >2x median) | >16.7 ms | GPU avg ms | GPU util before % | contaminated |', '|' + '---|' * 14]
    for r in summary:
        c, w = r.get('csv') or {}, r.get('wh_perf') or {}
        g = (c.get('gpu_ms') or {}).get('avg', w.get('gpu_avg_ms'))
        f = lambda x, n=2: ('%.*f' % (n, x)) if isinstance(x, (int, float)) else 'n/a'
        L.append('| %s (r.ScreenPercentage %s) | %sx%s | %sx%s | %s (%s) | %s | %s | %s | %s | %s | %s | %s/%s | %s | %s | %s |' % (
            r['config'], r['screen_percentage'], w.get('output_w', '?'), w.get('output_h', '?'), w.get('internal_w', '?'), w.get('internal_h', '?'),
            f(c.get('avg_ms')), f(c.get('fps_avg'), 1), f(c.get('best_5s_block_ms')), f(c.get('p50_ms')), f(c.get('p95_ms')), f(c.get('p99_ms')), f(c.get('max_ms')), c.get('hitches', 'n/a'),
            c.get('over_16_7ms', 'n/a'), c.get('csv_frames', 'n/a'), f(g), '/'.join(map(str, r['gpu_util_before_pct'])),
            'YES: ' + r['contamination_reason'] if r['contaminated'] else 'no'))
    return '\n'.join(L) + '\n'

if __name__ == '__main__':
    main()
