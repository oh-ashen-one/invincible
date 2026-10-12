#!/usr/bin/env python3
"""Captures one final-loop clip (SPEC_FINAL shot list): real -game, playable profile + Fast preset, 1920x1080 output, 100 % internal, TSR, fixed 1/60 s, -dumpmovie, 1.5 s pre-roll cut,
the default (Tessera) suit. Multi-case clips (s2, s3) run one engine per case and are concatenated. One engine at a time through with_holder.sh.
outputs: <scratch>/<round>/<clip>/<case>/{frames/, route_telemetry.csv, route.log}; <docs round dir>/<clip>.mp4 (<= 15 MB), <clip>_telemetry.csv (cases concatenated, extra columns case, clip_t), <clip>_render.json
usage: run_clip.py <round> <clip> [--map island|island-night] [--cases c1,c2] [--crf 22] [--keep-frames] [--scratch-root ABS_PATH] [--cleanup-case-frames]"""
import argparse, csv, json, os, shutil, signal, subprocess, sys, time
from pathlib import Path
from cache_safety import cache_work, scratch_root, validate_and_cleanup

ROOT = Path(__file__).resolve().parents[3]
SCR = Path.home() / 'sm2-n1/_scratch/final/swing'
SHOTS = ROOT / 'unreal/WebHomage/Saved/Showcase/User/Saved/Screenshots/MacEditor'   # play.py runs with -UserDir=Saved/Showcase/User/
PRE = 1.5
UE = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor')
GPU = Path.home() / '.cache/gpu-slot'
MAPS = {'island': '/Game/Showcase/Maps/Manhattan_Island', 'island-night': '/Game/Showcase/Maps/Manhattan_Island_Night'}


