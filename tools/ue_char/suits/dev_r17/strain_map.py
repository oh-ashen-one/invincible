"""Round 17 CPU aid: edge strain of the prepped hero GLB skinned in an idle pose over the WHOLE front torso + head, hotspots listed and a heat-coloured CPU render.
   python3 strain_map.py SK_Hero.glb [t=0.5] [out.png] [az=-25] ; env REGION=torso|head|all"""
import sys, os, numpy as np, cv2
WT='/Users/midir/sm2-n1/characters'
sys.path[:0]=[WT+'/tools/ue_char/suits/dev_r16', WT+'/tools/ue_char/suit8', WT+'/tools/ue_char', WT+'/tools/ue_char/suits', WT+'/tools/skinfit', WT+'/tools/ue_char/heroanim']
import posed_render as PR
import glbedit, hero_shoulder_r14 as HS, meshio, softrender as sr
glb=sys.argv[1]; t=float(sys.argv[2]) if len(sys.argv)>2 else 0.5
out=sys.argv[3] if len(sys.argv)>3 else None; az=float(sys.argv[4]) if len(sys.argv)>4 else -25.0
g=glbedit.Glb(glb); _,P,N,UV,J,W,F=HS.read_body(g)
X,Nn,UV2,F2=PR.posed(glb,'idle',t)
P=P.astype(np.float64); X=X.astype(np.float64)
E=np.unique(np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),1),axis=0)
u=X-P
L=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)
du=np.linalg.norm(u[E[:,0]]-u[E[:,1]],axis=1)/np.maximum(L,1e-5)
c=0.5*(P[E[:,0]]+P[E[:,1]])
reg=os.environ.get('REGION','torso')
if reg=='torso': box=(np.abs(c[:,0])<0.40)&(c[:,1]>0.95)&(c[:,1]<1.50)&(c[:,2]>-0.10)
elif reg=='head': box=(c[:,1]>1.45)&(np.abs(c[:,0])<0.2)
else: box=np.ones(len(c),bool)
names=meshio.load_body()['names']
print('region',reg,'edges',box.sum(),'strain p50 %.3f p90 %.3f p99 %.3f max %.3f'%(np.median(du[box]),np.percentile(du[box],90),np.percentile(du[box],99),du[box].max()))
k=np.where(box)[0][np.argsort(-du[box])[:int(os.environ.get('TOP','30'))]]
for e in k:
    a,b=E[e]
    print('strain %.2f L %.1fmm at %s  wa %s wb %s'%(du[e],L[e]*1000,np.round(c[e],3),[(names[J[a][q]],round(float(W[a][q]),2)) for q in range(4) if W[a][q]>0.02],[(names[J[b][q]],round(float(W[b][q]),2)) for q in range(4) if W[b][q]>0.02]))
if out:
    # orthographic front scatter (x right-is-image-left like the stage front camera: image x = -world x), colour = edge strain at the edge midpoint
    x0,x1,y0,y1=(-0.40,0.40,0.95,1.55); Wd=int(os.environ.get('W','2400')); Hd=int(Wd*(y1-y0)/(x1-x0))
    img=np.full((Hd,Wd,3),30,np.uint8); sel=box&(c[:,2]>-0.02)
    order=np.argsort(du[sel]); idx=np.where(sel)[0][order]
    for e in idx:
        px=int((x1-c[e,0])/(x1-x0)*Wd); py=int((y1-c[e,1])/(y1-y0)*Hd); s_=min(du[e]/float(os.environ.get('SMAX','1.0')),1.0)
        col=(int(255*(1-s_)), int(255*min(1,2*s_) if s_<0.5 else 255*(2-2*s_)), int(255*s_))
        cv2.circle(img,(px,py),2 if s_<0.3 else 4,col,-1)
    for yy in np.arange(1.0,1.55,0.1):
        py=int((y1-yy)/(y1-y0)*Hd); cv2.line(img,(0,py),(Wd,py),(70,70,70),1); cv2.putText(img,'%.1f'%yy,(5,py-3),cv2.FONT_HERSHEY_SIMPLEX,0.6,(200,200,200),1)
    for xx in np.arange(-0.4,0.41,0.1):
        px=int((x1-xx)/(x1-x0)*Wd); cv2.line(img,(px,0),(px,Hd),(70,70,70),1); cv2.putText(img,'%.1f'%xx,(px+3,Hd-8),cv2.FONT_HERSHEY_SIMPLEX,0.6,(200,200,200),1)
    cv2.imwrite(out,img)
