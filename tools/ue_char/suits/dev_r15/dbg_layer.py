import sys, json, numpy as np, cv2
sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/ue_char/suits')
import net_end_check_r15 as N, meshio, design
from scipy import ndimage as ndi
suit,layer=sys.argv[1],sys.argv[2]; n=2048
cfg=json.load(open('/Users/midir/sm2-n1/characters/tools/ue_char/suits/suits.json'))
e=[x for x in cfg['suits'] if x['id']==suit][0]
m=meshio.load_body(); tri,w0,w1,inside=meshio.raster_tri(m['UV'],m['F'],n); cov=tri>=0
P,Nn_,UV,F,GW=m['P'],m['N'],m['UV'],m['F'],m['GW']
a3=np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)/2
a2=np.abs((UV[F[:,1],0]-UV[F[:,0],0])*(UV[F[:,2],1]-UV[F[:,0],1])-(UV[F[:,2],0]-UV[F[:,0],0])*(UV[F[:,1],1]-UV[F[:,0],1]))/2*n*n
mpt_tri=np.clip(np.sqrt(a3/np.maximum(a2,1e-9)).astype(np.float32),2e-5,2e-3)
gi={g:i for i,g in enumerate(meshio.GROUPS)}; jp={k:tuple(float(x) for x in v) for k,v in m['jpos'].items()}
cords=np.zeros((n,n),bool); ends=np.zeros((n,n),bool); col=np.zeros((n,n,3),np.float32); crease=np.zeros((n,n),bool); zon=np.zeros((n,n),np.float32)
for r0 in range(0,n,256):
    sl=slice(r0,r0+256)
    if not cov[sl].any(): continue
    Pp=meshio.gather(tri,w0,w1,F,P,sl); Nn=meshio.gather(tri,w0,w1,F,Nn_,sl); Nn/=np.linalg.norm(Nn,axis=-1,keepdims=True)+1e-9
    G=meshio.gather(tri,w0,w1,F,GW,sl); mp=mpt_tri[np.where(tri[sl]>=0,tri[sl],0)]
    dbg={}; o=design.paint(Pp,Nn,G,mp,gi,jp,e.get('style'),dbg=dbg)
    col[sl]=o['col']; cords[sl]=dbg['cord']>0.3
    ax_,y_=np.abs(Pp[...,0]),Pp[...,1]; crease[sl]=(y_>1.14)&(y_<1.40)&(ax_>0.10)&(ax_<0.30)
    for line,zone,nm in dbg['net']:
        if nm==layer: ends[sl]|=(line>0.4)&(zone>0.02)&(zone<0.98); zon[sl]=np.maximum(zon[sl],zone)
near=ndi.binary_dilation(cords,iterations=3)
dead=ends&~near&ndi.binary_erosion(cov,iterations=8)&~ndi.binary_dilation(crease,iterations=6)
lab,k=ndi.label(ndi.binary_dilation(dead,iterations=2))
cs=ndi.center_of_mass(dead,lab,range(1,k+1)); print(k,[(int(c[1]),int(c[0])) for c in cs])
img=(np.clip(col,0,1)*255).astype(np.uint8)[...,::-1].copy()
img[ndi.binary_dilation(dead,iterations=1)]=(0,0,255)
img[cords&~dead]=(img[cords&~dead]*0.5+np.array([0,255,0])*0.5).astype(np.uint8)
cv2.imwrite(f'/Users/midir/sm2-n1/_scratch/characters/r15/view/dbg_{suit}_{layer}.png',img)
np.save(f'/Users/midir/sm2-n1/_scratch/characters/r15/view/dbg_{suit}_{layer}_zone.npy',zon)
