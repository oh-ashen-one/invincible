# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). Director spec instrument, 2026-09-29. Run with a venv holding ultralytics+opencv (see specs README lines).
import cv2, numpy as np, sys, json
R='/Users/midir/spiderman-learnings/refs/'
def stats(f, regs):
    im=cv2.resize(cv2.imread(R+f),(1920,1080),interpolation=cv2.INTER_AREA).astype(np.float32)
    print('==',f)
    sky=None
    for name,(x0,y0,x1,y1) in regs.items():
        c=im[y0:y1,x0:x1]; b,g,r=c[...,0],c[...,1],c[...,2]; Y=0.2126*r+0.7152*g+0.0722*b
        hsv=cv2.cvtColor(c.astype(np.uint8),cv2.COLOR_BGR2HSV)
        lap=np.abs(cv2.Laplacian(Y,cv2.CV_32F)).mean()
        s=dict(R=r.mean(),G=g.mean(),B=b.mean(),Y=Y.mean(),Ystd=Y.std(),rms=Y.std()/max(Y.mean(),1),sat=hsv[...,1].mean()/255,lap=lap,p95=np.percentile(Y,95),hi80=(Y>0.8*255).mean()*100)
        if name=='sky': sky=s
        extra = f" dY_sky {s['Y']-sky['Y']:+6.1f}" if sky and name!='sky' else ''
        print(f"  {name:14s} RGB ({s['R']:5.1f},{s['G']:5.1f},{s['B']:5.1f}) B-R {s['B']-s['R']:+6.1f}  Y {s['Y']:5.1f}  Ystd {s['Ystd']:5.1f}  rms {s['rms']:.3f}  sat {s['sat']:.2f}  lap {s['lap']:5.2f}{extra}")
stats('streets/skyline-perch-nm__nm_0846.jpg', {'sky':(0,0,1920,100),'horizon_far':(0,150,1920,215),'far_shore':(1150,225,1900,300),'river':(1250,340,1650,430),'mid_city':(0,330,700,540),'near_city':(0,650,800,900)})
stats('streets/skyline-perch-dn__dn_1438.jpg', {'sky':(0,0,1920,300),'far_city':(0,350,700,540),'far_shore':(1150,450,1900,560),'river':(0,590,500,700),'near_city':(0,780,600,1000)})
stats('streets/skyline-queens-aerial__gr_0033.jpg', {'sky':(0,0,1920,200),'far_manhattan':(200,330,900,430),'river':(1540,520,1900,590),'mid_city':(0,520,700,640),'near_city':(0,700,700,900)})
