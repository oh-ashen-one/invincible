# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 06: open boundary loops of a refit citizen (welded vertices): size, centre, dominant bone.  Use it to find the shoe collar / trouser cuff /
sleeve rings that could get a bridge strip.   python3 tools/ue_char/eval/boundary_loops.py NAME     (needs $P2_SCRATCH)"""
import sys, os
_R=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..'))
sys.path.insert(0,_R+'/tools/ue_char/eval'); sys.path.insert(0,_R+'/tools/ue_char')
import numpy as np
from scipy.spatial import cKDTree
import weights_r6 as W
from p2paths import scr
name=sys.argv[1]
z=np.load(scr('eval','refit',name+'_final.npz'))
pos,idx,dense,welded=z['pos'],z['idx'],z['dense'],z['welded']
nu=welded.max()+1; first=np.zeros(nu,int); first[welded[::-1]]=np.arange(len(welded))[::-1]
Pu=pos[first]; Fu=welded[idx]
# boundary edges
e=np.concatenate([Fu[:,[0,1]],Fu[:,[1,2]],Fu[:,[2,0]]]); es=np.sort(e,axis=1)
u,inv,cnt=np.unique(es,axis=0,return_inverse=True,return_counts=True)
bnd=u[cnt==1]
print(name,'welded verts',nu,'boundary edges',len(bnd),'nonmanifold edges',(cnt>2).sum())
# components of boundary graph
adj={}
for a,b in bnd: adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
seen=set(); loops=[]
for v in adj:
    if v in seen: continue
    st=[v]; comp=[]; seen.add(v)
    while st:
        a=st.pop(); comp.append(a)
        for b in adj[a]:
            if b not in seen: seen.add(b); st.append(b)
    loops.append(np.array(comp))
names=['hips','spine','chest','neck','head','uarmL','farmL','handL','uarmR','farmR','handR','thighL','shinL','footL','thighR','shinR','footR','prop']
for L in sorted(loops,key=lambda l:-len(l)):
    c=Pu[L].mean(0); d=dense[first[L]].mean(0)
    per=sum(np.linalg.norm(Pu[a]-Pu[b]) for a,b in bnd if a in set(L)) if len(L)<400 else -1
    print('loop verts %3d centre (%.2f,%.2f,%.2f) extent %.2f bone %s'%(len(L),c[0],c[1],c[2],np.linalg.norm(Pu[L].max(0)-Pu[L].min(0)),names[d.argmax()]))
