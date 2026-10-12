#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Wall-run check (critic round 05): on 6 fps samples of the wall-run (mode 'wall'),
#  - limb phases: distinct hand / foot arrangements up the wall. Phase of a sample = the order of the four limbs
#    (hand_L, hand_R, foot_L, foot_R) by height above the hips plus which foot / which hand leads (L or R);
#    a phase counts as distinct only when its limb-height vector differs by > DIST_M from every phase already counted
#  - head above hips: head bone higher than the hips bone (world up) in every sample
#  - steps: sign changes of (foot_L - foot_R) height over the whole wall-run (each change = one step), steps per second
#  - hero in frame: every rendered frame from the wall-run start to the end of the top-out landing has the hero pixel box
#    fully inside the frame (px_* columns, needs a real render; 0 = touches or leaves an edge)
#  - camera: pitch (deg, + = up), camera below the hero (m), camera-hero distance, over the wall-run
# usage: wall_check.py <telemetry.csv> [label]
import csv, sys, math
DIST_M = 0.12
rows = list(csv.DictReader(open(sys.argv[1])))
for i in range(len(rows) - 1):  # anim / pose / pixel columns are sampled at the start of the next frame
    for k in ("anim_node", "anim_clip", "anim_weight", "pose_sig", "head_hip_dz", "limb_z", "px_top", "px_bottom", "px_left", "px_right"):
        if k in rows[i + 1]:
            rows[i][k] = rows[i + 1][k]
rows = rows[:-1]
lab = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
wall = [r for r in rows if r["mode"] == "wall"]
if not wall:
    print(f"{lab}: no wall frames"); sys.exit(0)
t0, t1 = float(wall[0]["t"]), float(wall[-1]["t"])
samples = [r for r in wall if (round((float(r["t"]) - t0) * 60) % 10) == 0]
phases, head_bad = [], []
for r in samples:
    lz = [float(v) for v in r["limb_z"].split()]
    if all(math.dist(lz, p) > DIST_M for p in phases):
        phases.append(lz)
    if float(r["head_hip_dz"]) <= 0:
        head_bad.append(float(r["t"]))
d = [float(r["limb_z"].split()[2]) - float(r["limb_z"].split()[3]) for r in wall]
steps = sum(1 for a, b in zip(d, d[1:]) if a * b < 0 and abs(a - b) > 1e-4)
dur = t1 - t0
# top-out: first frames after the wall until the landing sub ends (mode back to ground / idle)
end = t1
after = [r for r in rows if float(r["t"]) > t1]
for r in after:
    end = float(r["t"])
    if r["mode"] == "ground" and r["sub"] not in ("landTopOut",):
        break
span = [r for r in rows if t0 <= float(r["t"]) <= end]
has_px = any(float(r.get("px_top", -1)) >= 0 for r in span)
out = [float(r["t"]) for r in span if not (float(r["px_top"]) > 0 and float(r["px_bottom"]) < 1080 and float(r["px_left"]) > 0 and float(r["px_right"]) < 1920)]
pitch = [float(r["cam_pitch_deg"]) for r in wall]
below = [float(r["z_m"]) - float(r["cam_z"]) for r in wall]
dist = [float(r["cam_hero_dist_m"]) for r in wall]
print(f"{lab}: wall-run {t0:.2f}-{t1:.2f} s ({dur:.2f} s, {len(samples)} samples at 6 fps)")
print(f"  distinct limb phases at 6 fps: {len(phases)} (need >= 4)  {'PASS' if len(phases) >= 4 else 'FAIL'}")
print(f"  head above hips: {len(samples) - len(head_bad)}/{len(samples)} samples  {'PASS' if not head_bad else 'FAIL at ' + ', '.join(f'{t:.2f}' for t in head_bad[:6])}")
print(f"  steps (foot L/R height crossings): {steps} in {dur:.2f} s = {steps / max(dur, 1e-3):.2f} steps/s")
if has_px:
    print(f"  hero fully in frame {t0:.2f}-{end:.2f} s (wall-run + top-out + landing): {len(span) - len(out)}/{len(span)} frames  {'PASS' if not out else 'FAIL at ' + ', '.join(f'{t:.2f}' for t in out[:8])}")
else:
    print("  hero in frame: no pixel data (headless run)")
print(f"  camera on the wall: pitch {min(pitch):.1f}..{max(pitch):.1f} deg (+ = up), below the hero {min(below):.2f}..{max(below):.2f} m, distance {min(dist):.2f}..{max(dist):.2f} m")
