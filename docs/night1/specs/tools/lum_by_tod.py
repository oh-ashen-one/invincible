# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). Director spec instrument, 2026-09-29. Run with a venv holding ultralytics+opencv (see specs README lines).
import re, cv2, numpy as np, json, collections
R='/Users/midir/spiderman-learnings/refs/'
rows=[]
for line in open(R+'INDEX.md'):
    m = re.match(r"\|\s*`([^`]+\.jpg)`\s*\|(.*?)\|(.*?)\|(.*?)\|", line)
    if m: rows.append((m.group(1), m.group(4).strip()))
out=[]
for f,tod in rows:
    im = cv2.imread(R+f)
    if im is None: continue
    if im.shape[1] > 1920: im = cv2.resize(im,(1920, int(im.shape[0]*1920/im.shape[1])), interpolation=cv2.INTER_AREA)
    b,g,r = [im[:,:,k].astype(np.float32) for k in range(3)]
    Y = 0.2126*r+0.7152*g+0.0722*b
    mx = im.max(axis=2)
    H = Y.shape[0]
    d = dict(f=f, tod=tod, src=f.split('__')[-1].split('_')[0], mean=float(Y.mean()), p1=float(np.percentile(Y,1)), p5=float(np.percentile(Y,5)), p50=float(np.median(Y)), p95=float(np.percentile(Y,95)), p99=float(np.percentile(Y,99)),
             lt10=float((Y<10).mean()*100), lt25=float((Y<25).mean()*100), clip=float((mx>=250).mean()*100), clipY=float((Y>=250).mean()*100),
             bot_mean=float(Y[2*H//3:].mean()), top_mean=float(Y[:H//3].mean()))
    out.append(d)
json.dump(out, open('m/lum.json','w'))
def cat(d):
    t=d['tod'].lower()
    if 'night' in t: return 'night'
    if 'midday' in t or 'overcast' in t: return 'midday_overcast'
    if 'golden' in t or 'sunset' in t: return 'golden_sunset'
    if 'dusk' in t: return 'dusk'
    if 'afternoon' in t or t.startswith('day'): return 'day_afternoon'
    return 'other'
G=collections.defaultdict(list)
for d in out:
    if d['f'].startswith('ui/') or 'press' in d['f'] or 'trailer' in d['f']: continue
    G[cat(d)].append(d)
for k,v in G.items():
    print(f"\n== {k}  n={len(v)}")
    for key in ['mean','p1','p5','p50','p95','p99','lt10','lt25','clip','bot_mean']:
        a=np.array([d[key] for d in v]); print(f"  {key:8s} p10 {np.percentile(a,10):7.2f}  med {np.median(a):7.2f}  p90 {np.percentile(a,90):7.2f}  min {a.min():7.2f} max {a.max():7.2f}")
