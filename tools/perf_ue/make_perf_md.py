#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Builds PERF.md of a round from the evidence directories written by run_perf.py / sweep_views.sh (numbers only, no self-assessment).
usage: tools/perf_ue/make_perf_md.py docs/night1/look/round-01 [--main perf_a,perf_b] [--extra name=dir,...]"""
import json, os, sys, glob, subprocess, statistics

rnd = os.path.abspath(sys.argv[1])
main = [d for d in (sys.argv[sys.argv.index('--main') + 1] if '--main' in sys.argv else 'perf_fixed_a,perf_fixed_b').split(',') if os.path.exists(os.path.join(rnd, d, 'summary.json'))]

def load(d): return json.load(open(os.path.join(rnd, d, 'summary.json')))
f = lambda x, n=1: ('%.*f' % (n, x)) if isinstance(x, (int, float)) else 'n/a'
def row(d, r):
    c, w = r.get('csv') or {}, r.get('wh_perf') or {}
    return '| %s | %s (SP %s) | %sx%s | %sx%s | %s (%s) | %s | %s | %s | %s | %s | %s | %s | %s |' % (
        d, r['config'], r['screen_percentage'], w.get('output_w'), w.get('output_h'), w.get('internal_w'), w.get('internal_h'), f(c.get('avg_ms')), f(c.get('fps_avg')), f(c.get('best_5s_block_ms')),
        f(c.get('p50_ms')), f(c.get('p95_ms')), f(c.get('p99_ms')), f(c.get('max_ms')), c.get('hitches'), f((c.get('gpu_ms') or {}).get('avg')),
        '/'.join(map(str, r['gpu_util_before_pct'])) + (' (during: mean %s)' % f((r.get('gpu_util_during_pct') or {}).get('mean'), 0)))
HDR = '| run | config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches | GPU ms (avg) | GPU util % before the run (3 samples) |\n|' + '---|' * 13

L = ['# P4 perf: 3840x2160 output, real gameplay (round 01)', '',
     '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
     '@@SUMMARY@@', '',
     '## How it was measured', '',
     'Real game (`Scripts/run_game.sh`: standalone `-game`, offscreen, true 3840x2160 back buffer, `t.MaxFPS 0`, no vsync), map `/Game/Tests/Look/Look_Midtown` (midday preset, city + traversal boxes),',
     'the P3 traversal hero (real hero mesh, C++ animation) replaying `tools/perf_ue/scripts/city_swing_avenue.json`: 14 s standing warm-up, then sprint, jump and a continuous swing chain up the avenue.',
     'Main table: `run_perf.py --fixed-step` = `-benchmark -fps=60`, a fixed 1/60 s game step, so the hero flies the SAME route in every config (free-running, the swing rhythm depends on the frame time and the hero',
     'ends up on a different, shorter route in every run: see the second table). Frame times are wall-clock either way (CSV profiler `FrameTime`, identical to the in-game `WH_PERF` json `avg_ms`).',
     'Perf window: game seconds 22 to 52 (30 s, swinging the whole time). Internal resolution = the `WH_PERF` json (`r.ScreenPercentage` set explicitly, TSR upscale).',
     'A "hitch" = a frame slower than 25 ms and slower than twice the run median. GPU utilisation is `ioreg -r -d 1 -c IOAccelerator | grep "Device Utilization"` (3 samples before the run, plus a 1 Hz mean during it).', '',
     '## READ THIS FIRST: the GPU is shared', '',
     'Other agents\' Unreal editors, game runs, Blender and Chrome used the GPU during the whole session: device utilisation before a run was 40 to 100 % for most of it. Identical builds then differ by up to 2x between repeats',
     '(`perf_free_*`, `perf_variants`). Each run\'s `result.json` carries `contaminated` (utilisation before the run >= 10 % or another busy Unreal / Blender / Chrome process) and the reason;',
     'a run is only a clean measurement of this machine when the last column says so. `run_perf.py --wait-idle N` waits for an idle GPU before each run.', '',
     '## Frame times, three resolution configs, deterministic route (fixed step), two repeats', '', HDR]
for d in main:
    for r in load(d): L.append(row(d, r))
L += ['', 'For comparison, free-running (real-time step) repeats of the same three configs. The hero route differs per run (it can stall on a wall for several seconds) and the GPU load of other agents changed between runs:', '', HDR]
for d in sorted(glob.glob(os.path.join(rnd, 'perf_free_*'))):
    dn = os.path.basename(d)
    if os.path.exists(os.path.join(d, 'summary.json')):
        for r in load(dn): L.append(row(dn, r))
L += ['']

# summary of the main table (numbers only), spliced in at the top
_best = {}
for d in main:
    for r in load(d):
        c = r.get('csv') or {}
        if c.get('best_5s_block_ms'): _best.setdefault(r['config'], []).append((c['best_5s_block_ms'], c['avg_ms'], (r.get('wh_perf') or {})))
_sum = []
if _best:
    _sum += ['## Summary (numbers only)', '',
             'Deterministic route, 3840x2160 output, real gameplay, GPU shared with other agents (see below). "Best 5 s block" = the fastest 5 s stretch of the 30 s window (other processes can only add time).', '']
    for cfg in ('tsr50', 'tsr67', 'native100'):
        if cfg in _best:
            v = _best[cfg]; w = v[0][2]
            _sum.append('- **%s** (internal %sx%s): best 5 s block %.1f to %.1f ms (%.0f to %.0f fps); whole-window average %.1f to %.1f ms over %d runs' % (
                cfg, w.get('internal_w'), w.get('internal_h'), min(x[0] for x in v), max(x[0] for x in v), 1000.0 / max(x[0] for x in v), 1000.0 / min(x[0] for x in v),
                min(x[1] for x in v), max(x[1] for x in v), len(v)))
    _sum += ['- No config reached 16.7 ms (60 fps) in any 5 s block.', '']
_i = L.index('@@SUMMARY@@'); L[_i:_i + 2] = _sum

# hero telemetry over the perf window (proves the frames are real movement through the city)
import csv as _csv
def hero_summary(path, t0, t1):
    rows = [r for r in _csv.DictReader(open(path)) if t0 <= float(r['t']) <= t1]
    if not rows: return None
    modes = {}
    for r in rows: modes[r['mode']] = modes.get(r['mode'], 0) + 1
    y = [float(r['y_m']) for r in rows]; sp = [float(r['speed_mps']) for r in rows]; h = [float(r['height_above_floor_m']) for r in rows]
    return {'frames': len(rows), 'modes': {k: '%.0f %%' % (100.0 * v / len(rows)) for k, v in modes.items()}, 'y_m': (y[0], y[-1]), 'mean_speed_mps': sum(sp) / len(sp), 'max_speed_mps': max(sp), 'height_range_m': (min(h), max(h))}
if main:
    tp = os.path.join(rnd, main[0], 'tsr50', 'trav_telemetry.csv')
    if os.path.exists(tp):
        hs = hero_summary(tp, 22.0, 52.0) if False else hero_summary(tp, 22.0, 52.0)
        if hs: L += ['## What the hero does inside the perf window (%s / tsr50 telemetry, hero time 22 s to 52 s)' % main[0], '',
                     '%d frames; modes %s; travels from y = %.0f m to y = %.0f m (north = -Y); speed mean %.1f m/s, max %.1f m/s; height above the floor %.1f to %.1f m.' % (
                         hs['frames'], hs['modes'], hs['y_m'][0], hs['y_m'][1], hs['mean_speed_mps'], hs['max_speed_mps'], hs['height_range_m'][0], hs['height_range_m'][1]), '']
# top GPU passes
L += ['## Top GPU costs during the swing chain (CSV `GPU/*` stats, ms per frame, averaged over the window)', '',
      'Same GPU pass timers that `stat gpu` shows (`-csvGpuStats`). Absolute values inherit the contamination above; the ranking and the shares are the useful part.', '']
for d in main[:1]:
    for r in load(d):
        c = r['csv']; tot = (c.get('gpu_ms') or {}).get('avg') or 0
        L += ['**%s / %s, internal %sx%s: GPU %.1f ms per frame, render thread %.1f ms, game thread %.1f ms**' % (d, r['config'], r['wh_perf']['internal_w'], r['wh_perf']['internal_h'], tot, c['render_thread_ms']['avg'], c['game_thread_ms']['avg']), '',
              '| pass | ms | share of GPU time |', '|---|---|---|']
        for k, v in list(c['gpu_passes_avg_ms'].items())[:12]: L.append('| %s | %.2f | %.0f %% |' % (k[4:], v, 100.0 * v / tot if tot else 0))
        L.append('')
# heaviest view
vd = os.path.join(rnd, 'perf_views')
if os.path.isdir(vd):
    L += ['## Heaviest view (static shot cameras S1..S8, midday preset, 3840x2160 output, TSR 50 %, window 14 s to 24 s; measured just before the sky light cloud ambient occlusion was switched off, 2 passes, GPU shared)', '',
          '| view | pass | avg ms (CSV) | GPU ms (avg) | GPU util % before |', '|---|---|---|---|---|']
    best = {}
    for pdir in sorted(glob.glob(vd + '/pass*')):
        for sd in sorted(glob.glob(pdir + '/S*')):
            rp = sd + '/tsr50/result.json'
            if not os.path.exists(rp): continue
            r = json.load(open(rp)); c = r.get('csv') or {}
            sid = os.path.basename(sd); g = (c.get('gpu_ms') or {}).get('avg')
            L.append('| %s | %s | %s | %s | %s |' % (sid, os.path.basename(pdir), f(c.get('avg_ms')), f(g), '/'.join(map(str, r['gpu_util_before_pct']))))
            if g and (sid not in best or g < best[sid][0]): best[sid] = (g, r)
    if best:
        heavy = max(best, key=lambda k: best[k][0]); g, r = best[heavy]
        L += ['', 'Heaviest view by the lower GPU time of the two passes: **%s** (%.1f ms GPU at 1920x1080 internal). Its top GPU passes:' % (heavy, g), '', '| pass | ms | share |', '|---|---|---|']
        for k, v in list(r['csv']['gpu_passes_avg_ms'].items())[:12]: L.append('| %s | %.2f | %.0f %% |' % (k[4:], v, 100.0 * v / g))
        L.append('')
# variants
if os.path.exists(os.path.join(rnd, 'perf_variants', 'summary.json')):
    L += ['## Console-variable variants at TSR 50 %, deterministic route (what each feature costs)', '',
          'Same route every time (fixed step), so the route position is the same in block k of every row: compare blocks, not only averages. The GPU was shared while these ran (last column;',
          'the second half of `base_b` and the first half of `no_dfshadow` show a burst of other load: 34 to 40 ms blocks). Differences under about 2 ms are inside the run-to-run spread.', '',
          '| variant | cvars | avg ms | GPU ms | 5 s block averages, in route order (ms) | GPU util % before |', '|---|---|---|---|---|---|']
    for r in load('perf_variants'):
        c = r.get('csv') or {}
        L.append('| %s | %s | %s | %s | %s | %s |' % (r['config'], (' '.join(r['extra_cvars']) or '(none)'), f(c.get('avg_ms')), f((c.get('gpu_ms') or {}).get('avg')), ' '.join('%.1f' % b for b in c.get('blocks_5s_avg_ms', [])), '/'.join(map(str, r['gpu_util_before_pct']))))
    L.append('')
L += ['## Commands', '', '```',
      'unreal/WebHomage/Scripts/build_editor.sh                        # C++ (once)',
      'tools/perf_ue/rebuild_city.sh; tools/perf_ue/rebuild_look.sh    # content, see HANDOFF.md',
      'tools/perf_ue/run_perf.py --out docs/night1/look/round-01/perf_a --window 22:52 --wait-idle 40      # tsr50, tsr67, native100',
      'tools/perf_ue/sweep_views.sh docs/night1/look/round-01/perf_views midday 2                          # heaviest view',
      '```', '', 'Exact command line of every run: `command` in each `<run>/<config>/result.json` and `run.txt`. Per-frame CSVs: `<run>/<config>/csv.csv`; hero telemetry: `trav_telemetry.csv`.', '']
open(os.path.join(rnd, 'PERF.md'), 'w').write('\n'.join(L))
print('wrote', os.path.join(rnd, 'PERF.md'))
