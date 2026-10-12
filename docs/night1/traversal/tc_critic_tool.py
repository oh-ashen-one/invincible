# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 18: copy of the r17 blind critic's TC reader (_scratch/critic-P3-r17-work/tc.py), only the round dir is an argument:
#   python tc_critic_tool.py <round dir> <clip> ...   (window = program + 0.5 s; TC-C on the bone box)
import csv,math,sys,numpy as np
R=sys.argv.pop(1).rstrip('/')+'/'
def wrap(a): return (a+180)%360-180
def pct(a,p): return float(np.percentile(a,p)) if len(a) else float('nan')
pooled={k:[] for k in 'off hh cx cy pitch dz'.split()}
for n in sys.argv[1:]:
    T=list(csv.DictReader(open(R+n+'_telemetry.csv')))
    f=lambda r,k: float(r[k]) if r[k] not in ('','None') else float('nan')
    t=np.array([f(r,'t') for r in T]); ft=np.array([f(r,'flip_t') for r in T])
    # slew whole clip
    yaw=np.array([f(r,'pcm_yaw') for r in T]); pit=np.array([f(r,'pcm_pitch') for r in T])
    pos=np.array([[f(r,'pcm_x'),f(r,'pcm_y'),f(r,'pcm_z')] for r in T])
    dy=np.abs(wrap(np.diff(yaw))); dp=np.abs(np.diff(pit)); dpos=np.linalg.norm(np.diff(pos,axis=0),axis=1)
    print(f'== {n}: TC-K per-frame max yaw {dy.max():.2f}@{t[1:][dy.argmax()]:.2f} pitch {dp.max():.2f}@{t[1:][dp.argmax()]:.2f} pos {dpos.max():.2f}m@{t[1:][dpos.argmax()]:.2f}  frames yaw>4:{(dy>4).sum()} pitch>3:{(dp>3).sum()} pos>1.2:{(dpos>1.2).sum()}')
    # tricks
    on=ft>=0; i=0; N=len(T)
    while i<N:
        if not on[i]: i+=1; continue
        s=i
        while i<N and on[i]: i+=1
        e=i  # exclusive
        tend=t[e-1]+0.5
        w=[k for k in range(s,N) if t[k]<=tend]
        r0=T[s]; hd=math.degrees(math.atan2(f(r0,'vy'),f(r0,'vx')))
        # heading: pcm_yaw is camera forward; travel-behind => camera looks along travel. offset = |yaw - heading|
        off=np.abs(wrap(yaw[w]-hd)); rng=yaw[w].max()-yaw[w].min() if True else 0
        yw=np.unwrap(np.radians(yaw[w])); rng=math.degrees(yw.max()-yw.min())
        k=np.array([f(T[j],'flipcam_k') for j in w]); rate=np.abs(np.degrees(np.diff(yw)))/np.diff(t[w])
        held=k[1:]>=0.9
        hh=np.array([f(T[j],'hero_bbox_h') for j in w]); cx=np.array([f(T[j],'hero_cx') for j in w]); cy=np.array([f(T[j],'hero_cy') for j in w])
        pp=pit[w]; dz=np.array([f(T[j],'z_m')-f(T[j],'pcm_z') for j in w]); vs=np.array([f(T[j],'view_sun_deg') for j in w])
        inf=np.array([f(T[j],'hero_in_frame') for j in w]); geo=np.array([f(T[j],'cam_in_geometry') for j in w]); occ=np.array([f(T[j],'hero_occl') for j in w])
        dist=np.array([f(T[j],'cam_hero_dist_m') for j in w]); roll=np.array([f(T[j],'pcm_roll') for j in w]); fov=np.array([f(T[j],'pcm_fov') for j in w])
        # settle pitch attach+0.5..1.0
        att=t[e-1]; st=[j for j in range(N) if att+0.5<=t[j]<=att+1.0]
        sp=np.median(pit[st]) if st else float('nan')
        print(f' trick {T[s]["trick"]} t{t[s]:.2f}-{t[e-1]:.2f} hd{hd:.0f} | A off p5 {pct(off,5):.0f} p95 {pct(off,95):.0f} range {rng:.0f} | B held p95 {pct(rate[held],95) if held.any() else -1:.0f} max {rate[held].max() if held.any() else -1:.0f} all max {rate.max():.0f} | C h p10 {pct(hh,10):.3f} p50 {pct(hh,50):.3f} p90 {pct(hh,90):.3f} | D cx {pct(cx,5):.2f}-{pct(cx,95):.2f} cy {pct(cy,5):.2f}-{pct(cy,95):.2f} | E pitch(+up) p5 {pct(pp,5):.1f} p95 {pct(pp,95):.1f} settle {sp:.1f} | F dz p10 {pct(dz,10):.2f} p50 {pct(dz,50):.2f} | G inframe {inf.mean():.2f} geo {np.nansum(geo):.0f} occ {np.nansum(occ):.0f} | H sun min {np.nanmin(vs):.0f} | dist p50 {pct(dist,50):.2f} min {dist.min():.2f} roll max {np.nanmax(np.abs(roll)):.1f} fov {pct(fov,50):.0f}')
        for kk,v in zip('off hh cx cy pitch dz'.split(),[off,hh,cx,cy,pp,dz]): pooled[kk]+=list(v)
print('POOLED', {k:(round(pct(v,5),3),round(pct(v,50),3),round(pct(v,95),3)) for k,v in pooled.items()})
