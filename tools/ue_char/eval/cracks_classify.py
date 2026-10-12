import sys,cv2,numpy as np,json
from ultralytics import YOLO
m=YOLO('/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt')
p=sys.argv[1]
im=cv2.imread(p); H,W=im.shape[:2]
r=m.predict(im,classes=[0],conf=0.35,verbose=False,device='mps',imgsz=1920,retina_masks=True)[0]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
tot={'head_hair_face':0,'hand_arm_skin':0,'cloth_or_other':0}
rows=[]
for k,mk in enumerate(r.masks.data.cpu().numpy()):
    mk=(mk>0.5).astype(np.uint8)
    e=cv2.erode(mk,np.ones((9,9),np.uint8))
    med=np.median(hsv[...,2][e>0]) if e.sum() else 255
    if med>140 or e.sum()<2000: continue
    x1,y1,x2,y2=r.boxes.xyxy[k].cpu().numpy().astype(int)
    bright=((hsv[...,2]-med)>90)&(e>0)
    n,lab,st,_=cv2.connectedComponentsWithStats(bright.astype(np.uint8))
    c=dict(head_hair_face=0,hand_arm_skin=0,cloth_or_other=0)
    for i,s in enumerate(st[1:],1):
        if 6<=s[4]<=600 and max(s[2],s[3])>=3*min(s[2],s[3]):
            mh=hsv[lab==i]; h,sat=np.median(mh[:,0]),np.median(mh[:,1])
            cy=s[1]+s[3]/2
            if cy<y1+0.16*(y2-y1): c['head_hair_face']+=1
            elif h<25 and sat>45: c['hand_arm_skin']+=1
            else: c['cloth_or_other']+=1
    rows.append(dict(bbox=[int(x1),int(y1),int(x2-x1),int(y2-y1)],**c))
    for kk in tot: tot[kk]+=c[kk]
print(json.dumps(dict(image=p.split('/')[-1],totals=tot,per_person=rows)))