def stop_tree(proc):
    """SIGTERM the launcher (gpu_slot.py / guarded_preview stop their own child), 90 s, SIGKILL last resort."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=90)
    except subprocess.TimeoutExpired:
        proc.kill(); proc.wait()


def launch_case(d, name, q, game_map, log):
    """One case's engine run. Primary: with_holder.sh -> play.py -> guarded_preview (the round-04 path). If that cannot admit
    (a foreign loop parks the coordinator: no engine starts within 180 s), fall back to the coordinator's FIFO queue
    (tools/gpu/gpu_slot.sh capture -- the M1 commandlet path) around the same engine command. Both paths honor PAUSED, the
    holders and the queue at ~/.cache/gpu-slot; the fallback additionally repeats play.py's foreign-engine process check.
    Returns True when the engine ran (route.log exists); False = never admitted (safe to retry)."""
    cmd = [str(ROOT / 'tools/showcase/with_holder.sh'), 'python3', str(ROOT / 'tools/showcase/play.py'), '--map', game_map, '--profile', 'playable', '--res-scale', '100', '--res', '1920x1080',
           '--capture', str(d), '--name', 'route', '--script', str(ROOT / 'docs/night1/traversal/scripts/final' / (name + '.json')), '--quit', str(q + PRE), '--timeout', '3000',
           '--game-arg=-benchmark', '--game-arg=-fps=60', '--game-arg=-dumpmovie', '--game-arg=-WHTravMask', '--game-arg=-WHSuit=tessera', '--game-arg=-WHMovieAsync', '--game-arg=-WHTravPreroll=%s' % PRE, '--game-arg=-WHPerfPreset=%s' % (ROOT / 'unreal/WebHomage/Config/PerfPlayableFast.cvars')]
    if a.tune: cmd.append('--game-arg=-WHTravTune=%s' % a.tune)   # round 08: probe override for Rope* floats (the round itself must run on the shipped defaults)
    for arg in a.game_arg: cmd.append('--game-arg=' + arg)
    cmd.append('--launch')
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
    t0 = time.time()
    while proc.poll() is None and not (d / 'route.log').exists() and time.time() - t0 < 180:
        time.sleep(3)
    if proc.poll() is None and not (d / 'route.log').exists():
        stop_tree(proc)   # the primary path never started the engine (it had launched nothing yet)
        log.write('\n[run_clip] primary path (with_holder/play.py) not admitted within 180 s; trying the coordinator FIFO queue (gpu_slot.sh capture)\n'); log.flush()
    elif proc.poll() is None:
        proc.wait()       # the engine is up: let the capture run out
    if (d / 'route.log').exists():
        return True
    # ---- fallback: queue for a capture slot at the same coordinator (never direct, never bypassing PAUSED / holders)
    if (GPU / 'PAUSED').exists():
        log.write('[run_clip] coordinator PAUSED; refusing the queued launch too\n'); log.flush()
        return False
    engines = subprocess.run(['ps', '-axo', 'comm'], capture_output=True, text=True).stdout
    if any(l.rsplit('/', 1)[-1] in ('UnrealEditor', 'UnrealEditor-Cmd', 'Blender', 'blender', 'Unity') for l in engines.splitlines()):
        log.write('[run_clip] a renderer-bearing engine process exists; not launching under the queue path this attempt\n'); log.flush()
        return False
    r = subprocess.run(['python3', str(ROOT / 'tools/showcase/check.py')], capture_output=True, text=True)
    try:
        problems = json.loads(r.stdout)['missing']
    except (ValueError, KeyError):
        problems = ['check.py produced no report']
    if problems:
        sys.exit('Content is incomplete: ' + ', '.join(problems))
    user = ROOT / 'unreal/WebHomage/Saved/Showcase/User'
    execs = ['t.MaxFPS 0', 'r.ScreenPercentage 100', 'r.AntiAliasingMethod 4']
    game_args = ['-game', '-ResX=1920', '-ResY=1080', '-ForceRes', '-NoCrashReports', '-NoSound', '-NoVSync', '-notraceserver',
                 '-WHNoMouseCapture', '-UserDir=%s/' % user, '-WHShotDir=%s' % d, '-WHShotName=route', '-abslog=%s' % (d / 'route.log'), '-RenderOffScreen',
                 '-WHTravScript=%s' % (ROOT / 'docs/night1/traversal/scripts/final' / (name + '.json')), '-WHProfile=playable', '-WHResScale=100',
                 '-benchmark', '-fps=60', '-dumpmovie', '-WHTravMask', '-WHSuit=tessera', '-WHMovieAsync', '-WHTravPreroll=%s' % PRE,
                 '-WHPerfPreset=%s' % (ROOT / 'unreal/WebHomage/Config/PerfPlayableFast.cvars'),
                 '-WHQuitAt=%s' % (q + PRE), '-ExecCmds=' + ','.join(execs)]
    if a.tune: game_args.append('-WHTravTune=%s' % a.tune)
    game_args.extend(a.game_arg)
    env = dict(os.environ, GPU_SLOT_DIR=str(GPU))
    qcmd = [str(ROOT / 'tools/gpu/gpu_slot.sh'), 'capture', '--label', 'final-swing-%s-%s' % (a.round, name), '--',
            str(UE), str(ROOT / 'unreal/WebHomage/WebHomage.uproject'), MAPS[game_map], *game_args]
    proc = subprocess.Popen(qcmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, env=env)
    try:
        proc.wait(timeout=1200)   # engine self-quits at -WHQuitAt; the cap is only a stuck-run guard
    except subprocess.TimeoutExpired:
        log.write('[run_clip] queued capture exceeded 1200 s; SIGTERM to gpu_slot (it stops the engine: SIGTERM, 60 s, SIGKILL last resort)\n'); log.flush()
        stop_tree(proc)
    return (d / 'route.log').exists()
ap = argparse.ArgumentParser()
ap.add_argument('round'); ap.add_argument('clip'); ap.add_argument('--map'); ap.add_argument('--cases'); ap.add_argument('--crf', type=int, default=22); ap.add_argument('--keep-frames', action='store_true'); ap.add_argument('--q', type=float, help='dev render: quit time (s after the cut) for every case; the outputs get the suffix _dev'); ap.add_argument('--reuse', action='store_true', help='post-process frames / telemetry left by an earlier engine run of this case (no launch)')
ap.add_argument('--tune', help='probe: extra -WHTravTune=Name=V,... passed to the game (not used for the round captures)')
ap.add_argument('--game-arg', action='append', default=[], help='extra Unreal argument for a scoped diagnostic; repeat as needed')
ap.add_argument('--scratch-root', help='absolute task-owned cache root; a normal run recaptures cases there; default is the historical shared cache')
ap.add_argument('--cleanup-case-frames', action='store_true', help='delete per-case frames_done only after the final MP4, telemetry and metadata validate; requires --scratch-root')
a = ap.parse_args()
if a.cleanup_case_frames and not a.scratch_root: ap.error('--cleanup-case-frames requires --scratch-root')
if a.cleanup_case_frames and a.reuse: ap.error('--cleanup-case-frames cannot be combined with --reuse')
try:
    if a.scratch_root: SCR = scratch_root(a.scratch_root, ROOT)
    work = cache_work(SCR, a.round, a.clip)
    if not (SHOTS.resolve() == ROOT or ROOT in SHOTS.resolve().parents):
        raise ValueError('screenshot path resolves outside this checkout')
except ValueError as e:
    ap.error(str(e))
clips = json.loads((ROOT / 'docs/night1/traversal/scripts/final/clips.json').read_text())
cases = clips[a.clip]
if a.cases: cases = [c for c in cases if c[0] in a.cases.split(',')]
if a.q: cases = [(n, a.q) for n, _ in cases]
game_map = a.map or ('island-night' if a.clip.startswith('s5') else 'island')
docs = ROOT / 'docs/night1/final/swing' / a.round; docs.mkdir(parents=True, exist_ok=True)
work.mkdir(parents=True, exist_ok=True)
fast = ROOT / 'unreal/WebHomage/Config/PerfPlayableFast.cvars'
info = {'clip': a.clip, 'map': game_map, 'cases': []}
all_rows, total_frames, n_out = [], 0, 0
out_frames = work / 'all_frames'; shutil.rmtree(out_frames, ignore_errors=True); out_frames.mkdir(parents=True)
clip_t = 0.0
for name, q in cases:
    d = work / name
    done = d / 'frames_done'   # round 05: per-case resume cache (frames + telemetry + log survive a later case's admission failure)
    t0 = time.time()
    rows = list(csv.DictReader((d / 'route_telemetry.csv').open())) if (d / 'route_telemetry.csv').exists() else []
    cached = (a.reuse or not a.scratch_root) and bool(rows) and (d / 'route.log').exists() and done.exists() and any(done.glob('MovieFrame*.png'))
    if a.reuse and not cached:
        sys.exit('%s: --reuse but no complete per-case cache at %s' % (name, d))
    if not cached:
        attempt = 0
        while True:   # admission retry: the shared GPU coordinator is contended at night; a refusal never starts the engine
            attempt += 1
            shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
            for f in SHOTS.glob('MovieFrame*.png'): f.unlink()
            with open(work / (name + '.launcher.log'), 'a') as lg:
                lg.write('\n=== %s attempt %d %s ===\n' % (name, attempt, time.strftime('%H:%M:%S')))
                ran = launch_case(d, name, q, game_map, lg)
            rows = list(csv.DictReader((d / 'route_telemetry.csv').open())) if (d / 'route_telemetry.csv').exists() else []
            frames_now = sorted(SHOTS.glob('MovieFrame*.png'))
            if rows and frames_now:
                done.mkdir(parents=True)
                for f in frames_now: shutil.move(str(f), str(done / f.name))
                break
            if ran:
                sys.exit('%s: the engine ran but produced no telemetry / frames (rows %d, frames %d); log %s -- not auto-relaunching, diagnose first' % (name, len(rows), len(frames_now), d / 'route.log'))
            if attempt >= 8:
                sys.exit('%s: no admission after %d attempts (the GPU coordinator never granted a slot)' % (name, attempt))
            print('%s: admission attempt %d refused (no engine started); waiting 120 s' % (name, attempt), flush=True)
            time.sleep(120)
    wall = time.time() - t0
    try:   # engine wall time from the log's first / last stamps (also valid with --reuse)
        import re, datetime
        st = [m.group(1) for m in re.finditer(r'^\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d)', (d / 'route.log').read_text(errors='replace'), re.M)]
        fmt = '%Y.%m.%d-%H.%M.%S'; wall = (datetime.datetime.strptime(st[-1], fmt) - datetime.datetime.strptime(st[0], fmt)).total_seconds() or wall
    except Exception: pass
    frames = sorted(done.glob('MovieFrame*.png'))
    skip = len(frames) - len(rows)
    if skip < 0: sys.exit('%s: fewer frames (%d) than telemetry rows (%d)' % (name, len(frames), len(rows)))
    for f in frames[skip:]:   # link (not move): done/ stays a complete resume cache
        n_out += 1
        try: os.link(str(f), str(out_frames / ('f%06d.png' % n_out)))
        except OSError: shutil.copy2(str(f), str(out_frames / ('f%06d.png' % n_out)))
    for i, rr in enumerate(rows):
        rr['case'] = name; rr['clip_t'] = '%.4f' % (clip_t + float(rr['t'])); rr['clip_frame'] = str(total_frames + i)
    all_rows += rows; total_frames += len(rows); clip_t += float(rows[-1]['t']) + 1 / 60
    info['cases'].append({'case': name, 'frames_rendered': len(frames), 'preroll_frames_cut': skip, 'rows': len(rows), 'wall_s': round(wall, 1), 'fps_render': round(len(frames) / wall, 2)})
    print(name, info['cases'][-1], flush=True)
    shutil.copy(d / 'route.log', work / (name + '.log'))
with (docs / (a.clip + ('_dev' if a.q else '') + '_telemetry.csv')).open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)
tag = a.clip + ('_dev' if a.q else '')
mp4 = docs / (tag + '.mp4')
crf = a.crf
while True:
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', '60', '-i', str(out_frames / 'f%06d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(crf), '-preset', 'slow', '-movflags', '+faststart', str(mp4)], check=True)
    if mp4.stat().st_size <= 15 * 1024 * 1024 or crf >= 36: break
    crf += 3
info.update({'frames': total_frames, 'duration_s': round(total_frames / 60, 2), 'mp4_mb': round(mp4.stat().st_size / 1048576, 2), 'crf': crf, 'wall_s_total': round(sum(c['wall_s'] for c in info['cases']), 1)})
metadata = docs / (tag + '_render.json')
metadata.write_text(json.dumps(info, indent=1))
if a.cleanup_case_frames:
    validate_and_cleanup(SCR, work, mp4, docs / (tag + '_telemetry.csv'), metadata, total_frames, [name for name, _ in cases])
if not a.keep_frames: shutil.rmtree(out_frames)
print(json.dumps(info))
