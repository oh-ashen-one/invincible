# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). Director spec instrument, 2026-09-29. Run with a venv holding ultralytics+opencv (see specs README lines).
# near-field coverage: share of frame whose optical-flow magnitude (between consecutive 60 fps frames, 480x270)
# exceeds T px/frame after removing the median (camera-rotation proxy) -> fast-moving near geometry (facades, trees)
import cv2, numpy as np, sys, glob
T = float(sys.argv[1]); clips = sys.argv[2:]
for p in clips:
    cap=cv2.VideoCapture(p); i=0; prev=None; cov=[]; left=[]; right=[]
    while True:
        ok,im=cap.read()
        if not ok: break
        g0=cv2.cvtColor(cv2.resize(im,(480,270),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2GRAY)
        g=g0
        if prev is not None and i%6==2:
            f=cv2.calcOpticalFlowFarneback(prev,g,None,0.5,3,15,3,5,1.2,0)
            f=f-np.median(f.reshape(-1,2),axis=0)
            mag=np.hypot(f[...,0],f[...,1]); m=mag>T
            cov.append(m.mean()); left.append(m[:,:160].mean()); right.append(m[:,320:].mean())
        if i%6==0: prev=g
        i+=1
    cov=np.array(cov); side=np.maximum(left,right)
    print(f"{p.split('/')[-1][:34]:34s} cov p50 {np.median(cov):.2f} p90 {np.percentile(cov,90):.2f} | max-side-third p50 {np.median(side):.2f} p90 {np.percentile(side,90):.2f} | frames with a side third >50% covered: {100*(side>0.5).mean():.0f}%")
