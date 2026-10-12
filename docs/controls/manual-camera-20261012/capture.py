#!/usr/bin/env python3
"""Focused, sequential guarded Unreal camera replays. Requires installed UE5.8 and generated assets."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
CASES={
 'high-look':('high-look.json',60,7.5,[]),
 'clear-air':('clear-air.json',60,7.5,[]),
 'mouse-look':('mouse-look.json',60,6,['--exec','wh.MouseSensitivity 3','--game-arg=-WHTravInputTest=mouseLook','--game-arg=-WHMouseTestPx=120']),
 'mouse-extreme':('mouse-look.json',60,6,['--exec','wh.MouseSensitivity 3','--game-arg=-WHTravInputTest=mouseLook','--game-arg=-WHMouseTestPx=1715']),
 'trick':('../../../docs/night1/traversal/scripts/final/s3_c1_fwd.json',60,7,[]),
 'high-look-30':('high-look.json',30,7.5,[]),
 'high-look-120':('high-look.json',120,7.5,[]),
 'wall-look':('wall-look.json',60,7,[]),
}
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--case',action='append',choices=CASES);a=ap.parse_args()
a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
manifest=ROOT/'unreal/WebHomage/Binaries/Mac/UnrealEditor.modules'
binary=manifest.parent/json.loads(manifest.read_text())['Modules']['WebHomage']
sha=hashlib.sha256(binary.read_bytes()).hexdigest()
for name in a.case or CASES:
 script,fps,quit_at,extra=CASES[name]
 cmd=[sys.executable,str(ROOT/'tools/showcase/play.py'),'--map','island','--profile','playable','--res-scale','67','--res','1280x720','--capture',str(a.out),'--name',name,'--script',str((HERE/script).resolve()),'--quit',str(quit_at),'--shots','2.5,3.5,5.5','--game-arg=-benchmark',f'--game-arg=-fps={fps}','--game-arg=-WHTravMask','--game-arg=-WHTravPreroll=1.5',f'--game-arg=-WHPerfPreset={ROOT}/unreal/WebHomage/Config/PerfPlayableFast.cvars','--timeout','180',*extra,'--launch']
 (a.out/(name+'_command.json')).write_text(json.dumps({'dylib_sha256':sha,'fixed_step_hz':fps,'command':cmd},indent=2)+'\n')
 print('Starting '+name,flush=True)
 with (a.out/(name+'_launcher.log')).open('w') as log:
  result=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode: raise SystemExit(f'{name} failed ({result.returncode}); no automatic retry')
 print('Finished '+name,flush=True)
