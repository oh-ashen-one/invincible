import sys, os, numpy as np
sys.path.insert(0,'/Users/midir/sm2-n1/_scratch/characters/r16/dev')
import posed_render as PR
WT='/Users/midir/sm2-n1/characters'
import glbedit, hero_shoulder_r14 as HS, meshio, hero_weights_r12 as hw
glb=sys.argv[1]; t=float(sys.argv[2]) if len(sys.argv)>2 else 0.5
g=glbedit.Glb(glb); _,P,N,UV,J,W,F=HS.read_body(g)
X,Nn,UV,F=PR.posed(glb,'idle',t)
P=P.astype(np.float64); X=X.astype(np.float64)
E=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); E=np.unique(np.sort(E,1),axis=0)
u=X-P
L=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)
du=np.linalg.norm(u[E[:,0]]-u[E[:,1]],axis=1)/np.maximum(L,1e-5)
c=0.5*(P[E[:,0]]+P[E[:,1]])
box=(np.abs(c[:,0])>0.10)&(np.abs(c[:,0])<0.26)&(c[:,1]>1.15)&(c[:,1]<1.45)&(c[:,2]>-0.07)
names=meshio.load_body()['names']
k=np.where(box)[0][np.argsort(-du[box])[:25]]
for e in k:
    a,b=E[e]
    print('edge strain %.2f  L %.1fmm  P %s  w_a %s  w_b %s'%(du[e],L[e]*1000,np.round(c[e],3), [(names[J[a][q]],round(float(W[a][q]),2)) for q in range(4) if W[a][q]>0.02],[(names[J[b][q]],round(float(W[b][q]),2)) for q in range(4) if W[b][q]>0.02]))
print('box edges',box.sum(),'strain p50 %.3f p99 %.3f max %.3f'%(np.median(du[box]),np.percentile(du[box],99),du[box].max()))
