#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# TRAVERSAL-SPEC (director, 2026-09-29) camera / framing lines, engine side, on the telemetry of a RENDERED capture:
#   T8  hero bbox height / frame height: median 0.15-0.23, p10 >= 0.09, p90 <= 0.38, never < 0.05 while swinging (pixel mask)
#   T9  hero centre x: p5-p95 inside 0.44-0.56 (pixel mask)
#   T10 hero centre y: p5-p95 spread >= 0.20, range 0.20-0.70
#   T11 camera pitch: median 4-12 deg down, p95 15-30 down, p5 between 10 up and 3 down (rendered camera, pcm_pitch)
#   T12 camera yaw off the avenue axis (this map: east-west, +/-X): median 2-10, p90 10-25 deg
#   T13 |roll| median <= 1.5, p90 <= 10, max <= 20 deg outside dives
#   T14 horizontal FOV 100-110 deg (pcm_fov, Unreal's horizontal FOV)
#   T16 hero in frame >= 94 % of samples;  T19 hero never occluded (hero_occl), camera never inside geometry
#   + arc low points (height over the floor) of consecutive swings (director brief: they vary between swings)
# Window: the swing chain = from the first web attach to the end of the recording (or [t0, t1] given).
# usage: spec_cam_check.py <telemetry.csv> <label> [t0 t1]
import csv, math, sys
rows = list(csv.DictReader(open(sys.argv[1])))
for i in range(len(rows) - 1):  # capture / camera-manager columns are read at the start of the next frame
    for k in ("px_top", "px_bottom", "px_left", "px_right", "hero_occl", "pcm_pitch", "pcm_yaw", "pcm_fov", "pcm_roll"):
        if k in rows[i + 1]:
            rows[i][k] = rows[i + 1][k]
rows = rows[:-1]
lab = sys.argv[2]
if len(sys.argv) > 4:
    t0, t1 = float(sys.argv[3]), float(sys.argv[4])
else:
    t0 = next((float(r["t"]) for r in rows if r["mode"] == "swing"), 0.0); t1 = float(rows[-1]["t"])
W = [r for r in rows if t0 <= float(r["t"]) <= t1]
def pct(v, p):
    v = sorted(v)
    if not v: return float("nan")
    k = (len(v) - 1) * p; f = math.floor(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)
res = []
def line(name, ok, text):
    res.append(ok); print(f"  {name:4s} {'PASS' if ok else 'FAIL'}  {text}")
print(f"{lab}: {t0:.2f}-{t1:.2f} s ({len(W)} frames)")
px = [r for r in W if float(r["px_top"]) >= 0]
hh = [(float(r["px_bottom"]) - float(r["px_top"])) / 1080.0 for r in px]
sw_h = [(float(r["px_bottom"]) - float(r["px_top"])) / 1080.0 for r in px if r["mode"] == "swing"]
line("T8", 0.15 <= pct(hh, .5) <= 0.23 and pct(hh, .1) >= 0.09 and pct(hh, .9) <= 0.38 and (min(sw_h) if sw_h else 1) >= 0.05,
     f"hero height / frame: p10 {pct(hh,.1):.3f} p50 {pct(hh,.5):.3f} p90 {pct(hh,.9):.3f}, min while swinging {min(sw_h) if sw_h else float('nan'):.3f}")
cx = [0.5 * (float(r["px_left"]) + float(r["px_right"])) / 1920.0 for r in px]
line("T9", pct(cx, .05) >= 0.44 and pct(cx, .95) <= 0.56, f"hero centre x: p5 {pct(cx,.05):.3f} p95 {pct(cx,.95):.3f} (inside 0.44-0.56)")
cy = [0.5 * (float(r["px_top"]) + float(r["px_bottom"])) / 1080.0 for r in px]
line("T10", pct(cy, .95) - pct(cy, .05) >= 0.20 and pct(cy, .05) >= 0.20 - 1e-9 and pct(cy, .95) <= 0.70,
     f"hero centre y: p5 {pct(cy,.05):.3f} p95 {pct(cy,.95):.3f} spread {pct(cy,.95)-pct(cy,.05):.3f}")
pd = [-float(r["pcm_pitch"]) for r in W]
line("T11", 4 <= pct(pd, .5) <= 12 and 15 <= pct(pd, .95) <= 30 and -10 <= pct(pd, .05) <= 3,
     f"pitch down: p5 {pct(pd,.05):+.1f} p50 {pct(pd,.5):+.1f} p95 {pct(pd,.95):+.1f} deg")
import os
AX = float(os.environ.get("AVENUE_YAW", "0"))  # round 10: Manhattan avenue runs north-south (+/-Y): AVENUE_YAW=90
yo = [abs((float(r["pcm_yaw"]) - AX + 90) % 180 - 90) for r in W]  # off the avenue axis
line("T12", 2 <= pct(yo, .5) <= 10 and 10 <= pct(yo, .9) <= 25, f"|yaw| off the avenue axis: p50 {pct(yo,.5):.1f} p90 {pct(yo,.9):.1f} deg")
ro = [abs(float(r["pcm_roll"])) for r in W if r.get("pcm_roll") not in (None, "") and r["sub"] != "dive"]
if ro:
    line("T13", pct(ro, .5) <= 1.5 and pct(ro, .9) <= 10 and max(ro) <= 20, f"|roll|: p50 {pct(ro,.5):.1f} p90 {pct(ro,.9):.1f} max {max(ro):.1f} deg")
hf = [float(r["pcm_fov"]) for r in W if r["mode"] == "swing"]
line("T14", 100 <= pct(hf, .5) <= 110, f"horizontal FOV while swinging: p10 {pct(hf,.1):.1f} p50 {pct(hf,.5):.1f} p90 {pct(hf,.9):.1f} deg")
line("T16", len(px) >= 0.94 * len(W), f"hero pixels present {len(px)}/{len(W)} = {100*len(px)/max(1,len(W)):.1f} %")
occ = sum(1 for r in W if float(r.get("hero_occl", -1)) > 0.02); geo = sum(1 for r in W if r["cam_in_geometry"] == "1")
line("T19", occ == 0 and geo == 0, f"hero occluded (> 2 % of his pixels) in {occ} frames; camera inside geometry in {geo} frames")
h = lambda r: float(r["height_above_floor_m"]) if float(r["height_above_floor_m"]) < 900 else 0.0
lows, cur = [], None
for r in rows:
    if r["mode"] == "swing": cur = min(cur, h(r)) if cur is not None else h(r)
    elif cur is not None: lows.append(cur); cur = None
d = [abs(a - b) for a, b in zip(lows, lows[1:])]
print(f"  arc low points (m over the floor): {', '.join(f'{v:.1f}' for v in lows)}; consecutive differences min {min(d) if d else float('nan'):.1f} m")
print(f"{lab}: {sum(res)}/{len(res)} camera lines pass")
