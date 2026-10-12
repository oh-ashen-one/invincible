#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Camera framing check (critic round 02) on a telemetry CSV (one row per rendered frame):
#   hero screen bbox height fraction (<= 0.30), hero kept in frame, camera-hero distance (>= 2 m), camera never inside
#   geometry, and per swing the hero's screen centre-Y travel (>= 0.20 of frame height).
# usage: cam_check.py <telemetry.csv> [<label>]
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
f = lambda k: [float(r[k]) for r in rows]
bh, bw, cy, dist = f("hero_bbox_h"), f("hero_bbox_w"), f("hero_cy"), f("cam_hero_dist_m")
inf = [int(r["hero_in_frame"]) for r in rows]
geo = [int(r["cam_in_geometry"]) for r in rows]
n = len(rows)
bad_fill = [float(r["t"]) for r, v in zip(rows, bh) if v > 0.30]
bad_frame = [float(r["t"]) for r, v in zip(rows, inf) if not v]
bad_dist = [float(r["t"]) for r, v in zip(rows, dist) if v < 2.0]
bad_geo = [float(r["t"]) for r, v in zip(rows, geo) if v]
def spans(ts):
    if not ts: return "none"
    out, a, b = [], ts[0], ts[0]
    for t in ts[1:]:
        if t - b > 0.02: out.append((a, b)); a = t
        b = t
    out.append((a, b))
    return ", ".join(f"{x:.2f}-{y:.2f}s" if y > x else f"{x:.2f}s" for x, y in out)
print(f"{sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]}: {n} frames")
print(f"  hero bbox height fraction  min {min(bh):.3f}  max {max(bh):.3f}   frames > 0.30: {len(bad_fill)} ({spans(bad_fill)})")
print(f"  hero bbox width fraction   min {min(bw):.3f}  max {max(bw):.3f}")
valid_cy = [c for c in cy if c >= 0]
print(f"  hero centre Y (0 top..1)   min {min(valid_cy):.3f}  max {max(valid_cy):.3f}")
print(f"  hero fully in frame        {sum(inf)}/{n} frames; out: {spans(bad_frame)}")
print(f"  camera-hero distance m     min {min(dist):.2f}  max {max(dist):.2f}   frames < 2 m: {len(bad_dist)} ({spans(bad_dist)})")
pd = [-float(r["cam_pitch_deg"]) for r in rows]
ha = [float(r["cam_z"]) - float(r["z_m"]) for r in rows]
sw_rows = [i for i, r in enumerate(rows) if r["mode"] in ("swing", "air")]
print(f"  camera pitch (deg down)    min {min(pd):.1f}  max {max(pd):.1f}   swing/air frames: {min(pd[i] for i in sw_rows) if sw_rows else 0:.1f}..{max(pd[i] for i in sw_rows) if sw_rows else 0:.1f}")
print(f"  camera height over hero m  min {min(ha):.2f}  max {max(ha):.2f}")
print(f"  camera in geometry         {sum(geo)} frames ({spans(bad_geo)})")
# per swing: hero centre-Y range over the swing
sw, cur = [], None
for r in rows:
    if r["mode"] == "swing":
        if cur is None: cur = [float(r["t"]), []]
        cur[1].append(float(r["hero_cy"]))
    elif cur is not None:
        sw.append(cur); cur = None
if cur: sw.append(cur)
for i, (t0, c) in enumerate(sw):
    c = [v for v in c if v >= 0]
    rng = (max(c) - min(c)) if c else 0
    print(f"  swing {i+1} t0 {t0:5.2f}s  hero centre-Y {min(c):.2f}..{max(c):.2f}  travel {rng*100:4.1f}% {'ok' if rng >= 0.2 else '<20%'}")
