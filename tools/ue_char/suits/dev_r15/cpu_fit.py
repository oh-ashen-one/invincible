import sys, numpy as np
sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/ue_char/suits'); sys.path.insert(0,'/Users/midir/sm2-n1/_scratch/characters/r15')
import head_check_r13 as H13, cpu_rim2 as C2
from scipy import ndimage as ndi
from scipy.optimize import minimize
glb=sys.argv[1]; still=sys.argv[2]
im=H13.load(still); sil=H13.silhouette(im)
rows=np.arange(650,1500)
def front_real(sil):
    out=[]
    for r in rows:
        c=np.nonzero(sil[r])[0]; out.append(c.max() if len(c) else np.nan)
    return np.array(out,float)
FR=front_real(sil)
def front_cpu(theta,yaw):
    C2.HP.load=C2.make_load(theta)
    img=C2.HP.persp_render(glb,yaw,dist=1.25,aim=1.665,fov_h=26.0)
    s=img>0
    out=[]
    for r in rows:
        c=np.nonzero(s[r])[0]; out.append(c.max() if len(c) else np.nan)
    return np.array(out,float)
best=None
for theta in np.arange(-12,0.1,1.5):
    for yaw in (-96,-92,-88,-84,-80):
        F=front_cpu(theta,yaw)
        for dy in range(-60,61,6):
            Fs=np.roll(F,dy)  # shift rows
            ok=~np.isnan(Fs)&~np.isnan(FR)&(rows>800)&(rows<1400)
            if ok.sum()<200: continue
            dx=np.nanmedian(FR[ok]-Fs[ok])
            e=np.sqrt(np.mean((FR[ok]-Fs[ok]-dx)**2))
            if best is None or e<best[0]: best=(e,theta,yaw,dy,dx)
print('best (rms px, pitch, yaw, row shift, col shift):',best)
