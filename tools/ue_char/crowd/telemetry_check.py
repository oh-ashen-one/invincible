# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: walker separation from the engine's own telemetry (-WHWalkerLog=<csv>, one row per walker per rendered frame).

  python3 tools/ue_char/crowd/telemetry_check.py LOG.csv [--radius 40] [--need 35] [--out DIR] [--tag NAME]

Reads the CSV (frame,time,label,x,y,yaw,offset,min_pair_dist), recomputes for EVERY frame the pairwise ground-plane distance between all walkers (the
log's own min_pair_dist column is only cross-checked), and reports per director shot (tracking = time < the restart, wide = after it; a restart is a jump
of walker positions between consecutive frames):
  frames, walkers, smallest centre distance and the pair, frames with a distance below 2 x need (two capsules of radius `need` overlap: the brief's 35 cm)
  and below 2 x radius (the capsule the game uses), largest lateral offset from the lane, largest heading deviation from the lane, largest yaw rate.
Writes DIR/<tag>_separation.json and DIR/<tag>_separation.png (smallest pair distance per frame; the 2 x 35 cm and 2 x 40 cm lines)."""
import sys, os, json, math, csv
import numpy as np

a = sys.argv[1:]
log = a[0]
def opt(k, d):
    return type(d)(a[a.index(k) + 1]) if k in a else d
R = opt('--radius', 40.0); NEED = opt('--need', 35.0); out = opt('--out', os.path.dirname(os.path.abspath(log))); tag = opt('--tag', os.path.splitext(os.path.basename(log))[0])
rows = list(csv.DictReader(open(log)))
frames = sorted({int(r['frame']) for r in rows}); labels = sorted({r['label'] for r in rows})
fi = {f: i for i, f in enumerate(frames)}; li = {l: i for i, l in enumerate(labels)}
X = np.full((len(frames), len(labels)), np.nan); Y = X.copy(); YAW = X.copy(); OFF = X.copy(); T = np.zeros(len(frames)); LOGMIN = np.full(len(frames), np.nan)
for r in rows:
    i, j = fi[int(r['frame'])], li[r['label']]
    X[i, j], Y[i, j], YAW[i, j], OFF[i, j] = float(r['x']), float(r['y']), float(r['yaw']), float(r['offset']); T[i] = float(r['time'])
    LOGMIN[i] = float(r['min_pair_dist']) if np.isnan(LOGMIN[i]) else min(LOGMIN[i], float(r['min_pair_dist']))
n = len(labels)
D = np.sqrt((X[:, :, None] - X[:, None, :]) ** 2 + (Y[:, :, None] - Y[:, None, :]) ** 2)
D[:, np.arange(n), np.arange(n)] = np.inf
mind = np.nanmin(D.reshape(len(frames), -1), axis=1)
arg = [np.unravel_index(np.nanargmin(D[i]), (n, n)) for i in range(len(frames))]
# shots: a restart = walkers jump (> 150 cm between consecutive frames for at least half of them)
step = np.sqrt(np.diff(X, axis=0) ** 2 + np.diff(Y, axis=0) ** 2)
jumps = [i + 1 for i in range(len(step)) if np.nanmedian(step[i]) > 150.0]
edges = [0] + jumps + [len(frames)]
res = dict(log=os.path.basename(log), frames=len(frames), walkers=n, radius_cm=R, need_cm=NEED, restarts_at_frames=[int(frames[j]) for j in jumps],
           log_column_agrees=bool(np.nanmax(np.abs(np.minimum(LOGMIN, 1e6) - np.minimum(mind, 1e6))) < 1.0), shots=[])
for s in range(len(edges) - 1):
    a_, b_ = edges[s], edges[s + 1]
    if b_ - a_ < 2: continue
    m = mind[a_:b_]; k = int(np.argmin(m)); pi, pj = arg[a_ + k]
    lane = np.nanmax(np.abs(OFF[a_:b_]))
    dyaw = np.abs(((np.diff(YAW[a_:b_], axis=0) + 180) % 360) - 180) / np.maximum(np.diff(T[a_:b_])[:, None], 1e-6)
    base = np.nanmedian(np.where(np.abs(np.cos(np.radians(YAW[a_:b_]))) > 0.5, np.round(YAW[a_:b_] / 180) * 180, np.nan), axis=0)   # lane heading = 0 or 180
    dev = np.abs(((YAW[a_:b_] - base[None, :] + 180) % 360) - 180)
    res['shots'].append(dict(t0=round(float(T[a_]), 3), t1=round(float(T[b_ - 1]), 3), frames=int(b_ - a_), min_distance_cm=round(float(m.min()), 2),
                             at_time=round(float(T[a_ + k]), 3), pair=[labels[pi], labels[pj]], frames_below_2x_need=int((m < 2 * NEED).sum()), frames_below_2x_radius=int((m < 2 * R - 0.01).sum()),
                             max_lane_offset_cm=round(float(lane), 1), max_heading_dev_deg=round(float(np.nanmax(dev)), 1), max_yaw_rate_deg_s=round(float(np.nanmax(dyaw)), 1),
                             median_min_distance_cm=round(float(np.median(m)), 1)))
res['overall_min_distance_cm'] = round(float(mind.min()), 2)
res['frames_below_2x_need'] = int((mind < 2 * NEED).sum()); res['frames_below_2x_radius'] = int((mind < 2 * R - 0.01).sum())
os.makedirs(out, exist_ok=True)
json.dump(res, open(os.path.join(out, tag + '_separation.json'), 'w'), indent=1)
print(json.dumps(res))
try:
    import cv2
    W, H = 1400, 420; img = np.full((H, W, 3), 255, np.uint8)
    top = max(300.0, float(np.nanmax(np.minimum(mind, 400))) + 10)
    def px(t, d): return int(60 + (t - T[0]) / max(T[-1] - T[0], 1e-6) * (W - 90)), int(H - 40 - min(d, top) / top * (H - 80))
    for lab, dd, col in (('2 x 35 cm', 2 * NEED, (0, 0, 255)), ('2 x %d cm (game capsule)' % R, 2 * R, (0, 140, 255))):
        p0, p1 = px(T[0], dd), px(T[-1], dd); cv2.line(img, p0, p1, col, 1); cv2.putText(img, lab, (p0[0] + 4, p0[1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
    pts = np.array([px(T[i], mind[i]) for i in range(len(frames))], np.int32); cv2.polylines(img, [pts], False, (60, 60, 60), 1)
    for j in jumps: x0_, _ = px(T[j], 0); cv2.line(img, (x0_, 20), (x0_, H - 40), (200, 200, 200), 1); cv2.putText(img, 'shot restart', (x0_ + 4, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
    cv2.putText(img, 'smallest centre-to-centre distance between any two walkers (cm), per rendered frame: %s' % tag, (60, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.imwrite(os.path.join(out, tag + '_separation.png'), img)
except Exception as e:
    print('plot skipped', e)
