#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Facade clearance / occlusion check (critic round 07) on a telemetry CSV of a RENDERED run, over time windows:
#  - wall_frac: share of the frame covered by non-hero surfaces closer than 6 m to the camera (full-scene depth capture,
#    480x270, same camera) — target <= 0.30 in every frame
#  - hero_occl: share of the hero's pixels with scene geometry > 0.3 m in front of the hero surface — target 0 (never occluded)
#  - hero / camera horizontal distance to the nearest building box of the layout (trav_canyon_layout.json) spanning their height
# usage: facade_check.py <telemetry.csv> <label> <t0:t1> [<t0:t1> ...]
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
B = [b for b in json.load(open(os.path.join(HERE, "trav_canyon_layout.json")))["boxes"] if b["label"] != "Ground"]
def dist(x, y, z):
    best = 1e9
    for b in B:
        if not (b["min"][2] - 0.5 <= z <= b["max"][2] + 0.5):
            continue
        dx = max(b["min"][0] - x, 0, x - b["max"][0]); dy = max(b["min"][1] - y, 0, y - b["max"][1])
        best = min(best, (dx * dx + dy * dy) ** 0.5)
    return best
rows = list(csv.DictReader(open(sys.argv[1])))
for i in range(len(rows) - 1):  # capture columns are read at the start of the next frame
    for k in ("wall_frac", "hero_occl", "px_top", "px_bottom"):
        if k in rows[i + 1]:
            rows[i][k] = rows[i + 1][k]
rows = rows[:-1]
lab = sys.argv[2]
ok = True
for w in sys.argv[3:]:
    t0, t1 = map(float, w.split(":"))
    xs = [r for r in rows if t0 <= float(r["t"]) <= t1]
    if not xs:
        continue
    wf = [(float(r.get("wall_frac", -1)), r["t"]) for r in xs]
    ho = [(float(r.get("hero_occl", -1)), r["t"]) for r in xs]
    hd = min(dist(float(r["x_m"]), float(r["y_m"]), float(r["z_m"])) for r in xs)
    cd = min(dist(float(r["cam_x"]), float(r["cam_y"]), float(r["cam_z"])) for r in xs)
    if max(v for v, _ in wf) < 0:
        print(f"{lab} {t0:.1f}-{t1:.1f} s: no capture data (headless run); hero-facade min {hd:.2f} m, camera-facade min {cd:.2f} m")
        continue
    mw = max(wf); mo = max(ho)
    occl_frames = sum(1 for v, _ in ho if v > 0.02)
    res = mw[0] <= 0.30 and occl_frames == 0
    ok &= res
    print(f"{lab} {t0:.1f}-{t1:.1f} s ({len(xs)} frames): near-wall share max {mw[0]:.3f} at {float(mw[1]):.2f} s (target <= 0.30); "
          f"hero occluded (> 2 % of his pixels) in {occl_frames} frames, max {mo[0]:.3f}; hero-facade min {hd:.2f} m, "
          f"camera-facade min {cd:.2f} m  {'PASS' if res else 'FAIL'}")
print("FACADE CHECK:", "PASS" if ok else "FAIL")
