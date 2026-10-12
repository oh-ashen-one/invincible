# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Overlay of what the critic's cracks.py flags (red) so it can be read by eye: python crack_view.py STILL.jpg OUT.jpg (YOLO on CPU)."""
import sys,cv2,numpy as np,os
from ultralytics import YOLO
m=YOLO('/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt')
p=sys.argv[1]; out=sys.argv[2]
im=cv2.imread(p); H,W=im.shape[:2]
r=m.predict(im,classes=[0],conf=0.35,verbose=False,device='cpu',imgsz=1920,retina_masks=True)[0]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
ov=im.copy(); allc=[]
for k,mk in enumerate(r.masks.data.cpu().numpy()):
    mk=(mk>0.5).astype(np.uint8)
    e=cv2.erode(mk,np.ones((9,9),np.uint8))
    med=np.median(hsv[...,2][e>0]) if e.sum() else 255
    if med>140 or e.sum()<2000: continue
    bright=((hsv[...,2]-med)>90)&(e>0)
    n,lab,st,_=cv2.connectedComponentsWithStats(bright.astype(np.uint8))
    for i,s in enumerate(st[1:],1):
        if 6<=s[4]<=600 and max(s[2],s[3])>=3*min(s[2],s[3]):
            ov[lab==i]=(0,0,255); allc.append((int(s[0]),int(s[1]),int(s[2]),int(s[3]),int(s[4])))
print(len(allc)); print(allc)
cv2.imwrite(out,cv2.resize(ov[700:2000,0:3840],None,fx=0.5,fy=0.5),[cv2.IMWRITE_JPEG_QUALITY,88])
