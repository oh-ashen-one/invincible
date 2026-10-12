# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Per-frame head-top / feet-bottom / x of the hero suit mask (saturated red + saturated blue) in the static-camera leap clip.

  python3 leap_track.py hero_run_leap_side.mp4 OUT.json [t0 t1]

Head top = min y of the mask, feet bottom = max y.  Reports the take-off crouch (head-top drop in px before the apex) and the apex, so CH10
(a take-off crouch, no pop) is a number not an impression.  Round 05 measured the same clip with an ad-hoc script: head top 410 px at 1.35 s -> 514 px
at 1.517 s, apex ~1.85 s."""
import sys, json
import numpy as np, cv2
src, out = sys.argv[1], sys.argv[2]
t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5; t1 = float(sys.argv[4]) if len(sys.argv) > 4 else 6.4
cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS)
rows = []; i = 0
while True:
    ok, im = cap.read()
    if not ok: break
    t = i / fps; i += 1
    if t < t0 or t > t1: continue
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    red = ((h < 8) | (h > 170)) & (s > 150) & (v > 90)
    blue = (h > 105) & (h < 130) & (s > 150) & (v > 50) & (v < 190)
    teal = (h > 82) & (h < 112) & (s > 120) & (v > 40); amber = (h > 8) & (h < 26) & (s > 170) & (v > 110)      # round 08: Tessera
    m = (red | blue | teal | amber).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if n <= 1: continue
    keep = [k for k in range(1, n) if st[k, 4] > 150]
    if not keep: continue
    ys, xs = np.where(np.isin(lab, keep))
    rows.append([round(t, 3), int(ys.min()), int(ys.max()), int(xs.mean())])
a = np.array(rows)
T = a[:, 0]; head = a[:, 1].astype(float)
# first leap = the deepest head-top rise (apex) after 1.0 s; crouch = the lowest head in the 0.6 s before it vs the running baseline before that
win = (T >= 1.0) & (T <= 3.0)
ia = int(np.where(win)[0][np.argmin(head[win])])
apex_t = float(T[ia])
pre = (T >= apex_t - 0.6) & (T <= apex_t); base = (T >= apex_t - 1.2) & (T < apex_t - 0.6)
crouch_y = float(head[pre].max()); base_y = float(np.median(head[base])); apex_y = float(head[ia])
t_crouch = float(T[pre][np.argmax(head[pre])])
res = dict(note='per frame: (t s, head-top y px, feet-bottom y px, mean x px) of the saturated red+blue suit mask; 1080p60 clip, static camera',
           apex_t=apex_t, apex_head_top_y=apex_y, run_head_top_y=base_y, crouch_t=t_crouch, crouch_head_top_y=crouch_y,
           crouch_drop_px=round(crouch_y - base_y, 1), rise_apex_px=round(base_y - apex_y, 1), crouch_to_apex_s=round(apex_t - t_crouch, 3), frames=rows)
json.dump(res, open(out, 'w'))
print(json.dumps({k: v for k, v in res.items() if k != 'frames'}))
