# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). Director spec instrument, 2026-09-29. Run with a venv holding ultralytics+opencv (see specs README lines).
import json, numpy as np, sys
manual = {'swing-canyon-chase':[.21,.20,.12,.11], 'swing-avenue-midday':[.12,.11,.16,.11,.08,.15,.20,.14,.12,.09,.07,.10,.05,.08,.18,.10],
          'swing-avenue-traffic':[.13,.11,.11,.10,.09,.10,.11,.11,.20,.11,.14,.12,.09,.20,.20]}
json.dump(manual, open('m/manual_h_a.json','w'))
P=json.load(open('m/picks_a.json')); allh=[]
for clip, pts in P.items():
    D = json.load(open(f'm/d_{clip}_dets.json')); H=[]
    for t,x,y in pts:
        fr = min(D, key=lambda d: abs(d['t']-t))
        cand = [d for d in fr['dets'] if (d.get('mbox') or d['box'])[0]-0.01 <= x <= (d.get('mbox') or d['box'])[2]+0.01 and (d.get('mbox') or d['box'])[1]-0.02 <= y <= (d.get('mbox') or d['box'])[3]+0.02 and (d['box'][3]-d['box'][1])<0.6]
        if cand:
            d=max(cand,key=lambda d:(d['box'][2]-d['box'][0])*(d['box'][3]-d['box'][1])); mb=d.get('mbox') or d['box']; H.append(mb[3]-mb[1])
    H += manual[clip]; H=np.array(H); allh+=list(H)
    print(f"{clip:22s} n {len(H)}  p10 {np.percentile(H,10):.3f} p25 {np.percentile(H,25):.3f} p50 {np.median(H):.3f} p75 {np.percentile(H,75):.3f} p90 {np.percentile(H,90):.3f} min {H.min():.3f} max {H.max():.3f}")
H=np.array(allh); print(f"ALL n {len(H)}  p5 {np.percentile(H,5):.3f} p10 {np.percentile(H,10):.3f} p25 {np.percentile(H,25):.3f} p50 {np.median(H):.3f} p75 {np.percentile(H,75):.3f} p90 {np.percentile(H,90):.3f} p95 {np.percentile(H,95):.3f}")
