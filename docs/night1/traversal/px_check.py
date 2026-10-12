#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Pixel-based framing check (critic round 04). Telemetry columns px_top/px_bottom/px_left/px_right come from a depth scene
# capture that renders ONLY the hero meshes from the view camera (480x270, scaled to 1920x1080); pcm_* are the engine's
# rendered camera. Both are sampled at the start of the next frame, so row i+1 describes frame i (aligned here).
#  - hero pixel height at 1080p per frame; share of frames >= 160 px
#  - anchor on screen at each web attach (projected through the rendered camera), and the first on-screen time within 0.4 s
# usage: px_check.py <telemetry.csv> [label] [t_max]
import csv, math, sys
rows = list(csv.DictReader(open(sys.argv[1])))
lab = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
tmax = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
keys = ("px_top", "px_bottom", "px_left", "px_right", "pcm_x", "pcm_y", "pcm_z", "pcm_pitch", "pcm_yaw", "pcm_fov")
for i in range(len(rows) - 1):
    for k in keys:
        rows[i][k] = rows[i + 1][k]
rows = [r for r in rows[:-1] if float(r["t"]) <= tmax]
hs = []
for r in rows:
    top, bot = float(r["px_top"]), float(r["px_bottom"])
    hs.append(bot - top if top >= 0 else 0.0)
ok = sum(1 for h in hs if h >= 160)
print(f"{lab}: {len(rows)} frames (t <= {min(tmax, float(rows[-1]['t'])):.2f} s)")
print(f"  hero pixel height (1080p): min {min(hs):.0f}  median {sorted(hs)[len(hs)//2]:.0f}  max {max(hs):.0f}; >= 160 px in {ok}/{len(rows)} frames ({100*ok/len(rows):.1f}%)")
mis = [float(r["t"]) for r, h in zip(rows, hs) if h == 0]
print(f"  frames with no hero pixels: {len(mis)}")
def onscreen(r, P):
    cx, cy, cz = float(r["pcm_x"]), float(r["pcm_y"]), float(r["pcm_z"])
    p, y = math.radians(float(r["pcm_pitch"])), math.radians(float(r["pcm_yaw"]))
    f = (math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p))
    rt = (-math.sin(y), math.cos(y), 0.0)
    up = (-math.sin(p) * math.cos(y), -math.sin(p) * math.sin(y), math.cos(p))
    d = (P[0] - cx, P[1] - cy, P[2] - cz)
    z = sum(a * b for a, b in zip(d, f))
    if z <= 0.1: return False, 0, 0
    th = math.tan(math.radians(float(r["pcm_fov"])) / 2)
    sx = 0.5 + 0.5 * sum(a * b for a, b in zip(d, rt)) / (z * th)
    sy = 0.5 - 0.5 * sum(a * b for a, b in zip(d, up)) / (z * th / (16 / 9))
    return 0 <= sx <= 1 and 0 <= sy <= 1, sx, sy
prev = None
n_att = n_vis0 = n_vis = 0
for i, r in enumerate(rows):
    if r["mode"] == "swing" and prev != "swing":
        n_att += 1
        A = (float(r["anchor_x"]), float(r["anchor_y"]), float(r["anchor_z"]))
        t0 = float(r["t"])
        v0, sx, sy = onscreen(r, A)
        first = None
        for r2 in rows[i:i + 25]:
            if r2["mode"] != "swing": break
            v, _, _ = onscreen(r2, (float(r2["anchor_x"]), float(r2["anchor_y"]), float(r2["anchor_z"])))
            if v: first = float(r2["t"]) - t0; break
        n_vis0 += v0; n_vis += first is not None
        print(f"  attach {n_att} t={t0:5.2f}s anchor on screen at attach frame: {'yes' if v0 else 'no'} (x {sx:.2f}, y {sy:.2f}); first on screen after {first if first is not None else float('nan'):.2f} s")
    prev = r["mode"]
print(f"  anchors on screen: {n_vis0}/{n_att} at the attach frame, {n_vis}/{n_att} within 0.4 s")
