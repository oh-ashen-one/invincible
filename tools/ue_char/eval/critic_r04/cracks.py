import sys,cv2,numpy as np
from ultralytics import YOLO
m=YOLO('/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt')
for p in sys.argv[1:]:
    im=cv2.imread(p); H,W=im.shape[:2]
    r=m.predict(im,classes=[0],conf=0.35,verbose=False,device=__import__('os').environ.get('YOLO_DEVICE','mps'),imgsz=1920,retina_masks=True)[0]
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
    tot=0; rep=[]
    for k,mk in enumerate(r.masks.data.cpu().numpy()):
        mk=(mk>0.5).astype(np.uint8)
        e=cv2.erode(mk,np.ones((9,9),np.uint8))
        med=np.median(hsv[...,2][e>0]) if e.sum() else 255
        if med>140 or e.sum()<2000: continue
        bright=((hsv[...,2]-med)>90)&(e>0)
        n,lab,st,_=cv2.connectedComponentsWithStats(bright.astype(np.uint8))
        comps=[s for s in st[1:] if 6<=s[4]<=600 and max(s[2],s[3])>=3*min(s[2],s[3])]
        x1,y1,x2,y2=r.boxes.xyxy[k].cpu().numpy().astype(int)
        rep.append((x1,y1,x2-x1,y2-y1,len(comps),int(bright.sum())))
        tot+=len(comps)
    print(p.split('/')[-1],'dark-clothed people',len(rep),'bright sliver comps total',tot)
    for q in sorted(rep,key=lambda q:-q[4])[:8]: print('  bbox',q[:4],'slivers',q[4],'px',q[5])
