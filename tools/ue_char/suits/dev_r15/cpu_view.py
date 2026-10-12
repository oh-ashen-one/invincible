import sys, os, numpy as np, cv2
sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/ue_char/suit8'); sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/ue_char'); sys.path.insert(0,'/Users/midir/sm2-n1/characters/tools/ue_char/suits')
import meshio, softrender as sr, swatch_cpu as sw
def render(maps, sid, eye, tgt, fov, w=1200, h=900, out=None):
    m=meshio.load_body()
    bc=sw.load_tex('%s/%s_basecolor.png'%(maps,sid)); nm=sw.load_tex('%s/%s_normal.png'%(maps,sid),gamma=False)
    body=sr.Prim(m['P'],m['N'],m['F'],UV=m['UV'],tex=bc,nmap=nm,rough=0.7,spec=0.12,name='suit')
    img=sr.render([body],sr.look_at(eye,tgt),fov,w,h,ssaa=2)
    img=np.clip(img,0,1) if img.dtype!=np.uint8 else img
    if img.dtype!=np.uint8: img=(img*255).astype(np.uint8)
    cv2.imwrite(out,img[...,::-1] if img.shape[2]==3 else img)
if __name__=='__main__':
    maps,sid,view,out=sys.argv[1:5]
    V={'armpitR':((-0.62,1.22,1.0),(-0.20,1.25,0.0),18),'chest':((0,1.30,1.6),(0,1.30,0),24),'front':((0,0.92,4.2),(0,0.92,0),26),'back':((0,0.92,-4.2),(0,0.92,0),26)}
    e,t,f=V[view]; render(maps,sid,e,t,f,out=out)
