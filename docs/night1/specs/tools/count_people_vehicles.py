# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). Director spec instrument, 2026-09-29. Run with a venv holding ultralytics+opencv (see specs README lines).
import sys, cv2, json, numpy as np, glob
from ultralytics import YOLO
m=YOLO('yolo11x-seg.pt')
R='/Users/midir/spiderman-learnings/refs/'
clips = sys.argv[1:]
for c in clips:
    p=glob.glob(R+c)[0]; cap=cv2.VideoCapture(p); fps=cap.get(5); i=0; out=[]
    while True:
        ok,im=cap.read()
        if not ok: break
        if i % int(round(fps/2))==0:
            r=m.predict(im,classes=[0,2,3,5,7],conf=0.35,verbose=False,device='mps',imgsz=1920)[0]
            cls=r.boxes.cls.cpu().numpy(); b=r.boxes.xyxy.cpu().numpy()
            hts=(b[:,3]-b[:,1])/im.shape[0]
            ppl=hts[cls==0]
            out.append(dict(t=i/fps, people=int((cls==0).sum()), people_h3=int((ppl>=0.03).sum()), people_h10=int((ppl>=0.10).sum()), vehicles=int(np.isin(cls,[2,3,5,7]).sum()), ph=[round(float(x),3) for x in sorted(ppl,reverse=True)[:8]]))
        i+=1
    P=np.array([o['people'] for o in out]); P3=np.array([o['people_h3'] for o in out]); V=np.array([o['vehicles'] for o in out])
    print(f"{c.split('/')[-1][:40]:40s} n{len(out)} people p10 {np.percentile(P,10):.0f} med {np.median(P):.0f} p90 {np.percentile(P,90):.0f} | people>=3%H med {np.median(P3):.0f} max {P3.max()} | vehicles med {np.median(V):.0f} p90 {np.percentile(V,90):.0f}")
    json.dump(out,open('m/count_'+c.split('/')[-1][:30]+'.json','w'))
