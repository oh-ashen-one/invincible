#!/usr/bin/env python3
"""Finite behavioral replays through the shared two-slot GPU coordinator; never performance evidence."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
UE='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
CASES={
 'rest':('rest.json',9,'2.5,5.8,9',True,[]),
 'boost-flip':('boost-flip.json',6,'2,2.4,4.5',True,[]),
 'web-release-zip':('web-release-zip.json',10,'2.8,4.3,8.5',True,[]),
 'swing-on':('../../../docs/night1/traversal/scripts/final/s1_swing_chain.json',6,'3,5',True,[]),
 'swing-off':('../../../docs/night1/traversal/scripts/final/s1_swing_chain.json',6,'3,5',False,[]),
 'settings':('rest.json',4,'3',True,['-WHShowSettings']),
 'music':('rest.json',10,'3,7',True,['-WHMusicStartAt=145','-WHMusicVerify','-WHShowSettings','-WHExecAt=3:pause;7:pause']),
}
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--case',action='append',choices=CASES);a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
proj=ROOT/'unreal/WebHomage';man=proj/'Binaries/Mac/UnrealEditor.modules';dll=man.parent/json.loads(man.read_text())['Modules']['WebHomage'];sha=hashlib.sha256(dll.read_bytes()).hexdigest()
for name in a.case or CASES:
 script,duration,shots,shake,extra=CASES[name]
 user=a.out/(name+'-user');ini=user/'Saved/Config/MacEditor/GameUserSettings.ini';ini.parent.mkdir(parents=True,exist_ok=True);ini.write_text('[/Script/Engine.GameUserSettings]\nVersion=5\n\n[WebHomage.Settings]\nMouseSensitivity=3\nGamepadLookSensitivity=3\nCameraShake='+str(shake)+'\n')
 args=[UE,str(proj/'WebHomage.uproject'),'/Game/Showcase/Maps/Manhattan_Island','-game','-RenderOffScreen','-ResX=1280','-ResY=720','-ForceRes','-NoVSync','-NoCrashReports','-notraceserver','-WHNoMouseCapture',f'-UserDir={user}/',f'-WHShotDir={a.out}',f'-WHShotName={name}',f'-abslog={a.out}/{name}.log',f'-WHTravScript={(HERE/script).resolve()}','-WHProfile=playable','-WHResScale=67','-benchmark','-fps=60','-WHTravMask','-WHTravPreroll=1.5',f'-WHQuitAt={duration+1.5}',f'-WHShotAt={shots}',f'-WHPerfPreset={proj}/Config/PerfPlayableFast.cvars','-ExecCmds=t.MaxFPS 0,r.ScreenPercentage 67,r.AntiAliasingMethod 4',*extra]
 if name!='music':args+=['-NoSound']
 else:
  args=[v for v in args if v not in ('-benchmark','-fps=60')]
  args=[v.replace('t.MaxFPS 0','t.MaxFPS 60') for v in args]
 cmd=[str(ROOT/'tools/gpu/gpu_slot.sh'),'capture','--label','spiderman-feedback-'+name,'--timeout','60','--json',str(a.out/(name+'_slot.json')),'--',*args]
 (a.out/(name+'_command.json')).write_text(json.dumps({'source_binary_sha256':sha,'behavior_only':True,'command':cmd},indent=2)+'\n')
 print('Starting '+name,flush=True)
 with (a.out/(name+'_launcher.log')).open('w') as log:
  result=subprocess.run(cmd,cwd=ROOT,env=dict(os.environ,GPU_SLOT_DIR=str(Path.home()/'.cache/gpu-slot'),GPU_SLOT_CAPTURE_MAX_HOLD='240'),stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(f'{name} failed ({result.returncode}); no automatic retry')
 print('Finished '+name,flush=True)
