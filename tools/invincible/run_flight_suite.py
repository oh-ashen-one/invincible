#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation. See DISCLAIMER.md.
"""Invincible flight capture suite: one REAL -game engine per case through the shared GPU coordinator (tools/gpu/gpu_slot.sh capture,
FIFO, honours PAUSED / holders / the hard cap), scripted input (-WHTravScript), per-frame telemetry, then check_flight.py.

  --sim     telemetry only: -nullrhi, 640x360, no frames (cheap; nullrhi telemetry is bit-identical to rendered runs, island r03)
  default   rendered: playable profile + Fast preset, 1920x1080, 100 % internal, TSR, fixed 1/60 s (-benchmark -fps=60), -dumpmovie,
            1.5 s pre-roll cut, -WHSuit=invincible; writes <case>.mp4 + a contact sheet.  Fixed-step footage is NOT real-time FPS proof.

outputs: <scratch>/<tag>/<case>/{<case>.log, <case>_telemetry.csv, frames/ (render)}; docs/invincible/captures/<tag>/{<case>.mp4, <case>_sheet.jpg,
         <case>_telemetry.csv, CHECK.json, CHECK.md, RUN.json}
usage: run_flight_suite.py <tag> [--sim] [--cases fl01,fl05] [--scratch DIR] [--game-arg ARG ...] [--keep-frames]"""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UE_DIR = ROOT / 'unreal/WebHomage'
UE = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor')
GPU_SH = ROOT / 'tools/gpu/gpu_slot.sh'
GPU_DIR = Path.home() / '.cache/gpu-slot'
CASES_DIR = Path(__file__).resolve().parent / 'flight_cases'
USER = UE_DIR / 'Saved/Showcase/User'
SHOTS = USER / 'Saved/Screenshots/MacEditor'
MAP = '/Game/Showcase/Maps/Manhattan_Island'
PRE = 1.5

ap = argparse.ArgumentParser()
ap.add_argument('tag'); ap.add_argument('--sim', action='store_true'); ap.add_argument('--cases')
ap.add_argument('--realtime', type=int, default=0, help='owner 2026-10-16 (landing camera seizure only in live play): real variable frame time capped at N fps instead of the fixed 1/60 s step')
ap.add_argument('--scratch', default=str(Path.home() / 'sm2-invincible-cache'))
ap.add_argument('--game-arg', action='append', default=[]); ap.add_argument('--keep-frames', action='store_true')
ap.add_argument('--timeout', type=int, default=1500)
a = ap.parse_args()

meta = json.loads((CASES_DIR / 'cases.json').read_text())
names = list(meta)
if a.cases:
    want = a.cases.split(',')
    names = [n for n in names if any(n == w or n.startswith(w + '_') for w in want)]
