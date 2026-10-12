#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: headless Unreal Insights analysis of a perf_route.py --trace run (no window: -NoUI -AutoQuit -RenderOffScreen).
What is the frame waiting on?  For a short slice of the trace it exports every thread's timing events and prints
  * the GPU graphics queue: SceneRender duration, period, the idle gaps between the top-level events,
  * the render thread: the long scopes (a 'WaitForVisibilityTasks' scope means it is blocked, usually on a GPU-bound occlusion query),
  * the worker threads: the long tasks the render thread is waiting for.
usage: insights_frame.py <trace.utrace> [--t0 60.0] [--len 0.07] [--out <dir>]      (t0 = trace seconds; any point inside the perf window)
Round 01 finding on the untouched Manhattan build (docs/night1/perf/round-01/INSIGHTS.md): render thread 26 of 28 ms in
OcclusionCullPipe > RHIGetRenderQueryResult_GPU_Wait (waiting for the previous frame's GPU work), GPU graphics queue SceneRender ~18-22 ms
plus a 3 ms idle hole before PostProcessing (TSR history at 200 % of 4K output)."""
import argparse, csv, os, signal, subprocess, sys, collections

EXE = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealInsights.app/Contents/MacOS/UnrealInsights'


def export(trace, out_csv, t0, t1, log):
    cmd = ('TimingInsights.ExportTimingEvents %s -columns=ThreadId,ThreadName,TimerId,TimerName,StartTime,EndTime,Duration,Depth '
           '-threads=* -timers=* -startTime=%s -endTime=%s' % (out_csv, t0, t1))
    p = subprocess.Popen([EXE, '-OpenTraceFile=' + trace, '-ExecOnAnalysisCompleteCmd=' + cmd, '-NoUI', '-AutoQuit', '-RenderOffScreen', '-unattended',
                          '-stdout', '-abslog=' + log], stdout=open(log + '.stdout', 'w'), stderr=subprocess.STDOUT)
    try: p.wait(timeout=300)
    except subprocess.TimeoutExpired:
        p.send_signal(signal.SIGTERM)  # never SIGKILL (RULES.md); Insights has no GPU work of its own
        p.wait(timeout=60)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('trace'); ap.add_argument('--t0', type=float, default=60.0)
    ap.add_argument('--len', type=float, default=0.07); ap.add_argument('--out', default='.')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    csv_path = os.path.abspath(os.path.join(a.out, 'slice.csv'))
    export(os.path.abspath(a.trace), csv_path, a.t0, a.t0 + a.len, os.path.join(os.path.abspath(a.out), 'insights.log'))
    rows = list(csv.DictReader(open(csv_path)))
    f = lambda r, k: float(r[k])
    gpu = sorted([r for r in rows if r['ThreadName'] == 'GPU0-Graphics0' and r['Depth'] == '0'], key=lambda r: f(r, 'StartTime'))
    print('GPU0-Graphics0 top-level events (ms from the first SceneRender start):')
    if gpu:
        t0 = next((f(r, 'StartTime') for r in gpu if r['TimerName'] == 'SceneRender'), f(gpu[0], 'StartTime'))
        prev_end = None
        for r in gpu:
            s, e = f(r, 'StartTime'), f(r, 'EndTime')
            if prev_end is not None and s - prev_end > 0.0005: print('    ---- idle %.2f ms' % ((s - prev_end) * 1e3))
            if e - s > 0.0003 or r['TimerName'] == 'SceneRender': print('  %8.2f -> %8.2f  %6.2f  %s' % ((s - t0) * 1e3, (e - t0) * 1e3, (e - s) * 1e3, r['TimerName']))
            prev_end = max(prev_end or e, e)
    for th in ('RenderThread 0', 'GameThread', 'RHIThread'):
        ev = sorted([r for r in rows if r['ThreadName'] == th and f(r, 'Duration') > 0.004], key=lambda r: (f(r, 'StartTime'), int(r['Depth'])))
        print('\n%s long scopes (>4 ms):' % th)
        for r in ev[:14]: print('  d%s %8.2f ms  %s' % (r['Depth'], f(r, 'Duration') * 1e3, r['TimerName'][:90]))
    print('\nworker-thread long tasks (>4 ms):')
    for r in sorted([r for r in rows if 'Worker' in r['ThreadName'] and f(r, 'Duration') > 0.004], key=lambda r: -f(r, 'Duration'))[:10]:
        print('  %-24s d%s %8.2f ms  %s' % (r['ThreadName'], r['Depth'], f(r, 'Duration') * 1e3, r['TimerName'][:90]))


if __name__ == '__main__':
    main()
