import sys, os, json
import numpy as np
from scipy import ndimage as ndi
WT='/Users/midir/sm2-n1/characters'
sys.path.insert(0, WT+'/tools/ue_char/suits'); sys.path.insert(0, WT+'/tools/ue_char'); sys.path.insert(0, WT+'/tools/ue_char/suit8')
import net_end_check_r15 as NE, meshio, design
n=int(sys.argv[1]); only=sys.argv[2].split(',')
cfg=json.load(open(NE.SUITS_JSON)); m=meshio.load_body(); pre=(m, meshio.raster_tri(m['UV'], m['F'], n))
tri,w0,w1,inside=pre[1]
P_,F_=m['P'],m['F']
Pm=np.zeros((n,n,3),np.float32)
for r0 in range(0,n,256):
    sl=slice(r0,min(r0+256,n)); Pm[sl]=meshio.gather(tri,w0,w1,F_,P_,sl)
# monkeypatch: capture dead mask via png path? reimplement quickly by calling evaluate with a hook
orig_label=ndi.label
for e in cfg['suits']:
    if e['id'] not in only: continue
    cap={}
    def lab_hook(mask, *a, **k):
        cap.setdefault('masks',[]).append(mask.copy()); return orig_label(mask,*a,**k)
    NE.ndi.label=lab_hook
    r=NE.evaluate(e,n,pre)
    NE.ndi.label=orig_label
    # first label call = count(dead & ~cr_zone) dilated mask
    mk=cap['masks'][0]
    lab,k=orig_label(mk)
    print(e['id'], r['open_fabric_by_layer'])
    for i in range(1,k+1):
        ys,xs=np.where(lab==i)
        p=Pm[ys,xs].mean(0)
        print('  blob %d texels %d  P=(%.3f %.3f %.3f) uv=(%d,%d)'%(i,len(ys),p[0],p[1],p[2],xs.mean(),ys.mean()))
