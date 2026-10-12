#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r26 contact sheets (CPU, ffmpeg + PIL):
#   sheets.py clip <mp4> <out.jpg> <t0> <t1> <n> [cols] [--crop x,y,w,h] [--label]   n frames evenly over t0..t1, tiled, <= 2048 px wide
#   sheets.py suit <round dir> <out.jpg> [default.png ...]   one frame per clip (the row with the tallest hero px box, cropped around the hero)
#                                                            + the default-launch frames: the suit proof sheet
import sys, os, subprocess, csv, tempfile
from PIL import Image, ImageDraw
MAXW = 2048


def grab(mp4, t, crop=None):
    fd, p = tempfile.mkstemp(suffix='.png'); os.close(fd)
    vf = [] if not crop else ['-vf', 'crop=%d:%d:%d:%d' % (crop[2], crop[3], crop[0], crop[1])]
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % t, '-i', mp4, '-frames:v', '1'] + vf + [p], check=True)
    im = Image.open(p).convert('RGB'); os.remove(p); return im


def tile(ims, cols, labels, out):
    w0 = MAXW // cols
    th = [im.resize((w0, max(1, round(im.height * w0 / im.width))), Image.LANCZOS) for im in ims]
    h0 = max(t.height for t in th)
    rows = (len(th) + cols - 1) // cols
    sheet = Image.new('RGB', (w0 * cols, h0 * rows), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for i, (t, lab) in enumerate(zip(th, labels)):
        x, y = (i % cols) * w0, (i // cols) * h0
        sheet.paste(t, (x, y))
        if lab:
            d.rectangle([x, y, x + 8 * len(lab) + 8, y + 16], fill=(0, 0, 0)); d.text((x + 4, y + 2), lab, fill=(255, 255, 255))
    sheet.save(out, quality=90)
    print('sheet', out, sheet.size)


def main():
    mode = sys.argv[1]
    if mode == 'clip':
        mp4, out, t0, t1, n = sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6])
        cols = int(sys.argv[7]) if len(sys.argv) > 7 and not sys.argv[7].startswith('--') else min(n, 5)
        crop = None
        if '--crop' in sys.argv: crop = [int(v) for v in sys.argv[sys.argv.index('--crop') + 1].split(',')]
        dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4], capture_output=True, text=True).stdout.strip() or 1e9)
        t1 = min(t1, dur - 0.05)   # never ask for a frame past the end of the clip
        ts = [t0 + (t1 - t0) * i / max(1, n - 1) for i in range(n)]
        lab = '--label' in sys.argv
        tile([grab(mp4, t, crop) for t in ts], cols, ['%.1f s' % t if lab else '' for t in ts], out)
    elif mode == 'suit':
        rd, out = sys.argv[2], sys.argv[3]
        ims, labs = [], []
        for f in sorted(os.listdir(rd)):
            if not f.endswith('.mp4'): continue
            name = f[:-4]; tel = os.path.join(rd, name + '_telemetry.csv')
            if not os.path.exists(tel): continue
            rows = list(csv.DictReader(open(tel)))
            best, bh = None, -1
            for i in range(len(rows) - 1):
                r = rows[i + 1]   # px columns are sampled at the start of the next frame
                try: top, bot, le, ri = float(r['px_top']), float(r['px_bottom']), float(r['px_left']), float(r['px_right'])
                except (KeyError, ValueError): continue
                if top < 0 or le <= 2 or ri >= 1917 or top <= 2 or bot >= 1077: continue
                if bot - top > bh: bh, best = bot - top, (i, top, bot, le, ri)
            if not best: continue
            i, top, bot, le, ri = best
            t = float(rows[i]['t'])
            cx, cy = (le + ri) / 2, (top + bot) / 2; s = max(bot - top, ri - le) * 1.35
            x0, y0 = int(max(0, min(1920 - s, cx - s / 2))), int(max(0, min(1080 - s, cy - s / 2)))
            ims.append(grab(os.path.join(rd, f), t, (x0, y0, int(s), int(s)))); labs.append('%s %.2f s' % (name.split('_')[0], t))
        for p in sys.argv[4:]:
            ims.append(Image.open(p).convert('RGB')); labs.append('default launch ' + os.path.basename(p))
        tile(ims, 5, labs, out)


if __name__ == '__main__':
    main()
