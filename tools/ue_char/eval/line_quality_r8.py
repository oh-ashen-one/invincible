# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 08: stair-step / wobble measure for a line or an edge in a native-resolution capture (critic r07: 'web lines stair-step').

  python3 tools/ue_char/eval/line_quality_r8.py IMAGE x0 y0 x1 y1 --ref R G B [--bg R G B] [--tol 70] [--yellow] [--label NAME]

The ROI must contain ONE roughly straight or smoothly curved line (or an edge between two flat colours), running mostly horizontally or vertically.  For every column (or
row, whichever the line crosses) the sub-pixel centre of the line is the weight-centroid of its colour similarity to --ref; the track is compared with a smooth fit (Savitzky-Golay
style polynomial, window 41 px).  Reported:
  max_dev_px / rms_dev_px      deviation of the centroid track from the smooth fit
  max_jump_px                  largest change of the centroid between neighbouring columns beyond the local slope (a 1-px staircase shows jumps of ~1 px every few px)
  worst_plateau_px             longest run of columns whose centroid stays within 0.08 px while the fit moves by >= 0.35 px over the run: the width of a stair tread
A stair step 'wider than 2 px' = worst_plateau_px > 2 with max_jump_px > 0.6."""
import sys, json
import numpy as np
import cv2
a = sys.argv[1:]
img = a[0]; x0, y0, x1, y1 = [int(v) for v in a[1:5]]
def opt(k, n, d):
    if k in a: i = a.index(k); return [float(v) for v in a[i + 1:i + 1 + n]]
    return d
ref = np.array(opt('--ref', 3, [224, 120, 12]), np.float32)
tol = opt('--tol', 1, [70])[0]
label = a[a.index('--label') + 1] if '--label' in a else ''
im = cv2.imread(img)[y0:y1, x0:x1, ::-1].astype(np.float32)
d = np.linalg.norm(im - ref, axis=-1)
w = np.clip(1 - d / tol, 0, 1) ** 2
if '--yellow' in a:      # amber / yellow detector: (R + G) / 2 - B is large on amber, ~0 on white stitching and negative on teal / blue
    yl = (im[..., 0] + im[..., 1]) / 2 - im[..., 2]
    w = np.clip((yl - 45.0) / 55.0, 0, 1) ** 2
H, W = w.shape
horiz = True
cols = w
# decide the dominant direction from the principal axis of the weight mass
ys, xs = np.mgrid[0:H, 0:W]
m = w.sum() + 1e-9
cx = (w * xs).sum() / m; cy = (w * ys).sum() / m
cov = np.array([[(w * (xs - cx) ** 2).sum(), (w * (xs - cx) * (ys - cy)).sum()], [(w * (xs - cx) * (ys - cy)).sum(), (w * (ys - cy) ** 2).sum()]]) / m
ev, evec = np.linalg.eigh(cov)
ax = evec[:, 1]
horiz = abs(ax[0]) >= abs(ax[1])
W_ = w if horiz else w.T
n_l, n_p = W_.shape[1], W_.shape[0]          # length along the line, extent across
idx = np.arange(n_p)[:, None]
den = W_.sum(0)
ok = den > 0.6
if ok.sum() > 20:
    med = float(np.median(den[ok])); ok = ok & (den > 0.8 * med) & (den < 1.25 * med)      # only columns where the whole line is inside the ROI (not cut by its border, not merged with another feature)
track = (W_ * idx).sum(0) / np.maximum(den, 1e-9)
pos = np.arange(n_l)[ok].astype(np.float64); tr = track[ok].astype(np.float64)
if len(pos) < 60:
    print(json.dumps(dict(label=label, error='line too short or not found', columns=int(len(pos))))); sys.exit(0)
win = min(41, (len(pos) // 2) * 2 - 1)
# running polynomial (order 2) smoothing
sm = np.zeros_like(tr); hw = win // 2
for i in range(len(pos)):
    lo, hi = max(0, i - hw), min(len(pos), i + hw + 1)
    c = np.polyfit(pos[lo:hi] - pos[i], tr[lo:hi], 2); sm[i] = c[-1]
dev = tr - sm
jump = np.abs(np.diff(tr) - np.diff(sm))
# plateaus: columns with a flat centroid while the smooth fit moves
best = 0; i = 0
while i < len(tr) - 1:
    j = i
    while j + 1 < len(tr) and abs(tr[j + 1] - tr[i]) < 0.08 and pos[j + 1] - pos[j] == 1: j += 1
    if abs(sm[j] - sm[i]) >= 0.35: best = max(best, int(pos[j] - pos[i] + 1))
    i = j + 1
res = dict(label=label, image=img.split('/')[-1], roi=[x0, y0, x1, y1], direction='horizontal' if horiz else 'vertical', columns=int(len(pos)), line_width_px=round(float(den[ok].mean() * 1.0), 2),
           max_dev_px=round(float(np.abs(dev).max()), 2), rms_dev_px=round(float(np.sqrt((dev ** 2).mean())), 3), max_jump_px=round(float(jump.max()), 2), worst_plateau_px=best)
print(json.dumps(res))
