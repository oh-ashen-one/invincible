import sys, cv2, numpy as np
from ultralytics import YOLO
m=YOLO('/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt')
for p in sys.argv[1:]:
    cap=cv2.VideoCapture(p); fps=cap.get(5); i=0; P=[];P3=[];HT=[]
    while True:
        ok,im=cap.read()
        if not ok: break
        if i % int(round(fps/2))==0:
            r=m.predict(im,classes=[0],conf=0.35,verbose=False,device=__import__('os').environ.get('YOLO_DEVICE','mps'),imgsz=1920)[0]
            b=r.boxes.xyxy.cpu().numpy(); h=(b[:,3]-b[:,1])/im.shape[0]
            P.append(len(h)); P3.append(int((h>=0.03).sum())); HT+= list(h)
        i+=1
    P=np.array(P);P3=np.array(P3);HT=np.array(HT)
    print(p.split('/')[-1], 'n',len(P),'people med',np.median(P),'p10',np.percentile(P,10),'max',P.max(),'| >=3%H med',np.median(P3),'| height med %.3f p90 %.3f max %.3f'%(np.median(HT),np.percentile(HT,90),HT.max()))
