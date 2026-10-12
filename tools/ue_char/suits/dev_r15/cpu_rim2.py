import sys, numpy as np
sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/ue_char/suits')
import head_profile_r14 as HP
_orig_load = HP.load
PIV = np.array([0.0, 1.60, -0.02])
def make_load(theta_deg):
    th = np.radians(theta_deg); c, s = np.cos(th), np.sin(th)
    def ld(path):
        S = _orig_load(path); out = {}
        for k, (P, F) in S.items():
            Q = P.copy(); d = Q - PIV
            y = d[:,1]*c - d[:,2]*s; z = d[:,1]*s + d[:,2]*c
            Q[:,1] = PIV[1]+y; Q[:,2] = PIV[2]+z
            out[k] = (Q, F)
        return out
    return ld
def measure(glb, yaw=-90.0, pitch=0.0, dist=1.25, aim=1.665, fov=26.0, ty=0.0):
    HP.load = make_load(pitch)
    im = HP.persp_render(glb, yaw, dist=dist, aim=aim, fov_h=fov)
    sil = im>0
    f = 1920.0/np.tan(np.radians(fov/2))/dist
    row_of=lambda y:int(round(1080-(y-aim)*f))
    sgn=1
    # brow: front-most silhouette column in the band above the glass top: use rows between glass top - 140 px and glass top
    gy,gx=np.nonzero(im==3); gtop=gy.min()
    band_rows=np.arange(gtop-170, gtop-5)
    fxs=np.array([np.nonzero(sil[r])[0].max() for r in band_rows])
    ib=int(np.argmax(fxs)); xb=int(fxs[ib]); rb=int(band_rows[ib])
    ry,rx=np.nonzero(im==2); k=int(np.argmax(rx)); xr=int(rx.max()); rr=int(ry[k])
    xg=int(gx.max())
    return dict(brow_x=xb,brow_row=rb,rim_x=xr,rim_row=rr,glass_x=xg, glass_minus_brow=xg-xb, rim_minus_brow=xr-xb, rim_row_minus_brow_row=rr-rb)
if __name__=='__main__':
    g=sys.argv[1]
    best=[]
    for pitch in np.arange(-12,13,3.0):
        for yaw in (-100,-95,-90,-85,-80):
            r=measure(g,yaw,pitch)
            err=abs(r['glass_minus_brow']+18)+abs(r['rim_minus_brow']-14)+abs(r['rim_row_minus_brow_row']-281)*0.3
            best.append((err,pitch,yaw,r))
    best.sort(key=lambda t:t[0])
    for b in best[:6]: print(b)
