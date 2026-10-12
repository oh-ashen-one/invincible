#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 26 targets (director after the r25 critic), engine side on a w1 telemetry CSV (rendered or -nullrhi):
#   V1 vertical wall-run 0.95-3.58 s (mode wall, sub wallRun): lateral knee gap (knee_gap_lat_m, shins across the run axis) median <= 0.25 m
#   V2 at 10 fps, every sample t vs t + 0.3 s: the limb pose differs -- limb_z (hands / feet height over the hips) distance > 0.12 m
#      (wall_check.py DIST_M) AND the gait phase moved >= 0.15 cycle away from 0 / 1 (not the same stride phase)
#   V3 knees drive forward: the recovery knee leaves the wall (max knee_wall of the two) >= 0.25 m in every 0.4 s window;
#      arms alternate: sign changes of (hand_L - hand_R) height >= 3 per second
#   C1 camera -> hero distance (cam_hero_dist_m) inside 4.0-7.0 m on every wall-run row (T15)
#   C2 hero box height / frame (px mask, rendered only) p90 inside 0.30-0.38 (T8 cap .38, director floor .30)
# usage: r26_checks.py <telemetry.csv> [label] [t0 t1]
import csv, sys, math
rows = list(csv.DictReader(open(sys.argv[1])))
for i in range(len(rows) - 1):   # anim / pose / pixel columns are sampled at the start of the next frame
    for k in ("anim_node", "anim_clip", "pose_sig", "head_hip_dz", "limb_z", "px_top", "px_bottom", "px_left", "px_right"):
        if k in rows[i + 1]:
            rows[i][k] = rows[i + 1][k]
rows = rows[:-1]
lab = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
T0, T1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.95, 3.58)
f = lambda r, k: float(r[k])
W = [r for r in rows if T0 <= f(r, "t") <= T1 and r["mode"] == "wall"]
if not W:
    print(f"{lab}: no wall rows in {T0}-{T1} s"); sys.exit(0)
def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p; a = math.floor(k); b = min(a + 1, len(v) - 1); return v[a] + (v[b] - v[a]) * (k - a)
res = []
def line(name, ok, text):
    res.append(ok); print(f"  {name:3s} {'PASS' if ok else 'FAIL'}  {text}")
print(f"{lab}: wall rows {f(W[0], 't'):.2f}-{f(W[-1], 't'):.2f} s ({len(W)} rows, subs {sorted(set(r['sub'] for r in W))})")
run = [r for r in W if r["sub"] == "wallRun" and f(r, "wall_ik_w") >= 0.99]
kl = [f(r, "knee_gap_lat_m") for r in run]
line("V1", pct(kl, .5) <= 0.25, f"lateral knee gap median {pct(kl, .5):.3f} m (p10 {pct(kl, .1):.3f}, p90 {pct(kl, .9):.3f}, max {max(kl):.3f}) on {len(run)} full-IK rows")
# 10 fps samples (every 6th 60 fps row) of the full-IK run, each vs the row 0.3 s later
idx = {round(f(r, "t") * 60): r for r in run}
ks = sorted(idx)
smp = [k for k in ks if (k - ks[0]) % 6 == 0]
pairs, bad = 0, []
for k in smp:
    r2 = idx.get(k + 18)
    if r2 is None: continue
    r1 = idx[k]; pairs += 1
    lz1 = [float(v) for v in r1["limb_z"].split()]; lz2 = [float(v) for v in r2["limb_z"].split()]
    d = math.dist(lz1, lz2)
    dph = abs(f(r2, "gait_ph") - f(r1, "gait_ph")) % 1.0; dph = min(dph, 1.0 - dph)
    if not (d > 0.12 and dph >= 0.15): bad.append(f"{f(r1, 't'):.1f}->{f(r2, 't'):.1f} (d {d:.2f} m, dph {dph:.2f})")
line("V2", pairs > 0 and not bad, f"10 fps samples vs +0.3 s: {pairs - len(bad)}/{pairs} pairs differ (limb_z dist > .12 m, gait phase >= .15 cycle apart)" + (f"; same: {', '.join(bad[:6])}" if bad else ""))
kw = [(f(r, "t"), max(f(r, "knee_wall_l"), f(r, "knee_wall_r"))) for r in run]
wins, ok = 0, 0
t = kw[0][0]
while t + 0.4 <= kw[-1][0] + 1e-6:
    vs = [v for tt, v in kw if t <= tt < t + 0.4]
    if vs: m = max(vs); wins += 1; ok += m >= 0.25
    t += 0.4
hz = [float(r["limb_z"].split()[0]) - float(r["limb_z"].split()[1]) for r in run]
sc = sum(1 for a, b in zip(hz, hz[1:]) if (a > 0) != (b > 0))
dur = f(run[-1], "t") - f(run[0], "t")
line("V3", ok == wins and sc / max(dur, 1e-3) >= 3.0, f"recovery knee off the wall >= .25 m in {ok}/{wins} 0.4 s windows (median knee-off {pct([v for _, v in kw], .5):.2f} m); "
     f"hand lead changes {sc} in {dur:.2f} s = {sc / max(dur, 1e-3):.1f}/s; gait {pct([f(r, 'gait_ph') for r in run], 0):.2f}..")
cd = [f(r, "cam_hero_dist_m") for r in W]
line("C1", min(cd) >= 4.0 and max(cd) <= 7.0, f"camera -> hero {min(cd):.2f}-{max(cd):.2f} m (median {pct(cd, .5):.2f}) over the wall rows (4.0-7.0)")
px = [r for r in W if f(r, "px_top") >= 0]
if px:
    hh = [(f(r, "px_bottom") - f(r, "px_top")) / 1080.0 for r in px]
    line("C2", 0.30 <= pct(hh, .9) <= 0.38, f"hero box height / frame (px mask): p10 {pct(hh, .1):.3f} p50 {pct(hh, .5):.3f} p90 {pct(hh, .9):.3f} on {len(px)} rows (p90 0.30-0.38)")
else:
    bb = [f(r, "hero_bbox_h") for r in W if f(r, "hero_bbox_h") < 0.99]
    print(f"  C2 n/a   no px mask (-nullrhi); bone-bbox height p50 {pct(bb, .5):.3f} p90 {pct(bb, .9):.3f} (proxy only)")
print(f"  -> {sum(res)}/{len(res)} PASS")
