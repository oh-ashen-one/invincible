import cv2, numpy as np, sys
path=sys.argv[1]
cap=cv2.VideoCapture(path); fps=cap.get(5)
rows=[]
i=0
while True:
    ok,f=cap.read()
    if not ok: break
    hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV)
    h,s,v=hsv[...,0].astype(int),hsv[...,1].astype(int),hsv[...,2].astype(int)
    red=((h<=6)|(h>=172))&(s>150)&(v>90)
    blue=(h>=105)&(h<=128)&(s>130)&(v>50)
    m=(red|blue).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    if n<2: rows.append((i,np.nan,np.nan,np.nan,np.nan,0)); i+=1; continue
    k=1+np.argmax(st[1:,4])
    x,y,w,hh,a=st[k]
    rows.append((i,x,y,w,hh,a)); i+=1
r=np.array(rows,float)
H=1080.0
print("frames",len(r),"fps",fps,"H",H)
hh=r[:,4]; top=r[:,2]; bot=r[:,2]+r[:,4]
print("height/H median %.3f  p10 %.3f p90 %.3f"%(np.nanmedian(hh/H),np.nanpercentile(hh/H,10),np.nanpercentile(hh/H,90)))
def dom(sig,lo=1.0,hi=6.0):
    s=sig-np.nanmean(sig); s=np.nan_to_num(s)
    s=s-np.convolve(s,np.ones(31)/31,'same')
    F=np.abs(np.fft.rfft(s*np.hanning(len(s)),n=8192)); fr=np.fft.rfftfreq(8192,1/fps)
    msk=(fr>lo)&(fr<hi); j=np.argmax(F*msk); return fr[j]
print("dom freq height %.2f Hz, top %.2f Hz"%(dom(hh),dom(top)))
np.save(sys.argv[2],r)
