# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). Director spec instrument, 2026-09-29. Run with a venv holding ultralytics+opencv (see specs README lines).
# All person detections (with mask stats) at a given step; overlay sheets with IDs for manual hero pick.
import sys, cv2, json, numpy as np
from ultralytics import YOLO
clip, out, step = sys.argv[1], sys.argv[2], int(sys.argv[3])
m = YOLO('yolo11x-seg.pt')
cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS); i=0; D=[]; tiles=[]
while True:
    ok, fr = cap.read()
    if not ok: break
    if i % step == 0:
        H,W = fr.shape[:2]
        r = m.predict(fr, classes=[0], conf=0.06, verbose=False, device='mps', imgsz=1920, retina_masks=True)[0]
        dets=[]
        if r.boxes is not None:
            for k,(b,c) in enumerate(zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy())):
                mk = cv2.resize(r.masks.data[k].cpu().numpy().astype(np.uint8),(W,H))>0 if r.masks is not None else None
                ys,xs = np.nonzero(mk) if mk is not None else ([],[])
                d = dict(id=len(dets), conf=float(c), box=[float(b[0]/W),float(b[1]/H),float(b[2]/W),float(b[3]/H)])
                if len(ys):
                    d['mbox']=[xs.min()/W, ys.min()/H, (xs.max()+1)/W, (ys.max()+1)/H]; d['mpx']=int(len(ys))
                    g = cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY).astype(np.float32)
                    lap = np.abs(cv2.Laplacian(g,cv2.CV_32F))
                    d['lap_in']=float(lap[mk].mean())
                    ring = cv2.dilate(mk.astype(np.uint8), np.ones((41,41),np.uint8)).astype(bool) & ~cv2.dilate(mk.astype(np.uint8), np.ones((9,9),np.uint8)).astype(bool)
                    d['lap_ring']=float(lap[ring].mean()) if ring.any() else -1
                    d['luma_in']=float(g[mk].mean())
                dets.append(d)
                x0,y0,x1,y1=[int(v) for v in b]
                cv2.rectangle(fr,(x0,y0),(x1,y1),(0,255,0),3)
                cv2.putText(fr,str(d['id']),(x0,max(y0-8,40)),0,2.2,(0,0,0),10); cv2.putText(fr,str(d['id']),(x0,max(y0-8,40)),0,2.2,(0,255,255),4)
        t=i/fps; D.append(dict(t=round(t,3), dets=dets))
        tl=cv2.resize(fr,(480,270)); cv2.putText(tl,f"{t:.2f}",(380,262),0,0.7,(0,0,0),4); cv2.putText(tl,f"{t:.2f}",(380,262),0,0.7,(255,255,255),2); tiles.append(tl)
    i+=1
json.dump(D, open(out+'_dets.json','w'))
per=20
for s in range(0,len(tiles),per):
    ch=tiles[s:s+per]
    while len(ch)%4: ch.append(np.zeros_like(ch[0]))
    cv2.imwrite(f"{out}_ids_{s//per}.jpg", np.vstack([np.hstack(ch[q:q+4]) for q in range(0,len(ch),4)]), [cv2.IMWRITE_JPEG_QUALITY,78])
print(out, len(D))
