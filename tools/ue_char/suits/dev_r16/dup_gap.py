import sys, os, json
import numpy as np
from scipy.spatial import cKDTree
WT='/Users/midir/sm2-n1/characters'; S8=WT+'/tools/ue_char/suit8'
sys.path[:0]=[S8, WT+'/tools/ue_char', WT+'/tools/skinfit', WT+'/tools/ue_char/heroanim']
import skinfit, meshio, ganim, glbedit
import hero_weights_r12 as hw, hero_shoulder_r14 as HS
glb=sys.argv[1]
g=glbedit.Glb(glb); _,P,N,UV,J,W,F=HS.read_body(g)
P=P.astype(np.float64); names=meshio.load_body()['names']
dense=hw.dense_of(J,W,len(names))
t=cKDTree(P); pairs=t.query_pairs(1e-6, output_type='ndarray')
print('verts',len(P),'coincident pairs',len(pairs))
dw=np.abs(dense[pairs[:,0]]-dense[pairs[:,1]]).sum(1)
print('weight L1 diff: max %.4f, n>0.01: %d'%(dw.max(), (dw>0.01).sum()))
doc=ganim.Doc(meshio.GLB); j,b=skinfit.read_glb(meshio.GLB)
sk=j['skins'][0]; ibm=skinfit.accessor(j,b,sk['inverseBindMatrices']).reshape(-1,4,4)
Ph=np.concatenate([P,np.ones((len(P),1))],1)
for clip,tt in (('idle',0.0),('idle',1.0),('idle',2.2)):
    Wd=doc.world(doc.sample(doc.tracks(clip),tt))
    M=np.stack([Wd[n]@ibm[k].T for k,n in enumerate(sk['joints'])])
    X=np.einsum('vj,jab,vb->va',dense,M,Ph)[:,:3]
    gap=np.linalg.norm(X[pairs[:,0]]-X[pairs[:,1]],axis=1)
    k=np.argsort(-gap)[:8]
    print(clip,tt,'max gap mm %.2f  n>0.5mm %d'%(gap.max()*1000,(gap>0.0005).sum()), [(np.round(P[pairs[i,0]],3).tolist(), round(gap[i]*1000,2)) for i in k[:5]])
# --- near pairs (border vertices of different faces' islands within 8 mm, not coincident)
import collections
Fl=F.reshape(-1)
# boundary edges (edges used once)
E=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); Es=np.sort(E,1)
u,c=np.unique(Es,axis=0,return_counts=True); bE=u[c==1]; bv=np.unique(bE)
print('boundary verts',len(bv))
tb=cKDTree(P[bv]); pr=tb.query_pairs(0.008,output_type='ndarray')
d=np.linalg.norm(P[bv[pr[:,0]]]-P[bv[pr[:,1]]],axis=1)
pr=pr[d>1e-6]; d=d[d>1e-6]
# only pairs that are not mesh-adjacent
adj=set(map(tuple,Es.tolist()))
keep=np.array([ (min(bv[a],bv[b]),max(bv[a],bv[b])) not in adj for a,b in pr])
pr=pr[keep]; d=d[keep]
ia,ib=bv[pr[:,0]],bv[pr[:,1]]
print('near non-adjacent boundary pairs',len(pr),'dist mm p50 %.2f max %.2f'%(np.median(d)*1000,d.max()*1000))
for clip,tt in (('idle',1.0),):
    Wd=doc.world(doc.sample(doc.tracks(clip),tt))
    M=np.stack([Wd[n]@ibm[k].T for k,n in enumerate(sk['joints'])])
    X=np.einsum('vj,jab,vb->va',dense,M,Ph)[:,:3]
    ch=np.linalg.norm(X[ia]-X[ib],axis=1)-d
    k=np.argsort(-np.abs(ch))[:10]
    print('posed distance change mm max %.2f'%(np.abs(ch).max()*1000), [(np.round(P[ia[i]],3).tolist(), round(d[i]*1000,2), round(ch[i]*1000,2)) for i in k])
sel=(np.abs(P[ia,0])>0.12)&(np.abs(P[ia,0])<0.22)&(P[ia,1]>1.25)&(P[ia,1]<1.37)
print('pairs in armpit-side box', sel.sum(), [(np.round(P[ia[i]],3).tolist(), np.round(P[ib[i]],3).tolist()) for i in np.where(sel)[0][:10]])
