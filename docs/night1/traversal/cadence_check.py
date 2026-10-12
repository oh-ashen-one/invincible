#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Swing cadence check (critic round 06) on a telemetry CSV, over the first WINDOW seconds:
#  - web attaches (entries into 'swing') and attach -> release durations (target 1.2-1.8 s)
#  - web-less air phases: release -> next web stuck (web_on column; else swing start) (target: next web within 0.5 s; none > 0.6 s unless a trick is running)
#  - release height vs the swing's highest point after its low point (release near the top of the arc)
#  - drop per swing: height at the preceding release (or start) minus the swing's low point (target >= 10 m)
#  - rope on screen: frames with a web attached (strand stuck: web_on, or swing mode) AND the hero projected inside the frame, share of all frames
#  - body vs rope at the arc bottom: body_rope_deg (hips->head vs hips->anchor) at each swing's low point (target <= 15)
# usage: cadence_check.py <telemetry.csv> [label] [window_s]
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
lab = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
W = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
for i in range(len(rows) - 1):  # bone-derived columns are sampled at the start of the next frame
    for k in ("body_rope_deg",):
        if k in rows[i + 1]:
            rows[i][k] = rows[i + 1][k]
rows = [r for r in rows[:-1] if float(r["t"]) <= W]
h = lambda r: float(r["height_above_floor_m"]) if float(r["height_above_floor_m"]) < 900 else 0.0
swings, gaps, cur, gap0, trick_in_gap, last_rel = [], [], None, None, False, h(rows[0])
for r in rows:
    t, sw = float(r["t"]), r["mode"] == "swing"
    if gap0 is not None and (r.get("web_on") == "1" or sw):  # next web stuck (web_on) or swing started
        gaps.append((gap0, t, t - gap0, trick_in_gap)); gap0 = None
    if sw and cur is None:
        cur = dict(t0=t, rel_before=last_rel, low=h(r), tlow=t, hi_after_low=h(r), br=None, rows=[])
        gap0 = None
    if sw:
        cur["rows"].append(r)
        if h(r) < cur["low"]:
            cur.update(low=h(r), tlow=t, hi_after_low=h(r))
            cur["br"] = r.get("body_rope_deg")
        cur["hi_after_low"] = max(cur["hi_after_low"], h(r))
        cur["t1"], cur["exit"] = t, h(r)
        last_rel = h(r)
    elif cur is not None:
        swings.append(cur); cur = None; gap0 = t; trick_in_gap = False
    if not sw and r["mode"] == "air":
        last_rel = max(last_rel, h(r))
        if r["sub"] == "trick":
            trick_in_gap = True
if cur is not None:
    swings.append(cur)
n_att = len(swings)
on = sum(1 for r in rows if (r.get("web_on", "0") == "1" or r["mode"] == "swing") and r["hero_in_frame"] == "1")
print(f"{lab}: first {W:.0f} s ({len(rows)} frames)")
print(f"  web attaches: {n_att}  (target >= 7)  {'PASS' if n_att >= 7 else 'FAIL'}")
print(f"   #    t0    t1   dur  relH  lowH  drop exitH peakH  rel-vs-peak  body-rope@low")
for i, s in enumerate(swings):
    dur = s["t1"] - s["t0"]
    drop = s["rel_before"] - s["low"]
    br = s["br"] if s["br"] not in (None, "", "nan") else "-"
    print(f"  {i+1:2d} {s['t0']:5.2f} {s['t1']:5.2f} {dur:5.2f} {s['rel_before']:5.1f} {s['low']:5.1f} {drop:5.1f} {s['exit']:5.1f} {s['hi_after_low']:5.1f}  {s['exit'] - s['hi_after_low']:+6.1f} m    {br}")
full = [s for s in swings if s["t1"] < W - 0.05]
durs = [s["t1"] - s["t0"] for s in full]
if durs:
    print(f"  attach->release (complete swings): {min(durs):.2f}..{max(durs):.2f} s, mean {sum(durs)/len(durs):.2f} (target 1.2-1.8)")
if gaps:
    print(f"  web-less gaps: " + ", ".join(f"{g[0]:.2f}+{g[2]:.2f}{'T' if g[3] else ''}" for g in gaps))
    long = [g for g in gaps if g[2] > 0.6 and not g[3]]
    print(f"  longest gap {max(g[2] for g in gaps):.2f} s; gaps > 0.6 s without a trick: {len(long)}  {'PASS' if not long else 'FAIL'}")
drops = [s["rel_before"] - s["low"] for s in swings[1:] if s["t1"] < W - 0.05]  # swings completed inside the window
if drops:
    print(f"  drop per swing (after the first): min {min(drops):.1f} m  (target >= 10)  {'PASS' if min(drops) >= 10 else 'FAIL'}")
print(f"  rope on screen (web stuck + hero in frame): {on}/{len(rows)} = {100*on/len(rows):.1f}%  (target >= 75)  {'PASS' if on >= 0.75*len(rows) else 'FAIL'}")
brs = [float(s["br"]) for s in swings if s["t1"] < W - 0.05 and s["br"] not in (None, "", "nan", "-")]
if brs:
    print(f"  body vs rope at the arc bottom: max {max(brs):.1f} deg  (target <= 15)  {'PASS' if max(brs) <= 15 else 'FAIL'}")
