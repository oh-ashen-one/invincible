#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island r04: camera-in-foliage check on a rendered route movie. Frames are sampled at --fps (default 4, like the critic), each frame's share of
FOLIAGE pixels is measured: green-dominant (G > 1.06 R and G > 1.06 B), not dark (G >= 18 of 255) and not grey (max - min >= 6). The city
has no other large green-dominant surfaces at street level (no green facades; park lawns appear only from roof height and far away), so a
frame whose foliage share is > 40 % is a camera inside / right behind a crown. Calibrated on the round-03 movies against the r03 critic's
readings (README of round 04).
usage: island_foliage_check.py <movie.mp4> [out.json] [--fps 4] [--limit 40]"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image


def foliage_share(img):
    a = np.asarray(img.convert('RGB'), np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (g * 100 > r * 106) & (g * 100 > b * 106) & (g >= 18) & ((a.max(-1) - a.min(-1)) >= 6)
    return float(m.mean())


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    fps = float(sys.argv[sys.argv.index('--fps') + 1]) if '--fps' in sys.argv else 4.0
    lim = float(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 40.0
    mov = args[0]
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['ffmpeg', '-v', 'error', '-i', mov, '-vf', 'fps=%g,scale=480:-2' % fps, os.path.join(td, 'f%05d.png')], check=True)
        fs = sorted(f for f in os.listdir(td) if f.endswith('.png'))
        vals = [foliage_share(Image.open(os.path.join(td, f))) * 100.0 for f in fs]
    T = [round(i / fps, 3) for i in range(len(vals))]
    over = [[t, round(v, 1)] for t, v in zip(T, vals) if v > lim]
    k = int(np.argmax(vals)) if vals else 0
    out = {'movie': mov, 'fps': fps, 'frames': len(vals), 'limit_pct': lim, 'max_pct': round(max(vals), 1) if vals else None,
           'max_at_t': T[k] if vals else None, 'frames_over_limit': len(over), 'over': over[:60],
           'mean_pct': round(float(np.mean(vals)), 2) if vals else None, 'pass': not over, 'series': [round(v, 1) for v in vals]}
    s = json.dumps(out)
    if len(args) > 1: open(args[1], 'w').write(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != 'series'}))


if __name__ == '__main__':
    main()
