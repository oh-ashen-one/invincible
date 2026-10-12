#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Swing arc test on a telemetry CSV: for every swing, drop = height at the preceding release (or the spawn / take-off
# height for the first swing) minus the lowest height during that swing; also rope length, duration, release height.
# PASS rule (critic round 01; round 07: >= 10 m, relaxed by the orchestrator with the cadence gap): drop >= DROP_MIN m on every swing, and consecutive swings differ (drop or rope or duration > 5 %).
# usage: drop_test.py <telemetry.csv> [--skip-first] [--min M]   (round 24: --min 20 = the T7 drop of critic r23)
import csv, math, sys
rows = list(csv.DictReader(open(sys.argv[1])))
skip_first = "--skip-first" in sys.argv
DROP_MIN = float(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 10.0
z = lambda r: float(r["height_above_floor_m"]) if float(r["height_above_floor_m"]) < 900 else 0.0
# horizon (vanishing point) height on screen, fraction of frame height above centre: 0.5 tan(-pitch) / tan(vfov/2)
vp = lambda r: 0.5 * math.tan(math.radians(-float(r["cam_pitch_deg"]))) / math.tan(math.radians(float(r["cam_vfov_deg"]) / 2))
swings, cur, last_rel = [], None, z(rows[0])
for r in rows:
    sw = r["mode"] == "swing"
    if sw and cur is None:
        cur = {"t0": float(r["t"]), "entry": z(r), "rel_before": last_rel, "min": z(r), "rope": float(r["rope_m"]), "tmin": float(r["t"]), "vp_low": vp(r)}
    if sw:
        if z(r) < cur["min"]:
            cur["min"], cur["tmin"], cur["vp_low"] = z(r), float(r["t"]), vp(r)
        cur["rope"] = float(r["rope_m"]); cur["t1"] = float(r["t"]); cur["exit"] = z(r); cur["vp_rel"] = vp(r)
    elif cur is not None:
        swings.append(cur); cur = None
    if not sw:
        last_rel = max(last_rel, z(r)) if r["mode"] == "air" else z(r)
    if sw:
        last_rel = z(r)
# round 08: a swing still running when the recording ends is incomplete (its low point is unknown): not judged
ok = True
tv = [(float(r["t"]), vp(r)) for r in rows]
print(f"{'#':>2} {'t0':>6} {'relH':>6} {'entryH':>6} {'lowH':>6} {'drop':>6} {'exitH':>6} {'rope':>6} {'dur':>5} {'VPlow>rel':>9} {'VPcycle':>7}  result")
prev = None
for i, s in enumerate(swings):
    drop = s["rel_before"] - s["min"]
    dur = s["t1"] - s["t0"]
    s["drop"], s["dur"] = drop, dur
    cyc = [v for t, v in tv if s["t0"] <= t <= s["t1"] + 0.6]
    s["vpr"] = (max(cyc) - min(cyc)) * 100 if cyc else 0
    res = "ok" if drop >= DROP_MIN else f"DROP<{DROP_MIN:g}"
    if i == 0 and skip_first:
        res += " (first swing exempt)"
    elif drop < DROP_MIN:
        ok = False
    if prev:
        same = all(abs(a - b) <= 0.05 * max(abs(b), 1e-3) for a, b in ((drop, prev["drop"]), (s["rope"], prev["rope"]), (dur, prev["dur"])))
        if same:
            res += " SAME-AS-PREV"; ok = False
    print(f"{i+1:>2} {s['t0']:6.2f} {s['rel_before']:6.1f} {s['entry']:6.1f} {s['min']:6.1f} {drop:6.1f} {s['exit']:6.1f} {s['rope']:6.1f} {dur:5.2f} {abs(s['vp_rel']-s['vp_low'])*100:8.1f}% {s['vpr']:6.1f}%  {res}")
    prev = s
print("DROP TEST:", "PASS" if ok and swings else "FAIL", f"({len(swings)} swings)")
