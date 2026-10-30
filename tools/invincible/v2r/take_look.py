# First-look aids for a Seedance take: a frame strip (N frames across, both panels, time stamps) and a motion-energy curve per panel
# (mean absolute frame difference inside the body's silhouette bbox, per frame, as a PNG plot + a text summary of freezes).
#   python3 take_look.py <take.mp4> <out_prefix> [--n 12]
import sys, subprocess, json, os, argparse
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('mp4'); ap.add_argument('out'); ap.add_argument('--n', type=int, default=12); ap.add_argument('--freeze', type=float, default=0.25)
a = ap.parse_args()
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames,duration', '-of', 'json', a.mp4]))['streams'][0]
W, H = int(probe['width']), int(probe['height']); num, den = probe['r_frame_rate'].split('/'); fps = float(num) / float(den)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.mp4, '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32); T = len(fr)
half = W // 2
curves = {}
for name, sl in (('front', slice(0, half)), ('side', slice(half, W))):
    p = fr[:, :, sl]; bgv = np.median(p[0]); mask = (np.abs(p - bgv) > 18).any(0)
    ys, xs = np.where(mask); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    d = np.abs(np.diff(p[:, y0:y1, x0:x1], axis=0)).mean((1, 2)); curves[name] = d
mean_e = np.mean([c.mean() for c in curves.values()])
freeze = []
for name, c in curves.items():
    low = c < a.freeze * c.mean(); runs = []; s = None
    for i, v in enumerate(list(low) + [False]):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s >= int(0.3 * fps): runs.append((s / fps, i / fps))
            s = None
    freeze.append((name, runs))
# strip
idx = np.linspace(0, T - 1, a.n).round().astype(int)
tile_h = 180; tile_w = int(W * tile_h / H)
strip = np.zeros((tile_h, tile_w * a.n), np.uint8)
for k, i in enumerate(idx):
    img = fr[i]; ys = (np.arange(tile_h) * H / tile_h).astype(int); xs = (np.arange(tile_w) * W / tile_w).astype(int)
    strip[:, k * tile_w:(k + 1) * tile_w] = img[ys][:, xs]
from PIL import Image, ImageDraw
im = Image.fromarray(strip).convert('RGB'); dr = ImageDraw.Draw(im)
for k, i in enumerate(idx): dr.text((k * tile_w + 4, 4), '%.2fs' % (i / fps), fill=(255, 220, 60))
im.save(a.out + '_strip.jpg', quality=88)
# curve plot (no matplotlib dependency: draw with PIL)
pw, ph = 900, 220; pl = Image.new('RGB', (pw, ph), (20, 20, 20)); d2 = ImageDraw.Draw(pl)
mx = max(c.max() for c in curves.values()) or 1.0
for name, col in (('front', (90, 170, 255)), ('side', (255, 170, 60))):
    c = curves[name]; pts = [(int(i * (pw - 20) / max(1, len(c) - 1)) + 10, ph - 10 - int(v / mx * (ph - 30))) for i, v in enumerate(c)]
    d2.line(pts, fill=col, width=2); d2.text((10 if name == 'front' else 80, 4), name, fill=col)
for s in range(int(T / fps) + 1): x = int(s * fps * (pw - 20) / max(1, T - 1)) + 10; d2.line([(x, ph - 10), (x, ph - 4)], fill=(200, 200, 200)); d2.text((x + 2, ph - 16), '%ds' % s, fill=(160, 160, 160))
pl.save(a.out + '_energy.png')
summary = dict(frames=T, fps=fps, size=[W, H], mean_energy=float(mean_e), energy_front=[round(float(x), 2) for x in curves['front']], energy_side=[round(float(x), 2) for x in curves['side']], freezes={n: [[round(s, 2), round(e, 2)] for s, e in r] for n, r in freeze})
json.dump(summary, open(a.out + '_look.json', 'w'))
print('LOOK frames %d fps %.2f mean_energy %.2f freezes %s' % (T, fps, mean_e, {n: [[round(s, 2), round(e, 2)] for s, e in r] for n, r in freeze}))
