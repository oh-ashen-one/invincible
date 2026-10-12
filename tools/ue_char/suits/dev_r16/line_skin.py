import sys, os, json
import numpy as np
WT='/Users/midir/sm2-n1/characters'; S8=WT+'/tools/ue_char/suit8'
sys.path[:0]=[S8, WT+'/tools/ue_char', WT+'/tools/skinfit', WT+'/tools/ue_char/heroanim']
import skinfit, meshio, ganim, glbedit
import hero_weights_r12 as hw, hero_shoulder_r14 as HS
def load(glb):
    g=glbedit.Glb(glb); _,P,N,UV,J,W,F=HS.read_body(g)
    names=meshio.load_body()['names']
    return P.astype(np.float64), F, hw.dense_of(J,W,len(names))
def plane_pts(P,F,yc,front=True):
    """points where triangle edges cross y = yc, with barycentric weights (i, j, t)"""
    out=[]
    E=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); E=np.unique(np.sort(E,1),axis=0)
    a,b=P[E[:,0]],P[E[:,1]]
    s=(a[:,1]-yc)*(b[:,1]-yc)<0
    E=E[s]; a,b=a[s],b[s]
    t=(yc-a[:,1])/(b[:,1]-a[:,1])
    X=a+(b-a)*t[:,None]
    keep=(X[:,2]>0) if front else (X[:,2]<0)
    return E[keep], t[keep], X[keep]
def skin(Pv,dense,clip,tt):
    doc=ganim.Doc(meshio.GLB); j,b=skinfit.read_glb(meshio.GLB)
    sk=j['skins'][0]; ibm=skinfit.accessor(j,b,sk['inverseBindMatrices']).reshape(-1,4,4)
    Wd=doc.world(doc.sample(doc.tracks(clip),tt))
    M=np.stack([Wd[n]@ibm[k].T for k,n in enumerate(sk['joints'])])
    Ph=np.concatenate([Pv,np.ones((len(Pv),1))],1)
    return np.einsum('vj,jab,vb->va',dense,M,Ph)[:,:3]
if __name__=='__main__':
    glb=sys.argv[1]; yc=float(sys.argv[2])
    P,F,dense=load(glb)
    E,t,X=plane_pts(P,F,yc)
    for clip,tt in (('idle',0.0),('idle',1.2)):
        Xs=skin(P,dense,clip,tt)
        Y=Xs[E[:,0]]+(Xs[E[:,1]]-Xs[E[:,0]])*t[:,None]
        o=np.argsort(X[:,0]); x0=X[o,0]; Yp=Y[o]
        # posed vertical vs posed horizontal: local slope changes
        sel=(np.abs(x0)<0.23)
        x0,Yp=x0[sel],Yp[sel]
        dy=np.diff(Yp[:,1]); dx=np.diff(Yp[:,0])
        sl=dy/np.maximum(np.abs(dx),1e-5)
        # kink: change of posed y vs a 2 cm running fit
        from numpy.polynomial import polynomial as Pn
        dev=[]
        for i in range(len(x0)):
            m=np.abs(x0-x0[i])<0.02
            if m.sum()<5: dev.append(0);continue
            c=np.polyfit(Yp[m,0],Yp[m,1],2); dev.append(Yp[i,1]-np.polyval(c,Yp[i,0]))
        dev=np.array(dev)
        k=np.argsort(-np.abs(dev))[:6]
        print(clip,tt,'n',len(x0),'max dev mm %.2f'%(np.abs(dev).max()*1000), [(round(x0[i],3),round(dev[i]*1000,2)) for i in k])
