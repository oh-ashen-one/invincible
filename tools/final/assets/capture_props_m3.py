#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""PA verification captures (offline visual evidence, never perf): the real -game binary on a PropsM3 map, matched cameras (-WHShotCam),
playable profile + Fast preset at 1920x1080, through tools/m5/guarded_preview.py (exclusive admission on ~/.cache/gpu-slot: it refuses while
any holder / waiter / renderer exists, so this tool WAITS politely and retries; it never bypasses PAUSED, the queue or a holder).

usage: capture_props_m3.py --map /Game/PropsM3/Maps/PropsM3_IslandCheck_Golden --cams cams.json --name golden --out DIR [--dump prims.csv] [--game-arg ...]
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / 'unreal/WebHomage'
GPU = Path.home() / '.cache/gpu-slot'
UE = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
PRESET = PROJECT / 'Config/PerfPlayableFast.cvars'
ENGINES = {'unrealeditor', 'unrealeditor-cmd', 'blender', 'unity', 'unityshadercompiler'}


def busy():
    if (GPU / 'PAUSED').exists(): return 'PAUSED'
    if any((GPU / 'queue').iterdir()): return 'waiters queued'
    if any((GPU / 'holders').glob('*.json')): return 'holder present'
    t = subprocess.check_output(['ps', '-axo', 'pid=,comm='], text=True)
    e = [l for l in t.splitlines() if l.strip().split(None, 1)[-1].rsplit('/', 1)[-1].lower() in ENGINES and '/Unity Hub.app/' not in l]
    return ('engines: ' + '; '.join(x.strip() for x in e)) if e else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', required=True); ap.add_argument('--cams', required=True); ap.add_argument('--name', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--dump'); ap.add_argument('--wait', type=float, default=10.0)
    ap.add_argument('--game-arg', action='append', default=[]); ap.add_argument('--timeout', type=int, default=900)
    ap.add_argument('--max-wait', type=int, default=7200)
    a = ap.parse_args()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    cams = json.loads(Path(a.cams).read_text())
    quit_at = max(c['t'] for c in cams) + a.wait + 4.0
    user = Path.home() / 'sm2-n1/_scratch/final/assets/ue_user'; user.mkdir(parents=True, exist_ok=True)
    log = out / f'{a.name}.log'
    args = ['-game', '-ResX=1920', '-ResY=1080', '-ForceRes', '-NoCrashReports', '-NoSound', '-NoVSync', '-notraceserver', '-WHNoMouseCapture',
            f'-UserDir={user}/', f'-WHShotDir={out}', f'-WHShotName={a.name}', f'-abslog={log}', '-RenderOffScreen',
            f'-WHShotCam={Path(a.cams).resolve()}', f'-WHShotCamWait={a.wait}', '-WHProfile=playable', '-WHResScale=100', f'-WHPerfPreset={PRESET}']
    if a.dump: args.append(f'-WHTravDumpPrims={Path(a.dump).resolve()}')
    args += a.game_arg + [f'-WHQuitAt={quit_at}', '-ExecCmds=t.MaxFPS 0,r.ScreenPercentage 100,r.AntiAliasingMethod 4']
    cmd = [str(ROOT / 'tools/m5/guarded_preview.py'), '--', UE, str(PROJECT / 'WebHomage.uproject'), a.map, *args]
    env = dict(os.environ, GPU_SLOT_DIR=str(GPU))
    t0 = time.time(); last = None
    while True:
        why = busy()
        if why is None: break
        if why == 'PAUSED': raise SystemExit('shared GPU PAUSED: not launching (never cleared here)')
        if why != last: print(time.strftime('%H:%M:%S'), 'waiting for the shared GPU:', why, flush=True); last = why
        if time.time() - t0 > a.max_wait: raise SystemExit('gave up waiting for the shared GPU after %d s' % a.max_wait)
        time.sleep(20)
    print(time.strftime('%H:%M:%S'), 'launch:', ' '.join(cmd), flush=True)
    proc = subprocess.Popen(cmd, env=env)
    deadline = time.monotonic() + a.timeout
    try:
        while proc.poll() is None:
            if time.monotonic() > deadline:
                print('capture timeout: SIGTERM to guarded_preview (it stops its engine child: SIGTERM, 60 s, SIGKILL last resort)')
                proc.terminate()
                try: proc.wait(timeout=90)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait()
                break
            time.sleep(1)
    except KeyboardInterrupt:
        proc.terminate(); proc.wait(timeout=90)
    shots = sorted(p.name for p in out.glob(f'{a.name}_*.png'))
    print('rc', proc.returncode, 'shots', len(shots), shots, flush=True)
    raise SystemExit(proc.returncode or (0 if shots or not cams else 3))


if __name__ == '__main__':
    main()
