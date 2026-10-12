#!/usr/bin/env python3
"""r04: sigma-3 high-pass SD (luma 0-255) of the PARK GROUND seen in the last 5 s of t5_avenue_to_park at 1080p (criterion: >= 5).
Frames at 4 fps from the movie (default last 5 s of a 15.4 s movie = 10.4 .. 15.4 s). Lawn pixels: green classifier (g > 1.02 r, g > 1.08 b, 30 <= Y <= 220), the hero's park-rectangle test is taken from the
telemetry (frames where the hero is over the park rectangle x -234..234, y -2151..-569 only; others are listed as 'outside'). Per frame: 96 x 96 windows (stride 48) with >= 85 % lawn pixels -> hp3 SD;
frame value = median of the windows; the verdict uses the median over the frames over the park.
usage: t5_ground_sd.py <movie.mp4> <telemetry.csv> <out.json> [t0=10.4] [t1=15.4]"""
import sys, os, json, subprocess, tempfile, glob, csv
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, uniform_filter
mp4, tel, out = sys.argv[1:4]; T0 = float(sys.argv[4]) if len(sys.argv) > 4 else 10.4; T1 = float(sys.argv[5]) if len(sys.argv) > 5 else 15.4
rows = list(csv.DictReader(open(tel))); tt = np.array([float(r['t']) for r in rows]); hx = np.array([float(r['x_m']) for r in rows]); hy = np.array([float(r['y_m']) for r in rows]); haf = np.array([float(r['height_above_floor_m']) for r in rows])
tmp = tempfile.mkdtemp(prefix='t5sd_', dir='/Users/midir/sm2-n1/_scratch/terrain')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', str(T0), '-t', str(T1 - T0 + 0.01), '-i', mp4, '-vf', 'fps=4', '-q:v', '2', os.path.join(tmp, 'f%04d.jpg')], check=True)
frames = []
for i, f in enumerate(sorted(glob.glob(os.path.join(tmp, 'f*.jpg')))):
    t = T0 + i * 0.25; k = int(np.argmin(np.abs(tt - t)))
    over = bool(-234 < hx[k] < 234 and -2151 < hy[k] < -569)
    a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32); Y = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lawn = ((g > 1.02 * r) & (g > 1.08 * b) & (Y >= 30) & (Y <= 220)).astype(np.float32)
    hp = Y - gaussian_filter(Y, 3.0); W = 96
    share = uniform_filter(lawn, W, mode='constant'); var = uniform_filter(hp * hp, W, mode='constant') - uniform_filter(hp, W, mode='constant') ** 2
    sds = [float(np.sqrt(max(var[y + W // 2, x + W // 2], 0))) for y in range(0, Y.shape[0] - W, 48) for x in range(0, Y.shape[1] - W, 48) if share[y + W // 2, x + W // 2] >= 0.85]
    frames.append({'t_s': round(t, 2), 'hero_over_park': over, 'hero_haf_m': round(float(haf[k]), 1), 'lawn_pct': round(100 * float(lawn.mean()), 1), 'windows': len(sds), 'median_sd3': round(float(np.median(sds)), 2) if sds else None,
                   'p10_sd3': round(float(np.percentile(sds, 10)), 2) if sds else None})
for f in glob.glob(os.path.join(tmp, '*.jpg')): os.remove(f)
os.rmdir(tmp)
ov = [f for f in frames if f['hero_over_park'] and f['median_sd3'] is not None]
lw = [f for f in frames if f['lawn_pct'] >= 10 and f['median_sd3'] is not None]   # frames where park lawn fills >= 10 % of the picture (park ground in view, hero over the park or not)
bd = [f for f in ov if 25.0 <= f['hero_haf_m'] <= 40.0]   # r04 SPEC E10(d) reads 'at 25-40 m': the frames of the window whose hero height above the floor is in that band
res = {'frames_in_25_40m_band': len(bd), 'median_in_25_40m_band': round(float(np.median([f['median_sd3'] for f in bd])), 2) if bd else None, 'min_in_25_40m_band': min((f['median_sd3'] for f in bd), default=None), 'pass_band_ge_5': bool(bd) and min(f['median_sd3'] for f in bd) >= 5.0,
       'frames_with_lawn_ge_10pct': len(lw), 'median_over_lawn_frames': round(float(np.median([f['median_sd3'] for f in lw])), 2) if lw else None, 'min_over_lawn_frames': min((f['median_sd3'] for f in lw), default=None),
       'window_s': [T0, T1], 'frames': len(frames), 'frames_over_park': sum(f['hero_over_park'] for f in frames), 'median_over_frames': round(float(np.median([f['median_sd3'] for f in ov])), 2) if ov else None,
       'min_over_frames': min((f['median_sd3'] for f in ov), default=None), 'pass_ge_5': bool(ov) and min(f['median_sd3'] for f in ov) >= 5.0, 'per_frame': frames}
json.dump(res, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'per_frame'})); [print(f) for f in frames]
