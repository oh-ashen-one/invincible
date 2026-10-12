import sys, numpy as np
sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/ue_char/suit8'); sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/skinfit')
import glbedit, skinfit, hero_head_r14 as H
g=glbedit.Glb(sys.argv[1]); j=g.j; raw=bytes(g.bin)
p=H.body_prim(j); A=p['attributes']
P=skinfit.accessor(j,raw,A['POSITION']).astype(np.float32); N=skinfit.accessor(j,raw,A['NORMAL']).astype(np.float32)
UV=skinfit.accessor(j,raw,A['TEXCOORD_0']).astype(np.float32); J=skinfit.accessor(j,raw,A['JOINTS_0']).astype(np.int64); W=skinfit.accessor(j,raw,A['WEIGHTS_0']).astype(np.float32)
F=skinfit.accessor(j,raw,p['indices']).reshape(-1,3).astype(int)
print('prepped verts',len(P),'tris',len(F))
P2,N2,UV2,J2,W2,F2,hd=H.sculpt(P,N,UV,J,W,F)
# undisplaced refined positions: re-run refine only
Pr=P.copy();Fr=F.copy();NN=N;UVv=UV;JJ=J;WW=W
for lev in range(H.LEVELS):
    sh=0.0 if lev==0 else 0.004
    c=Pr[Fr].mean(1)
    sel=(np.abs(c[:,0])<H.ZONE['xmax']-sh)&(c[:,1]>H.ZONE['y0']+sh)&(c[:,1]<H.ZONE['y1']-sh)&(c[:,2]>H.ZONE['zmin']+sh*0.5)
    Pr,NN,UVv,JJ,WW,Fr=H.refine(Pr,NN,UVv,JJ,WW,Fr,sel)
def area(P,F): return 0.5*np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)
a0=area(Pr,Fr); a1=area(P2,F2)
s=np.sqrt(a1/np.maximum(a0,1e-12))
c=Pr[Fr].mean(1)
face=(np.abs(c[:,0])<0.095)&(c[:,1]>1.545)&(c[:,1]<1.745)&(c[:,2]>0.02)
print('face tris',face.sum(),'stretch sqrt(area ratio): median %.2f p90 %.2f p99 %.2f max %.2f'%tuple(np.percentile(s[face],[50,90,99,100]).tolist()[:1]+np.percentile(s[face],[90,99,100]).tolist()))
# stretch by y band under the brow
for y0,y1 in [(1.72,1.745),(1.70,1.72),(1.69,1.70),(1.68,1.69),(1.66,1.68),(1.64,1.66),(1.62,1.64),(1.60,1.62),(1.58,1.60),(1.55,1.58)]:
    m=face&(c[:,1]>=y0)&(c[:,1]<y1)
    print('y %.2f-%.2f: n %d  stretch median %.2f p90 %.2f max %.2f'%(y0,y1,m.sum(),np.median(s[m]),np.percentile(s[m],90),s[m].max()))
np.savez(sys.argv[2],Pr=Pr,P2=P2,Fr=Fr,s=s,UV=UVv)
