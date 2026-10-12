# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 06: pose the fitted street thug (skinfit output, hero skeleton) in its own walk clip and measure edge growth (stretch / spikes) per triangle.
  python3 tools/ue_char/people/thug_probe.py     (reads $P2_SCRATCH/r3/fit/StreetThug.glb; writes $P2_SCRATCH/r6/thug_posed_frames.npy)
Result of round 06: whole mesh max 7.9 cm (19 triangles > 5 cm), collar zone (y 1.38-1.62, |x| < 0.2) max 0.9 cm: the hoodie collar is not stretched."""
import sys, os
_R=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..'))
sys.path.insert(0,_R+'/tools/skinfit'); sys.path.insert(0,_R+'/tools/ue_char/people'); sys.path.insert(0,_R+'/tools/ue_char/eval'); sys.path.insert(0,_R+'/tools/ue_char')
import numpy as np, cv2
import skinfit, make_walk
from skinfit import read_glb, accessor
from PIL import Image
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..'))
from p2paths import SCRATCH as SC   # noqa: E402
game=skinfit.Game(ROOT+'/public/assets/spiderman.glb')
an=next(a for a in game.j['animations'] if a['name']=='walk')
times,rot,tra,name2i,Pm=make_walk.build(game,an,'street')
n=len(times)
j,b=read_glb(SC+'/r3/fit/StreetThug.glb')
p=j['meshes'][0]['primitives'][0]; A=p['attributes']
R=accessor(j,b,A['POSITION']); F=accessor(j,b,p['indices']).reshape(-1,3).astype(int)
J=accessor(j,b,A['JOINTS_0']).astype(int); W=accessor(j,b,A['WEIGHTS_0']); UV=accessor(j,b,A['TEXCOORD_0'])
W=W/W.sum(1,keepdims=True)
skin=j['skins'][0]; ibm=accessor(j,b,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
joints=skin['joints']; gj=game.joints
print('joint order same as game:',joints==gj, len(joints))
par=game.parent
def mat(t,q): return make_walk.mat(t,q)
def posed(k):
    G={}
    for i in game.order:
        M=(G[par[i]] if par.get(i) in G else game.base[i])@mat(tra[i][k],rot[i][k]); G[i]=M
    S=np.stack([G[i] for i in joints])@ibm
    B=np.einsum('vk,vkij->vij',W,S[J])
    return np.einsum('vij,vj->vi',B[:,:3,:3],R)+B[:,:3,3]
os.makedirs(SC+'/r6',exist_ok=True); np.save(SC+'/r6/thug_posed_frames.npy',np.stack([posed(k) for k in range(0,n)]))
# stretch over clip
E=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]])
rest=np.linalg.norm(R[E[:,0]]-R[E[:,1]],axis=1)
worst=np.zeros(len(E))
frames=np.load(SC+'/r6/thug_posed_frames.npy')
for Q in frames:
    ln=np.linalg.norm(Q[E[:,0]]-Q[E[:,1]],axis=1); worst=np.maximum(worst,ln-rest)
tw=worst.reshape(3,-1).max(0)
print('thug walk frames',n,'tris >2cm',(tw>0.02).sum(),'>5cm',(tw>0.05).sum(),'>10cm',(tw>0.10).sum(),'max %.1f cm'%(tw.max()*100))
cen=R[F].mean(1)
col=(cen[:,1]>1.38)&(cen[:,1]<1.62)&(np.abs(cen[:,0])<0.2)
print('collar zone: >2cm',(col&(tw>0.02)).sum(),'>5cm',(col&(tw>0.05)).sum(),'max %.1f'%(tw[col].max()*100))
