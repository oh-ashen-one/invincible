#!/usr/bin/env python3
# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). P6 city life.
# Contact strip of a clip: one frame every N seconds in a grid (JPEG), for the round folder (evidence a reader can open without a video player) + mean luma of the first frames
# (checks the warm-up trim: frame 0 must be lit).
#   python3 tools/life/clip_strip.py clip.mp4 out.jpg [every_s=1.0] [cols=4] [tile_w=480]
import subprocess, sys, os, numpy as np
from PIL import Image
clip, out = sys.argv[1], sys.argv[2]
every = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0; cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4; tw = int(sys.argv[5]) if len(sys.argv) > 5 else 480
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', clip], capture_output=True, text=True).stdout.strip())
n = int(dur / every)
tiles = []
tmp = out + '.tmp.png'
for i in range(n):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % (i * every), '-i', clip, '-frames:v', '1', '-vf', 'scale=%d:-1' % tw, tmp], check=True)
    tiles.append(Image.open(tmp).convert('RGB'))
os.remove(tmp)
th = tiles[0].height; rows = (len(tiles) + cols - 1) // cols
W = Image.new('RGB', (cols * tw, rows * th))
for i, t in enumerate(tiles): W.paste(t, ((i % cols) * tw, (i // cols) * th))
W.save(out, quality=88)
# luma of frames 0..8
lum = []
for f in range(0, 9):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', clip, '-vf', 'select=eq(n\\,%d),scale=320:-1' % f, '-frames:v', '1', tmp], check=True)
    lum.append(float(np.asarray(Image.open(tmp).convert('L')).mean()))
os.remove(tmp)
print('%s: %.2f s, %d tiles -> %s; mean luma frames 0..8: %s' % (os.path.basename(clip), dur, len(tiles), out, ' '.join('%.0f' % x for x in lum)))
