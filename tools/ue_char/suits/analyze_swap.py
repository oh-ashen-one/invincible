#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 11: swap latency of the in-game suit change measured on the pixels of a fixed-step (-movie, 60 fps) run, next to the engine's own log.

  python3 tools/ue_char/suits/analyze_swap.py FRAMES_DIR SUIT_LOG.txt OUT.json [--fps 60] [--roi x0,y0,x1,y1]

FRAMES_DIR holds MovieFrameNNNNN.png.  For every frame the colour histogram (8x8x8 bins) of the HERO's pixels is computed at 1/4 size (the centre 40 pct of the frame minus the area-scaled
histogram of the two side strips, which only show sky / floor); a SWAP is a one-frame step of that histogram (L1 distance > max(0.15, 5 x the median step)).  Each logged
'WH_SUIT injected T press t=<s> frame=<n>' is matched with the first swap within [n-1, n+40] frames; the difference is the key-to-pixel latency (x 1000/60 ms).  Also parsed from the log:
the engine's own apply_ms and 'swap_done wall_ms / frames / textures_resident'.
"""
import sys, os, re, json, glob
import numpy as np
import cv2


def hero_hist(path):
    """Colour histogram (8x8x8 bins) of the hero's pixels: the central 40 % of the frame minus the (area-scaled) histogram of the two side strips, which show only sky / floor."""
    im = cv2.imread(path)
    h, w = im.shape[:2]
    g = cv2.resize(im, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    H, W = g.shape[:2]
    q = (g // 32).astype(np.int32)
    code = q[..., 0] * 64 + q[..., 1] * 8 + q[..., 2]
    mid = code[:, int(W * .3):int(W * .7)]
    side = np.concatenate([code[:, :int(W * .15)], code[:, int(W * .85):]], axis=1)
    hm = np.bincount(mid.ravel(), minlength=512).astype(np.float32)
    hs = np.bincount(side.ravel(), minlength=512).astype(np.float32) * (mid.size / side.size)
    hh = np.clip(hm - hs, 0, None)
    return hh / max(hh.sum(), 1.0)


def main():
    fr_dir, log_p, out = sys.argv[1:4]
    a = sys.argv
    fps = float(a[a.index('--fps') + 1]) if '--fps' in a else 60.0
    files = sorted(glob.glob(os.path.join(fr_dir, 'MovieFrame*.png')))
    hs = np.array([hero_hist(f) for f in files])
    step = np.abs(np.diff(hs, axis=0)).sum(axis=1)               # step[i] = change of the hero's colour distribution from frame i to i+1 (0 = identical, 2 = disjoint)
    base = float(np.median(step[10:])) if len(step) > 20 else 0.04
    thr = max(0.15, 5 * base)
    swaps = [int(i) + 1 for i in np.nonzero(step > thr)[0] if int(i) + 1 > 10]   # the first frames are the director's camera cut
    merged = []
    for s_ in swaps:
        if merged and s_ - merged[-1] <= 10: continue
        merged.append(s_)
    log = open(log_p).read() if os.path.exists(log_p) else ''
    presses = [float(m.group(1)) for m in re.finditer(r'injected T press t=([0-9.]+)', log)]
    press_frames = [int(m.group(1)) for m in re.finditer(r'injected T press t=[0-9.]+ frame=(\d+)', log)]
    sets = [dict(i=int(m.group(1)), id=m.group(3), why=m.group(4), t=float(m.group(5)), frame=int(m.group(6)), apply_ms=float(m.group(7)))
            for m in re.finditer(r'WH_SUIT set (\d+)/(\d+) (\S+) \(([^)]*)\) changed=\d t=([0-9.]+) frame=(\d+) apply_ms=([0-9.]+)', log)]
    done = [dict(i=int(m.group(1)), id=m.group(2), wall_ms=float(m.group(3)), frames=int(m.group(4)), res=m.group(5))
            for m in re.finditer(r'WH_SUIT swap_done (\d+) (\S+) wall_ms=([0-9.]+) frames=(\d+) textures_resident=(\d+/\d+)', log)]
    # movie file index == engine frame number (the dump starts with engine frame 0); the logged press frame is the frame the T key was injected in
    lat = []
    for pf in press_frames:
        near = [s_ for s_ in merged if pf - 1 <= s_ <= pf + 40]
        lat.append(near[0] - pf if near else None)
    matched = {pf + l for pf, l in zip(press_frames, lat) if l is not None}
    other = [s_ for s_ in merged if s_ not in matched]           # not a swap of a pressed key: the director's camera cut to the next pawn shot at game time 10 s
    res = dict(other_steps=other, matched=len(matched), method='colour histogram of the hero pixels (centre 40 pct minus side strips), step > %.3f (median step %.3f)' % (thr, base), frames=len(files), swap_frames=merged,
               press_times=presses, press_frames=press_frames, hist_steps=[round(float(step[s_ - 1]), 3) for s_ in merged], latency_frames=lat,
               latency_ms=[None if l is None else round(l * 1000 / fps, 1) for l in lat], engine_sets=sets, engine_swap_done=done,
               max_latency_s=None if any(l is None for l in lat) or not lat else round(max(lat) / fps, 3), swaps_found=len(merged), presses=len(presses))
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('method', 'frames', 'swap_frames', 'press_frames', 'hist_steps', 'other_steps', 'latency_frames', 'latency_ms', 'max_latency_s', 'matched', 'presses')}))
    for d in done: print('engine:', d)


if __name__ == '__main__':
    main()
