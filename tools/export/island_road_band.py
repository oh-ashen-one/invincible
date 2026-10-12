#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""(island r03) critic test "road band" on a route frame: lane-paint share and luminance spread of the street in the lower frame.

    python3 tools/export/island_road_band.py <frame.jpg|png> [...] [--json out.json]

Two bands (fractions of the frame: rows y0-y1, columns x0-x1), calibrated on the round-02 r2 frames the critic scored (critic: t=12 s 1.21 %
paint / std 39; t=28 s bare slab 0.00 % / std 13-17):
  paint band  rows 0.40-1.0, all columns          lane paint pixel = white paint (Rec.709 luma >= 200, HSV S <= 0.12) or yellow paint
                                                  (hue 35-65 deg, S >= 0.50, V >= 0.60)        -> r02 t=12 1.21 %, t=28 0.06 %
  std band    rows 0.60-1.0, columns 0.25-0.75    luminance std of the road under / ahead of the hero  -> r02 t=12 39.6, t=28 18.0
Targets (round-02 critic): paint >= 1 %, luminance std >= 35.
"""
import sys, json, colorsys
from PIL import Image

PAINT_BAND, STD_BAND = (0.40, 1.0, 0.0, 1.0), (0.60, 1.0, 0.25, 0.75)

def _crop(im, band):
    W, H = im.size
    return im.crop((int(band[2] * W), int(band[0] * H), int(band[3] * W), int(band[1] * H)))

def band_stats(path, paint_band=PAINT_BAND, std_band=STD_BAND):
    im = Image.open(path).convert('RGB')
    n = paint = 0
    for r, g, b in _crop(im, paint_band).getdata():
        Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        h, sat, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if (Y >= 200 and sat <= 0.12) or (35 / 360 <= h <= 65 / 360 and sat >= 0.50 and v >= 0.60): paint += 1
        n += 1
    k = 0; s = s2 = 0.0
    for r, g, b in _crop(im, std_band).getdata():
        Y = 0.2126 * r + 0.7152 * g + 0.0722 * b; k += 1; s += Y; s2 += Y * Y
    m = s / k; sd = max(0.0, s2 / k - m * m) ** 0.5
    return {'frame': path, 'size': list(im.size), 'paint_band': paint_band, 'std_band': std_band, 'lane_paint_pct': round(100.0 * paint / n, 2),
            'luma_mean': round(m, 1), 'luma_std': round(sd, 1), 'pass_paint_ge_1pct': paint / n >= 0.01, 'pass_std_ge_35': sd >= 35}

if __name__ == '__main__':
    a = sys.argv[1:]; out = None
    if '--json' in a: i = a.index('--json'); out = a[i + 1]; del a[i:i + 2]
    res = [band_stats(p) for p in a]
    for r in res: print('%-70s paint %5.2f %%  luma std %5.1f  mean %5.1f' % (r['frame'][-70:], r['lane_paint_pct'], r['luma_std'], r['luma_mean']))
    if out: json.dump(res, open(out, 'w'), indent=1)