work = Path(a.scratch) / a.tag
docs = (ROOT / 'docs/invincible/captures' / a.tag) if not a.sim else (work / 'report')   # sim telemetry stays in the cache
work.mkdir(parents=True, exist_ok=True)
docs.mkdir(parents=True, exist_ok=True)
head = subprocess.run(['git', 'rev-parse', '--short=8', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
dirty = bool(subprocess.run(['git', 'status', '--porcelain', '--', 'unreal/WebHomage/Source'], cwd=ROOT, capture_output=True, text=True).stdout.strip())
run = {'tag': a.tag, 'mode': 'sim-nullrhi' if a.sim else 'render-1080p-fixed60', 'source_head': head, 'source_dirty': dirty,
       'map': MAP, 'game_args': a.game_arg, 'cases': []}


def engines_busy():
    ps = subprocess.run(['ps', '-axo', 'stat=,comm='], capture_output=True, text=True).stdout
    return [l for l in ps.splitlines() if l.strip().split(None, 1)[-1].rsplit('/', 1)[-1] in ('UnrealEditor', 'UnrealEditor-Cmd')]


def run_case(name):
    m = meta[name]
    d = work / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    script = CASES_DIR / (name + '.json')
    csv_path = d / (name + '_telemetry.csv')
    quit_t = m['quit'] + (0 if a.sim else PRE) + 5.0   # the quit clock counts map-load time and breach slow-mo the script clock does not
    args = [str(UE), str(UE_DIR / 'WebHomage.uproject'), MAP, '-game', '-NoCrashReports', '-NoSound', '-NoVSync', '-notraceserver',
            '-WHNoMouseCapture', '-WHShotDir=%s' % d, '-WHShotName=%s' % name, '-abslog=%s' % (d / (name + '.log')),
            '-WHTravScript=%s' % script, '-WHTravCsv=%s' % csv_path, *([] if a.realtime else ['-benchmark', '-fps=60']), '-WHSuit=invincible',
            '-WHQuitAt=%.2f' % quit_t]
    if '-WHRescue=1' not in m['args']:
        args.append('-WHRescue=0')
    if a.sim:
        args += ['-nullrhi', '-ResX=640', '-ResY=360', '-ExecCmds=t.MaxFPS %d' % (a.realtime or 240)]
    else:
        for f in SHOTS.glob('MovieFrame*.png'): f.unlink()
        args += ['-ResX=1920', '-ResY=1080', '-ForceRes', '-RenderOffScreen', '-UserDir=%s/' % USER, '-WHProfile=playable', '-WHResScale=100',
                 '-dumpmovie', '-WHMovieAsync', '-WHTravMask', '-WHTravPreroll=%s' % PRE,
                 '-WHPerfPreset=%s' % (UE_DIR / 'Config/PerfPlayableFast.cvars'),
                 '-ExecCmds=t.MaxFPS 30,r.ScreenPercentage 100,r.AntiAliasingMethod 4']
    args += m['args'] + a.game_arg
    if (GPU_DIR / 'PAUSED').exists():
        sys.exit('GPU coordinator PAUSED: not launching (never clear PAUSED)')
    cmd = [str(GPU_SH), 'capture', '--label', 'sm2-invincible-%s-%s' % (a.tag, name), '--json', str(d / 'slot.json'), '--'] + args
    t0 = time.time()
    with open(d / 'launcher.log', 'w') as lg:
        p = subprocess.Popen(cmd, stdout=lg, stderr=subprocess.STDOUT, cwd=ROOT, env=dict(os.environ, GPU_SLOT_DIR=str(GPU_DIR)))
        try:
            p.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:   # gpu_slot stops its own child: SIGTERM, 60 s, SIGKILL last resort
            p.terminate()
            try: p.wait(timeout=90)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
    wall = time.time() - t0
    rows = csv_path.read_text().count('\n') - 1 if csv_path.exists() else 0
    n_case = rows
    if rows > 0:   # the case ends at its script time; the quit margin's tail frames are dropped from telemetry and movie
        lines = csv_path.read_text().splitlines()
        body = [l for l in lines[1:] if float(l.split(',')[1]) <= m['quit'] + 1e-6]
        n_case = len(body)
        csv_path.write_text('\n'.join([lines[0]] + body) + '\n')
    rec = {'case': name, 'rc': p.returncode, 'wall_s': round(wall, 1), 'rows': rows}
    if not a.sim:
        frames = sorted(SHOTS.glob('MovieFrame*.png'))
        fd = d / 'frames'; fd.mkdir(exist_ok=True)
        for f in frames: shutil.move(str(f), str(fd / f.name))
        skip = max(0, len(frames) - rows)
        rec.update(frames_rendered=len(frames), preroll_cut=skip)
        keep = sorted(fd.glob('MovieFrame*.png'))[skip:skip + n_case]
        rec['frames_kept'] = len(keep)
        lst = d / 'frames.txt'
        lst.write_text(''.join("file '%s'\nduration 0.0166667\n" % f for f in keep))
        if keep:
            mp4 = docs / (name + '.mp4')
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-r', '60', '-c:v', 'libx264',
                            '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'medium', '-movflags', '+faststart', str(mp4)], check=False)
            idx = [int(i * (len(keep) - 1) / 7) for i in range(8)]
            tiles = [str(keep[i]) for i in idx]
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + sum([['-i', t] for t in tiles], []) +
                           ['-filter_complex', ''.join('[%d:v]scale=480:-1[v%d];' % (i, i) for i in range(8)) +
                            ''.join('[v%d]' % i for i in range(8)) + 'xstack=inputs=8:layout=0_0|w0_0|w0+w1_0|w0+w1+w2_0|0_h0|w0_h0|w0+w1_h0|w0+w1+w2_h0',
                            '-q:v', '4', str(docs / (name + '_sheet.jpg'))], check=False)
            rec['mp4_mb'] = round(mp4.stat().st_size / 1048576, 2) if mp4.exists() else 0
            # per-frame mean luma (0-255) for the pixel visibility gate in check_flight.py (frame i = telemetry row i)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(mp4), '-vf',
                            'signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=%s' % (d / 'luma.txt'), '-f', 'null', '-'], check=False)
            if (d / 'luma.txt').exists(): shutil.copy(d / 'luma.txt', docs / (name + '_luma.txt'))
        if not a.keep_frames:
            shutil.rmtree(fd, ignore_errors=True)
    if csv_path.exists():
        shutil.copy(csv_path, docs / csv_path.name)
    print(json.dumps(rec), flush=True)
    return rec


crashes = 0
for n in names:
    busy = engines_busy()
    stuck = [l for l in busy if l.split()[0][0] in 'EZ']
    if stuck:
        sys.exit('an Unreal process is stuck exiting (%s): not launching' % stuck)
    rec = run_case(n)
    run['cases'].append(rec)
    if rec['rows'] == 0:
        crashes += 1
        print('%s: no telemetry (rc %s) -- see %s' % (n, rec['rc'], work / n / (n + '.log')), flush=True)
        if crashes >= 2:
            print('two engine runs without telemetry: stopping (no auto-relaunch after two crashes)', flush=True)
            break
(docs / 'RUN.json').write_text(json.dumps(run, indent=1) + '\n')
subprocess.run([sys.executable, str(Path(__file__).resolve().parent / 'check_flight.py'), str(work), str(docs)] + ['--cases', ','.join(r['case'] for r in run['cases'])])
