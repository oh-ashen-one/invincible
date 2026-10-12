# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). Director spec instrument, 2026-09-29. Run with a venv holding ultralytics+opencv (see specs README lines).
# Camera roll / pitch / FOV / avenue-yaw from vanishing points (vertical VP + dominant forward VP), per sampled frame.
import sys, cv2, numpy as np, csv
clip, out, step = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else 6
rng = np.random.default_rng(0)
lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
def segs(g):
    L = lsd.detect(g)[0]
    if L is None: return np.zeros((0,4))
    L = L.reshape(-1,4); ln = np.hypot(L[:,2]-L[:,0], L[:,3]-L[:,1])
    return L[ln > 25]
def hom(L):
    p1 = np.c_[L[:,0],L[:,1],np.ones(len(L))]; p2 = np.c_[L[:,2],L[:,3],np.ones(len(L))]
    l = np.cross(p1,p2); return l/np.linalg.norm(l[:,:2],axis=1,keepdims=True)
def ransac_vp(L, it=600, tol_deg=1.5):
    if len(L) < 6: return None, 0
    l = hom(L); ln = np.hypot(L[:,2]-L[:,0], L[:,3]-L[:,1]); mid = np.c_[(L[:,0]+L[:,2])/2,(L[:,1]+L[:,3])/2]
    d = np.c_[L[:,2]-L[:,0], L[:,3]-L[:,1]]/ln[:,None]
    best, bs = None, -1
    for _ in range(it):
        i,j = rng.choice(len(L),2,replace=False); v = np.cross(l[i],l[j])
        if abs(v[2]) < 1e-9: vv = np.array([v[0],v[1]]); dirs = np.tile(vv/np.linalg.norm(vv),(len(L),1))
        else:
            p = v[:2]/v[2]; dirs = p[None,:]-mid; dirs /= np.linalg.norm(dirs,axis=1,keepdims=True)+1e-9
        ang = np.degrees(np.arccos(np.clip(np.abs((dirs*d).sum(1)),0,1)))
        inl = ang < tol_deg; s = ln[inl].sum()
        if s > bs: bs, best = s, inl
    A = l[best]*ln[best,None]; _,_,Vt = np.linalg.svd(A); v = Vt[-1]
    return v, best.sum()
cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS); i=0; rows=[]
while True:
    ok, fr = cap.read()
    if not ok: break
    if i % step == 0:
        g = cv2.cvtColor(cv2.resize(fr,(960,540)),cv2.COLOR_BGR2GRAY); H,W = g.shape; cx,cy = W/2,H/2
        L = segs(g); ang = np.degrees(np.arctan2(L[:,3]-L[:,1], L[:,2]-L[:,0]))%180
        vert = L[np.abs(ang-90) < 30]; oth = L[np.abs(ang-90) >= 30]
        vv, nv = ransac_vp(vert); vh, nh = ransac_vp(oth)
        r = dict(t=round(i/fps,3), n_vert=int(nv), n_fwd=int(nh))
        if vv is not None and nv >= 8:
            if abs(vv[2]) > 1e-9:
                p = vv[:2]/vv[2]; dx, dy = p[0]-cx, p[1]-cy
                if dy < 0: dx, dy = -dx, -dy          # VP above centre (camera pitched up): flip for roll
                r['roll_deg'] = round(np.degrees(np.arctan2(dx, dy)),2)*(-1)
                r['vvp_dist'] = round(float(np.hypot(p[0]-cx,p[1]-cy)),1); r['vvp_below'] = int((p[1]-cy) > 0)
            else:
                r['roll_deg'] = round(float(np.degrees(np.arctan2(vv[0], vv[1]))),2); r['vvp_dist']=1e9; r['vvp_below']=-1
        if vh is not None and nh >= 8 and abs(vh[2])>1e-9 and 'vvp_dist' in r and r['vvp_dist']<1e8:
            p = vh[:2]/vh[2]; rr = np.radians(-r['roll_deg'])
            # rotate into roll-corrected frame
            x, y = p[0]-cx, p[1]-cy; xr = x*np.cos(rr)-y*np.sin(rr); yr = x*np.sin(rr)+y*np.cos(rr)
            if r['vvp_below'] == 1 and yr < 0:            # horizon above centre, vertical VP below: pitched down
                f = np.sqrt(-yr * r['vvp_dist'])
                r.update(fwd_x=round(p[0]/W,3), fwd_y=round(p[1]/H,3), f_px=round(float(f),1), hfov_deg=round(float(np.degrees(2*np.arctan(W/2/f))),1),
                         pitch_down_deg=round(float(np.degrees(np.arctan(-yr/f))),1), yaw_off_deg=round(float(np.degrees(np.arctan(xr/np.hypot(f,yr)))),1))
            else:
                r.update(fwd_x=round(p[0]/W,3), fwd_y=round(p[1]/H,3))
        rows.append(r)
    i+=1
keys = ['t','n_vert','n_fwd','roll_deg','vvp_dist','vvp_below','fwd_x','fwd_y','f_px','hfov_deg','pitch_down_deg','yaw_off_deg']
with open(out+'_cam.csv','w') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
print(out, len(rows))
