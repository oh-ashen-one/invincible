# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: pick crowd still frames from the id-movie analyses.  A frame qualifies when no walker's head touches another walker (head_overlap.py: head_body == 0) and as
many walkers as possible are visible; ties are broken by fewer touching silhouette pairs (id_overlap.py).  Prints the best candidates at least --gap frames apart.

  python3 tools/ue_char/crowd/pick_frames.py HEAD_OVERLAP.json ID_OVERLAP.json [--n 6] [--gap 40] [--lo 120] [--hi 470] [--min-visible 10]
"""
import sys, json
a = sys.argv[1:]
def opt(k, d):
    return type(d)(a[a.index(k) + 1]) if k in a else d
n = opt('--n', 6); gap = opt('--gap', 40); lo = opt('--lo', 120); hi = opt('--hi', 470); minvis = opt('--min-visible', 10)
H = {p['frame']: p for p in json.load(open(a[0]))['per_frame']}
I = {p['frame']: p for p in json.load(open(a[1]))['per_frame']}
cand = []
for f, h in H.items():
    if not (lo <= f <= hi) or f not in I: continue
    if h['head_body']: continue
    vis = I[f]['visible']
    if vis < minvis: continue
    cand.append((len(I[f]['contacts']), -vis, f))
cand.sort()
out = []
for c, v, f in cand:
    if all(abs(f - g) >= gap for _, _, g in out): out.append((c, v, f))
    if len(out) >= n: break
print(json.dumps([dict(frame=f, time_s=round(f / 60.0, 3), visible=-v, touching_pairs=c) for c, v, f in out]))
print('qualifying frames: %d of %d' % (len(cand), len(H)))
