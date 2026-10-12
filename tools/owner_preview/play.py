#!/usr/bin/env python3
"""Check the prepared preview. Opening requires an explicit --launch after owner request."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'unreal/WebHomage'
STATE = PROJECT / 'Saved/OwnerPreview'
GPU = Path(os.environ.get('GPU_SLOT_DIR', str(Path.home() / '.cache/gpu-slot')))
UE = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--launch', action='store_true')
    ap.add_argument('--ultrawide', action='store_true', help='3440x1440 native-display alternate; not 4K output')
    args = ap.parse_args()
    prepared = json.loads((STATE / 'prepared.json').read_text())
    width, height = (3440, 1440) if args.ultrawide else (3840, 2160)
    paused = (GPU / 'PAUSED').read_text().strip() if (GPU / 'PAUSED').exists() else None
    check = {'prepared': prepared['status'], 'map': prepared['map'], 'output_requested': [width, height],
             'internal_scale_requested': 100, 'launch_requested': args.launch,
             'shared_pause': paused, 'runtime_verified': False}
    print(json.dumps(check, indent=2), flush=True)
    if not args.launch:
        print('CHECK ONLY: no process launched. Wait for the owner to request opening.')
        return
    if prepared['status'] != 'prepared_on_disk':
        raise SystemExit('Prepared content is incomplete')
    if paused:
        raise SystemExit('Shared GPU coordinator is paused. Complete the approved recovery/health check first; this launcher never clears PAUSED.')
    process_table = subprocess.check_output(['ps', '-axo', 'pid,stat,comm'], text=True)
    engines = [line for line in process_table.splitlines()
               if line.rsplit('/', 1)[-1] in ('UnrealEditor', 'UnrealEditor-Cmd', 'Blender', 'blender', 'Unity')]
    if engines:
        raise SystemExit('A renderer-bearing engine already exists. Review ownership/health before this manual preview:\n' + '\n'.join(engines))
    # The UserDir override keeps the owner preview's saved settings separate from
    # the integration checkout. WHPreparedPlaytest explicitly applies 100% / Cinematic.
    user = STATE / 'User'
    user.mkdir(exist_ok=True)
    env = dict(os.environ, GPU_SLOT_DIR=str(GPU), GPU_SLOT_CAPTURE_SLOTS='1',
               GPU_SLOT_CAPTURE_MAX_HOLD='0', GPU_SLOT_FOREGROUND='1')
    command = [str(ROOT / 'tools/m5/guarded_preview.py'), '--',
               str(UE), str(PROJECT / 'WebHomage.uproject'), prepared['map'],
               '-game', '-windowed', f'-ResX={width}', f'-ResY={height}', '-ForceRes', '-WinX=0', '-WinY=0',
               '-WHPreparedPlaytest', f'-UserDir={user}/', '-NoCrashReports', '-notraceserver',
               '-ExecCmds=t.MaxFPS 30', f'-abslog={STATE / "owner-play.log"}']
    raise SystemExit(subprocess.call(command, env=env))

if __name__ == '__main__':
    main()
