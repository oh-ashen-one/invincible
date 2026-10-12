#!/usr/bin/env python3
"""r04 criterion (c): no flat untextured quad wider than 100 px in any t4_lawn_sprint frame at 4 fps.
Frames are taken from the encoded movie at 4 fps (ffmpeg), 1920 x 1080. A pixel is 'flat' when its 7 x 7 luma std < FLAT_SD (default 0.9: the movie's H.264 noise floor is ~0.5; textured gravel / lawn sit at 1.5-6) and its luma is 15..245;
flat pixels are labelled (8-connected, 5 px closing); components that touch the top 4 % of the frame are sky and are set aside; every other component whose bounding box is wider than 100 px is reported
(frame time, bbox, mean colour, area, fill ratio). Exit code 0; the verdict is in the JSON (`pass`: none reported).
usage: flatquad_check.py <movie.mp4> <out.json> [flat_sd]"""
import sys, os, json, subprocess, tempfile, glob
import numpy as np
from PIL import Image
from scipy import ndimage
mp4, out = sys.argv[1], sys.argv[2]; FLAT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.9
tmp = tempfile.mkdtemp(prefix='flatq_', dir='/Users/midir/sm2-n1/_scratch/terrain')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', mp4, '-vf', 'fps=4', '-q:v', '2', os.path.join(tmp, 'f%04d.jpg')], check=True)
hits, nfr = [], 0
for i, f in enumerate(sorted(glob.glob(os.path.join(tmp, 'f*.jpg')))):
    t = i * 0.25; nfr += 1
    a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32); Y = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    m1 = ndimage.uniform_filter(Y, 7); m2 = ndimage.uniform_filter(Y * Y, 7); sd = np.sqrt(np.maximum(m2 - m1 * m1, 0))
    flat = (sd < FLAT) & (Y > 15) & (Y < 245)
    flat = ndimage.binary_closing(flat, structure=np.ones((5, 5)))
    lab, n = ndimage.label(flat, structure=np.ones((3, 3)))
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None: continue
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        if w <= 100 or h < 25: continue                         # 'a quad wider than 100 px': at least 25 px tall (thin slivers are path edges / horizons)
        if sl[0].start < 0.04 * Y.shape[0] or sl[0].stop < 0.4 * Y.shape[0]: continue          # sky / clouds (touching the top edge, or wholly above 40 % of the frame height)
        msk = lab[sl] == k; area = int(msk.sum())
        if area < 0.55 * w * h: continue                       # gradients / irregular shapes
        hits.append({'t_s': round(t, 2), 'bbox_xywh': [int(sl[1].start), int(sl[0].start), int(w), int(h)], 'area_px': area, 'fill': round(area / float(w * h), 2), 'mean_rgb': [round(float(v), 1) for v in a[sl][msk].mean(0)]})
for f in glob.glob(os.path.join(tmp, '*.jpg')): os.remove(f)
os.rmdir(tmp)
res = {'movie': os.path.basename(mp4), 'frames_at_4fps': nfr, 'flat_sd_threshold': FLAT, 'pass': not hits, 'components_wider_than_100px': len(hits), 'hits': hits[:60]}
json.dump(res, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'hits'})); [print(h) for h in hits[:12]]
