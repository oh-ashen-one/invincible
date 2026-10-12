#!/usr/bin/env python3
"""Round 10: an independent PIXEL check of the knockdowns (the bone log is the engine's own measurement, this is the video's): YOLO11x-seg on every 0.2 s of a fight clip; a person whose box is
wider than tall (w / h >= 1.0; standing people measure 0.3 - 0.6) counts as lying.  Prints, per clip, the number of lying people per sample and the longest time two or more lie together.
Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.
  $P2_SCRATCH/r4/yv/bin/python tools/ue_char/fight/video_grounded.py clip.mp4 [out.json]     (YOLO_WEIGHTS = yolo11x-seg.pt)"""
import sys, os, json
import cv2
from ultralytics import YOLO
clip = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
w = os.environ.get('YOLO_WEIGHTS', '/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt')
m = YOLO(w); cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS) or 60.0; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); step = int(round(0.2 * fps))
rows = []
for f in range(0, n, step):
    cap.set(cv2.CAP_PROP_POS_FRAMES, f); ok, im = cap.read()
    if not ok: break
    r = m.predict(im, classes=[0], conf=0.25, verbose=False, device='cpu')[0]
    lying = standing = 0
    for b in r.boxes.xyxy.cpu().numpy():
        bw, bh = b[2] - b[0], b[3] - b[1]
        if bh < 0.03 * im.shape[0]: continue
        if bw / max(bh, 1) >= 1.0: lying += 1
        else: standing += 1
    rows.append((round(f / fps, 2), lying, standing))
best = cur = 0; start = None; runs = []
for t, ly, st in rows:
    if ly >= 2:
        if start is None: start = t
        cur = t - start + 0.2
    else:
        if start is not None: runs.append((start, round(cur, 2)))
        start = None; cur = 0
if start is not None: runs.append((start, round(cur, 2)))
longest = max([r[1] for r in runs], default=0.0)
print(os.path.basename(clip), 'samples', len(rows), 'max lying', max(r[1] for r in rows), '| runs with >= 2 lying (start s, length s):', runs, '| longest %.2f s' % longest)
print('lying per 0.2 s:', ''.join(str(r[1]) for r in rows))
if out: json.dump({'clip': clip, 'rows': rows, 'runs_ge2_lying': runs, 'longest_s': longest}, open(out, 'w'))
