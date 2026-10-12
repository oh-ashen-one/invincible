#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r23: facade luma (BT.709, ring = hero box grown by its size, box excluded; as r22 L22) on w1's WALL frames at 12 fps (w1 has no side run now)
import csv, subprocess, sys
import numpy as np
RD = sys.argv[1]; name = sys.argv[2] if len(sys.argv) > 2 else 'w1_wallrun_tall_zip'
rows = list(csv.DictReader(open(f'{RD}/{name}_telemetry.csv')))
def fl(r, k):
    try: return float(r[k])
    except (KeyError, ValueError): return float('nan')
wall = [i for i, r in enumerate(rows) if r['mode'] == 'wall']
t0, t1 = fl(rows[wall[0]], 't'), fl(rows[wall[-1]], 't')
lum, zs = [], []
t = t0
while t <= t1:
    i = min(wall, key=lambda j: abs(fl(rows[j], 't') - t)); r = rows[min(i + 1, len(rows) - 1)]
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', f'{t:.4f}', '-i', f'{RD}/{name}.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    t += 1 / 12
    if len(raw) < 1920 * 1080 * 3: continue
    img = np.frombuffer(raw[:1920 * 1080 * 3], np.uint8).reshape(1080, 1920, 3).astype(float)
    tp, b, l, rr = [fl(r, c) for c in ('px_top', 'px_bottom', 'px_left', 'px_right')]
    if min(tp, b, l, rr) < 0: continue
    bh, bw = b - tp, rr - l
    Y = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    m = np.zeros((1080, 1920), bool); m[int(max(0, tp - bh)):int(min(1080, b + bh)), int(max(0, l - bw)):int(min(1920, rr + bw))] = True
    m[int(tp):int(b), int(l):int(rr)] = False
    lum.append(float(Y[m].mean())); zs.append(fl(rows[i], 'z_m'))
print(f'{name} wall {t0:.2f}-{t1:.2f} s z {min(zs):.1f}-{max(zs):.1f}: {len(lum)} frames at 12 fps, facade luma min {min(lum):.1f} med {sorted(lum)[len(lum)//2]:.1f} max {max(lum):.1f}, >= 45 in {sum(x >= 45 for x in lum)}/{len(lum)}')
