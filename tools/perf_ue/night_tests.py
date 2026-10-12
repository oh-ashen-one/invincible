#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P4 night-look tests (numbers only, no judgement). Luma Y = 0.2126 R + 0.7152 G + 0.0722 B of the 8-bit sRGB code values (0..255).
  still  <png>                       mean luma, share of pixels < 10/255, percentiles
  pools  <png>                       light pools in the bottom third: maxima of the blurred luma >= PEAK, merged when the straight path between two maxima
                                     never drops to <= VALLEY (peak >= 120, valley <= 40 by default): count, peaks, path minima
  hero   <frames_dir> <telemetry.csv> [--skip N]
                                     mean luma inside the hero's pixel bounding box (telemetry px_left/right/top/bottom, from the P3 hero-only depth capture,
                                     1080p coordinates) for every frame of a swing clip; frames with no hero pixels are counted separately
  all    --still night_S1.png [--clip-frames dir --csv telemetry.csv --skip N] [--json out.json]
"""
import sys, os, json, glob, csv, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

def luma(img):
    a = np.asarray(img.convert('RGB'), dtype=np.float32)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

def still_stats(path):
    y = luma(Image.open(path))
    return {'file': os.path.basename(path), 'size': [y.shape[1], y.shape[0]], 'mean_luma': round(float(y.mean()), 2), 'pct_below_10': round(100.0 * float((y < 10).mean()), 2),
            'pct_below_5': round(100.0 * float((y < 5).mean()), 2), 'p1': round(float(np.percentile(y, 1)), 1), 'p50': round(float(np.percentile(y, 50)), 1),
            'p99': round(float(np.percentile(y, 99)), 1), 'pct_at_or_above_250': round(100.0 * float((y >= 250).mean()), 3)}

def pool_stats(path, peak=120.0, valley=40.0, sigma=8.0, nms=40.0, third='bottom'):
    y = luma(Image.open(path)); H, W = y.shape; s = W / 1920.0
    y0 = int(H * 2 / 3) if third == 'bottom' else 0
    sub = y[y0:, :]
    sm = ndi.gaussian_filter(sub, sigma * s)
    mx = ndi.maximum_filter(sm, size=int(2 * nms * s + 1))
    pk = np.argwhere((sm == mx) & (sm >= peak))
    pts = [(int(r), int(c), float(sm[r, c])) for r, c in pk]
    n = len(pts); par = list(range(n))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            (r0, c0, _), (r1, c1, _) = pts[i], pts[j]
            k = int(max(abs(r1 - r0), abs(c1 - c0)) / 2) + 2
            rr = np.linspace(r0, r1, k).round().astype(int); cc = np.linspace(c0, c1, k).round().astype(int)
            vmin = float(sm[rr, cc].min())
            pairs.append((i, j, round(vmin, 1)))
            if vmin > valley: par[find(i)] = find(j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(i)
    return {'file': os.path.basename(path), 'region': 'rows %d..%d of %d' % (y0, H, H), 'peak_thr': peak, 'valley_thr': valley, 'blur_sigma_px_at_1080p': sigma,
            'maxima': [{'x': round(c / s), 'y': round((r + y0) / s), 'v': round(v)} for r, c, v in pts], 'path_minima': pairs, 'distinct_pools': len(groups),
            'pool_peaks': sorted([round(max(pts[i][2] for i in g)) for g in groups.values()], reverse=True)}

def hero_stats(frames_dir, csv_path, skip=0, thr=40.0):
    rows = list(csv.DictReader(open(csv_path)))
    files = sorted(glob.glob(os.path.join(frames_dir, '*.png')))[skip:]
    n = min(len(files), len(rows) - 1)
    means, missing, low = [], [], []
    for k in range(n):
        r = rows[k + 1]                       # px_* is sampled at the start of the next frame (row i+1 describes frame i)
        try: t, b, l, rt = (float(r[c]) for c in ('px_top', 'px_bottom', 'px_left', 'px_right'))
        except (KeyError, ValueError): missing.append(k); continue
        if t < 0 or rt <= l or b <= t: missing.append(k); continue
        img = Image.open(files[k]); W, H = img.size; s = W / 1920.0
        y = luma(img)
        x0, x1, y0, y1 = int(max(0, l * s)), int(min(W, rt * s)), int(max(0, t * s)), int(min(H, b * s))
        if x1 <= x0 or y1 <= y0: missing.append(k); continue
        box = y[y0:y1, x0:x1]
        m = float(box.mean()); means.append((k, m, float(np.percentile(box, 10)), float(np.percentile(box, 90))))
        if m < thr: low.append(k)
    a = np.array([m for _, m, _, _ in means]) if means else np.zeros(1)
    return {'frames_measured': len(means), 'frames_without_hero_pixels': len(missing), 'bbox_mean_luma_min': round(float(a.min()), 1), 'bbox_mean_luma_p5': round(float(np.percentile(a, 5)), 1),
            'bbox_mean_luma_mean': round(float(a.mean()), 1), 'bbox_mean_luma_max': round(float(a.max()), 1), 'threshold': thr, 'frames_below_threshold': len(low),
            'first_frames_below': low[:12], 'p10_of_bbox_mean': round(float(np.mean([p for _, _, p, _ in means])), 1) if means else None,
            'p90_of_bbox_mean': round(float(np.mean([p for _, _, _, p in means])), 1) if means else None}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('a', nargs='?'); ap.add_argument('b', nargs='?'); ap.add_argument('--skip', type=int, default=0)
    ap.add_argument('--still'); ap.add_argument('--clip-frames'); ap.add_argument('--csv'); ap.add_argument('--json')
    a = ap.parse_args(); out = {}
    if a.cmd == 'still': out = still_stats(a.a)
    elif a.cmd == 'pools': out = pool_stats(a.a)
    elif a.cmd == 'hero': out = hero_stats(a.a, a.b, a.skip)
    elif a.cmd == 'all':
        out['night_S1_still'] = still_stats(a.still); out['night_S1_pools'] = pool_stats(a.still)
        if a.clip_frames: out['swing_night_hero'] = hero_stats(a.clip_frames, a.csv, a.skip)
    print(json.dumps(out, indent=1))
    if a.json: json.dump(out, open(a.json, 'w'), indent=1)

if __name__ == '__main__':
    main()
