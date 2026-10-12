import json,subprocess,csv,sys
from pathlib import Path
ROOT=Path('/Users/midirstudio2/spider-man-2'); OUT=ROOT/'docs/night1/traversal/scripts/final/live'
base=json.load(open(ROOT/'docs/night1/traversal/scripts/final/s1_swing_chain.json')); base.pop('tune',None)
CH=dict(autoChain=True,releasePhase=0.55,gap=0.9,repressVz=99.0,trickEvery=0,skyEvery=0,skyTricks=1,skyRepressH=30,skyPhase=0.8,skyMax=2.8)
presses=[]
def build():
    keys=[{"t":0.0,"move":[0,1],"heading":-90,"swing":False},dict({"t":0.4},**CH)]
    for t in presses: keys+= [{"t":t,"trick":True},{"t":t+0.1,"trick":False}]
    keys.sort(key=lambda k:k['t'])
    d=dict(base); d['name']='live_fix_clip'; d['keys']=keys; d['note']='s1-style chain (gap 0.9 s) + three mid-air F presses 0.4 s after a release; default tuning'
    (OUT/'live_fix_clip.json').write_text(json.dumps(d,indent=1))
for it in range(3):
    build()
    subprocess.run([sys.executable,str(ROOT/'tools/final/swing/probe.py'),str(OUT/'live_fix_clip.json'),'--quit','16.5','--out','/Users/midirstudio2/sm2-n1/_scratch/final/swing/live3/it%d'%it],capture_output=True)
    R=list(csv.DictReader(open('/Users/midirstudio2/sm2-n1/_scratch/final/swing/live3/it%d/live_fix_clip/route_telemetry.csv'%it)))
    f=lambda r,k: float(r[k])
    rel=[f(R[i],'t') for i in range(1,len(R)) if R[i-1]['mode']=='swing' and R[i]['mode']!='swing']
    cand=[t for t in rel if all(abs(t+0.4-p)>2.5 for p in presses) and t+0.4>presses[-1] if presses] if presses else rel
    nxt=[t for t in rel if (not presses or t>presses[-1]+0.5)]
    print('iter',it,'releases',[round(x,2) for x in rel],'presses',presses,flush=True)
    presses.append(round(nxt[0]+0.4,2) if nxt else 5.0)
build(); print('final presses',presses)
