"""Round 17 CPU aid: the face / throat centre seam in 3D.  Midline vertices (rest |x| < 2 mm, front) skinned in the idle clip; s = lateral distance from the HEAD's midsagittal plane (the plane the
head-lock camera sits in: normal = rest right axis turned with the head bone, through the head bone).  Prints the straightness of the seam over the face (y 1.56 - 1.72) and the step across the chin / throat
(y 1.45 - 1.56), in mm, over idle times; 1 mm = ~8.3 px at the 4K headfront framing (1.0 m, FOV 26).
   python3 seam3d.py SK_Hero.glb [GLB2 ...]"""
import sys, os, numpy as np
WT='/Users/midir/sm2-n1/characters'
sys.path[:0]=[WT+'/tools/ue_char/suit8', WT+'/tools/ue_char', WT+'/tools/ue_char/suits', WT+'/tools/skinfit', WT+'/tools/ue_char/heroanim']
import meshio, glbedit, skinfit, ganim, hero_weights_r12 as hw, hero_shoulder_r14 as HS
def run(glb, times=(0.0,0.4,0.8,1.2,1.6,2.0,2.4,2.8,3.2)):
    g=glbedit.Glb(glb); _,P,N,UV,J,W,F=HS.read_body(g); P=P.astype(np.float64)
    names=meshio.load_body()['names']; dense=hw.dense_of(J,W,len(names))
    doc=ganim.Doc(glb); j,b=skinfit.read_glb(glb); sk=j['skins'][0]; ibm=skinfit.accessor(j,b,sk['inverseBindMatrices']).reshape(-1,4,4)
    hj=sk['joints'].index(next(n for n in sk['joints'] if j['nodes'][n].get('name')=='head')) if False else [k for k,n in enumerate(sk['joints']) if j['nodes'][n].get('name')=='head'][0]
    hname=j['nodes'][sk['joints'][hj]]['name']
    Ph=np.concatenate([P,np.ones((len(P),1))],1)
    mid=np.where((np.abs(P[:,0])<0.002)&(P[:,2]>0.03)&(P[:,1]>1.45)&(P[:,1]<1.74))[0]; mid=mid[np.argsort(P[mid,1])]
    rest_head=np.linalg.inv(ibm[hj].T) if False else None
    out=[]
    for t in times:
        Wd=doc.world(doc.sample(doc.tracks('idle'),t))
        M=np.stack([Wd[n]@ibm[k].T for k,n in enumerate(sk['joints'])])
        X=np.einsum('vj,jab,vb->va',dense[mid],M,Ph[mid])[:,:3]
        R=M[hj][:3,:3]                    # rest -> posed rotation of the head bone (skinning matrix = posed * inverse bind)
        n=R@np.array([1.0,0,0]); n/=np.linalg.norm(n)
        p0=(M[hj]@np.array([0,P[mid][:,1].mean(),0,1.0]))[:3] if False else (M[hj]@np.concatenate([np.array([0,1.60,0.0]),[1.0]]))[:3]
        s=(X-p0)@n*1000.0 - (P[mid,0]-0.0)*1000.0     # mm, the rest-pose x offset of each vertex removed (the selection is +-2 mm wide)
        yy=P[mid,1]; face=(yy>1.56)&(yy<1.72); chin=(yy>1.44)&(yy<1.56)
        co=np.polyfit(yy[face],s[face],1); res=s[face]-np.polyval(co,yy[face])
        slope=co[0]                       # mm per m  -> px per 100 px = slope*0.1/1000*... (mm/m == 0.001 mm/mm)
        # chin step: s just below the chin line vs just above
        up=s[(yy>1.57)&(yy<1.60)].mean(); lo=s[(yy>1.50)&(yy<1.53)].mean() if ((yy>1.50)&(yy<1.53)).any() else np.nan
        ds=np.abs(np.diff(s))/np.maximum(np.diff(yy)*1000.0,0.2)     # lateral jump per mm of height between consecutive midline vertices
        out.append((t,slope,np.abs(res).max(),up-lo, s[face].max()-s[face].min(), ds.max(), yy[np.argmax(ds)]))
    return out
if __name__=='__main__':
    for glb in sys.argv[1:]:
        print(glb)
        o=run(glb)
        print('  t      slope(px/100px)  face resid max mm   chin step mm (above-below)   face range mm   max step slope (mm/mm) at y')
        for t,sl,rm,cs,rg,dm,dy in o: print('  %.1f   %8.2f   %10.2f   %14.2f   %10.2f   %8.3f at %.3f'%(t,sl/10.0,rm,cs,rg,dm,dy))
