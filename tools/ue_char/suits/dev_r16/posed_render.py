"""CPU render of the prepped hero GLB, skinned in a ganim pose, textured with a suit's base colour, from a stage-like camera (design aid, not evidence)."""
import sys, os, numpy as np, cv2
WT='/Users/midir/sm2-n1/characters'
sys.path[:0]=[WT+'/tools/ue_char/suit8', WT+'/tools/ue_char', WT+'/tools/ue_char/suits', WT+'/tools/skinfit', WT+'/tools/ue_char/heroanim']
import meshio, softrender as sr, swatch_cpu as SC, glbedit, skinfit, ganim
import hero_weights_r12 as hw, hero_shoulder_r14 as HS
def posed(glb, clip='idle', t=1.0):
    g=glbedit.Glb(glb); _,P,N,UV,J,W,F=HS.read_body(g)
    names=meshio.load_body()['names']; dense=hw.dense_of(J,W,len(names))
    doc=ganim.Doc(glb); j,b=skinfit.read_glb(glb)
    sk=j['skins'][0]; ibm=skinfit.accessor(j,b,sk['inverseBindMatrices']).reshape(-1,4,4)
    Wd=doc.world(doc.sample(doc.tracks(clip),t))
    M=np.stack([Wd[n]@ibm[k].T for k,n in enumerate(sk['joints'])])
    Ph=np.concatenate([P.astype(np.float64),np.ones((len(P),1))],1)
    X=np.einsum('vj,jab,vb->va',dense,M,Ph)[:,:3]
    if os.environ.get('REST'): return P.astype(np.float32), N.astype(np.float32), UV, F
    Nn=np.einsum('vj,jab,vb->va',dense,M[:,:3,:3],N.astype(np.float64)); Nn/=np.linalg.norm(Nn,axis=1,keepdims=True)
    return X.astype(np.float32), Nn.astype(np.float32), UV, F
if __name__=='__main__':
    glb, sid, out = sys.argv[1], sys.argv[2], sys.argv[3]
    az=float(sys.argv[4]) if len(sys.argv)>4 else 25.0
    t=float(sys.argv[5]) if len(sys.argv)>5 else 1.0
    maps=os.environ.get('MAPS', WT+'/art/night1/characters/hero/suits')
    X,Nn,UV,F=posed(glb,'idle',t)
    bc=SC.load_tex('%s/%s_basecolor.png'%(maps,sid))
    body=sr.Prim(X,Nn,F,UV=UV,tex=bc,nmap=None,rough=0.7,spec=0.12,name='suit')
    a=np.radians(az); tgt=np.array([0,1.35,0]); eye=tgt+np.array([np.sin(a),0.04,np.cos(a)])*float(os.environ.get('DIST','1.5'))
    W=int(os.environ.get('W','1600')); H=int(W*9/16)
    im=sr.render([body],sr.look_at(eye,tgt),float(os.environ.get("VFOV","17.1")),W,H,ssaa=1)
    cv2.imwrite(out,(np.clip(im,0,1)**(1/2.2)*255).astype(np.uint8)[...,::-1])
