#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Animation check on a telemetry CSV (critic round 03):
#  - T-pose / no-clip frames: anim clip weight < 0.5 or no node
#  - air silhouettes at 6 fps: consecutive air samples (every 10th frame at 60 fps) must differ; distance = mean 2D
#    displacement (m, camera right/up) of head, hands, feet relative to the hips; "same" if < SAME_M
#  - air cycles (release -> next attach / landing): the node sequence of each cycle must differ from the previous cycle's
# usage: anim_check.py <telemetry.csv> [label]
import csv, sys
SAME_M = 0.08
rows = list(csv.DictReader(open(sys.argv[1])))
# the anim / pose columns are written at the start of the next frame (the mesh evaluates after the actor tick):
# align them with the frame they were rendered in (row i takes row i+1's anim fields)
for i in range(len(rows) - 1):
    for k in ("anim_node", "anim_clip", "anim_weight", "air_flavor", "pose_sig"):
        rows[i][k] = rows[i + 1][k]
rows = rows[:-1]
lab = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
tpose = [float(r["t"]) for r in rows if float(r["anim_weight"]) < 0.5 or r["anim_node"] in ("none", "None", "")]
def sig(r):
    v = [float(x) for x in r["pose_sig"].split()]
    return list(zip(v[0::2], v[1::2]))
samples = rows[::10]
air_pairs = same = 0
worst = 9.0
for a, b in zip(samples, samples[1:]):
    if a["mode"] != "air" or b["mode"] != "air":
        continue
    sa, sb = sig(a), sig(b)
    d = sum(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 for (x1, y1), (x2, y2) in zip(sa, sb)) / len(sa)
    air_pairs += 1
    worst = min(worst, d)
    if d < SAME_M:
        same += 1
        print(f"  same silhouette: t={float(a['t']):.2f}->{float(b['t']):.2f} d={d:.3f} m ({a['anim_node']} -> {b['anim_node']})")
# cycles
cycles, cur, prev_mode = [], None, None
for r in rows:
    m = r["mode"]
    if m == "air" and prev_mode == "swing":
        cur = []
    if cur is not None:
        if m != "air":
            cycles.append(cur); cur = None
        elif not cur or cur[-1] != r["anim_node"]:
            cur.append(r["anim_node"])
    prev_mode = m
if cur:
    cycles.append(cur)
rep = sum(1 for x, y in zip(cycles, cycles[1:]) if x == y)
print(f"{lab}: {len(rows)} frames")
print(f"  T-pose / no-clip frames: {len(tpose)}" + (f" (first at {tpose[0]:.2f}s)" if tpose else ""))
print(f"  air silhouettes at 6 fps: {air_pairs} consecutive air pairs, {same} with the same silhouette (min distance {worst if air_pairs else 0:.3f} m, threshold {SAME_M} m)")
print(f"  air cycles: {len(cycles)}; consecutive identical cycles: {rep}")
for i, c in enumerate(cycles):
    print(f"    cycle {i+1}: {' > '.join(c)}")
