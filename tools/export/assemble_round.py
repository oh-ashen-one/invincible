#!/usr/bin/env python3
"""Assemble docs/night1/city/round-NN from a capture_round.sh output dir: JPG captures, perf.json, README (neutral:
camera parameters + frame times + GPU utilization only). usage: assemble_round.py <raw_dir> <round_dir> <round_no>"""
import json, os, sys
from PIL import Image
RAW, R, N = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(R, exist_ok=True)
shots = json.load(open(os.path.join(os.path.dirname(__file__), '../../unreal/WebHomage/Scripts/city_shots.json')))
rows, perf = [], {}
for s in shots:
    for res in ('1920x1080', '3840x2160'):
        import glob   # (r11) settle pair: shots at t = 24 and 28 s are numbered _00_t024.0 / _01_t028.0; the t = 28 s one is the round frame (the older single-shot runs had _00_t028.0)
        pngs = sorted(glob.glob(f'{RAW}/{s["id"]}_{res}_01_t*.png')) or sorted(glob.glob(f'{RAW}/{s["id"]}_{res}_00_t028.0.png'))
        if pngs: Image.open(pngs[-1]).convert('RGB').save(f'{R}/{s["id"]}_{res}.jpg', quality=88)
        p = json.load(open(f'{RAW}/{s["id"]}_{res}_perf.json')) if os.path.exists(f'{RAW}/{s["id"]}_{res}_perf.json') else {}
        g = json.load(open(f'{RAW}/{s["id"]}_{res}_gpu.json')) if os.path.exists(f'{RAW}/{s["id"]}_{res}_gpu.json') else {}
        p['gpu_util_before_pct'] = g.get('gpu_util_before_pct'); perf[f'{s["id"]}_{res}'] = p; rows.append((s['id'], res, p))
json.dump(perf, open(f'{R}/perf.json', 'w'), indent=1)
L = [f'# P1 City round {N} — captures and camera parameters', '', '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
     'Running game: `Scripts/run_game.sh` (`-game`, offscreen, map `/Game/Tests/City/City_View_<id>`, auto-activated CameraActor), screenshots at t = 34 s and t = 38 s (settle pair; the t = 38 s frame is the round frame).',
     'Frame times: game seconds 26-38 of a capture run under the shared GPU lock (`gpu_slot.sh capture`: frame cap 20 fps at 1080p / 8 fps at 3840 px, background priority, other agents render at the same time), NOT a performance measurement (a perf run needs the exclusive lock on an attended Mac); the 1080p frames use the automatic screen percentage (internal 1399x787), the 4K frames r.ScreenPercentage 100 (internal 3840x2160). GPU utilization read with ioreg before each run',
     '(GPU shared with other sessions; the P1 editor was closed during the runs). Positions in browser metres (x east, y up, z south); UE = (100x, 100z, 100y) cm.', '',
     '| id | camera pos | target | fov | sun (pitch, yaw) |', '|---|---|---|---|---|']
L += [f"| {s['id']} | {s['pos']} | {s['target']} | {s.get('fov', 70)} | {s.get('sun')} |" for s in shots]
L += ['', '| id | output | internal | avg ms | p95 ms | GPU ms | GPU util before |', '|---|---|---|---|---|---|---|']
L += [f"| {i} | {res} | {p.get('internal_w')}x{p.get('internal_h')} | {p.get('avg_ms')} | {p.get('p95_ms')} | {p.get('gpu_avg_ms')} | {p.get('gpu_util_before_pct')} % |" for i, res, p in rows]
ws, w3 = f'{R}/window_stats.json', f'{R}/window_stats_r03.json'
if os.path.exists(ws):
    cur = json.load(open(ws)); old = {r['region']: r for r in json.load(open(w3))} if os.path.exists(w3) else {}
    L += ['', '## Window brightness test (critic r03 test)', '',
          'Window pixels = pixels of glass panes, taken from a second capture of the same view with the facade material in debug mode 3',
          '(MPC_City.DebugMode = 3: red = glass, everything else black). In each 4K frame the 400 x 400 px crop with the most window pixels inside',
          'the listed region was measured (chosen from the mask only). Luminance = Rec.709 luma of the 8-bit sRGB frame, 0..1.', '',
          '| region | crop (x, y) | window px | > 80 % lum. | > 60 % lum. | median | mean | round 03 > 80 % | round 03 median |', '|---|---|---|---|---|---|---|---|---|']
    for r in cur:
        o = old.get(r['region'], {})
        L.append(f"| {r['region']} | {r['crop_xywh'][0]}, {r['crop_xywh'][1]} | {r['window_pixels']} | {r['above_80pct_luminance_pct']} % | {r['above_60pct_luminance_pct']} % | "
                 f"{r['median_luminance']} | {r['mean_luminance']} | {o.get('above_80pct_luminance_pct', '-')} % | {o.get('median_luminance', '-')} |")
    L += ['', 'Crops (`window_crops/`): `*_crop.jpg` = the measured crop, `*_over80.jpg` = window pixels above 80 % luminance in magenta.']
open(f'{R}/README.md', 'w').write('\n'.join(L) + '\n')
