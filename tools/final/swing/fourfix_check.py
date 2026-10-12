#!/usr/bin/env python3
"""Read-only, per-case telemetry hotspots for the four authorized swing fixes.

Usage: fourfix_check.py BEFORE_DIR [--after AFTER_DIR] [--output REPORT.json]
This supplements the unchanged final_check.py and flip_check.py.
"""

import argparse
import csv
import json
import math
from pathlib import Path


def f(row, key, default=None):
    try:
        v = float(row.get(key, ""))
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def r(value, places=3):
    return None if value is None else round(value, places)


def t(row):
    return r(f(row, "clip_t", f(row, "t")), 4)


def v3(row, prefix):
    values = [f(row, prefix + axis) for axis in ("_x", "_y", "_z")]
    return values if all(v is not None for v in values) else None


def unit(values):
    length = math.sqrt(sum(v * v for v in values))
    return [v / length for v in values] if length > 1e-8 else None


def angle(a, b):
    if a is None or b is None:
        return None
    return math.degrees(math.acos(max(-1, min(1, sum(x * y for x, y in zip(a, b))))))


def spans(rows, predicate):
    result, start = [], None
    for i, row in enumerate(rows):
        if predicate(row):
            if start is None:
                start = i
        elif start is not None:
            result.append({"first": t(rows[start]), "last": t(rows[i - 1]), "frames": i - start})
            start = None
    if start is not None:
        result.append({"first": t(rows[start]), "last": t(rows[-1]), "frames": len(rows) - start})
    return result


def cases(rows):
    out = {}
    for row in rows:
        out.setdefault(row.get("case") or "whole_clip", []).append(row)
    return out


def flips(rows):
    out, i = [], 0
    while i < len(rows):
        program = rows[i].get("flip_prog", "")
        if not program:
            i += 1
            continue
        a = i
        while i + 1 < len(rows) and rows[i + 1].get("flip_prog") == program and f(rows[i + 1], "flip_t", -1) >= f(rows[i], "flip_t", -1):
            i += 1
        out.append((a, i, program))
        i += 1
    return out


def camera(rows):
    missing = lambda x: f(x, "px_top", -1) < 0 or f(x, "hero_vis_px", -1) < 0
    clipped = lambda x: (f(x, "px_top", -1) == 0 or f(x, "px_bottom", -1) >= 1080
                         or f(x, "px_left", -1) == 0 or f(x, "px_right", -1) >= 1920)
    sizes = [(f(x, "hero_bbox_h"), x) for x in rows if f(x, "hero_bbox_h") is not None]
    rates = []
    for a, b in zip(rows, rows[1:]):
        dt = f(b, "t", 0) - f(a, "t", 0)
        y0, y1, p0, p1 = (f(a, "cam_yaw_deg"), f(b, "cam_yaw_deg"),
                          f(a, "cam_pitch_deg"), f(b, "cam_pitch_deg"))
        if dt > 0 and None not in (y0, y1, p0, p1):
            dy = (y1 - y0 + 180) % 360 - 180
            rates.append((math.hypot(dy, p1 - p0) / dt, b))
    sz = max(sizes, key=lambda x: x[0]) if sizes else None
    rate = max(rates, key=lambda x: x[0]) if rates else None
    distances = [f(x, "cam_dist_m") for x in rows if f(x, "cam_dist_m") is not None]
    return {
        "frames": len(rows),
        "absent": spans(rows, missing),
        "out_of_frame": spans(rows, lambda x: f(x, "hero_in_frame", 0) < 1),
        "edge_clipped": spans(rows, clipped),
        "size_over_0_36h": spans(rows, lambda x: f(x, "hero_bbox_h", 0) > 0.36),
        "max_projected_size_h": r(sz[0], 4) if sz else None,
        "max_size_at": t(sz[1]) if sz else None,
        "min_camera_distance_m": r(min(distances)) if distances else None,
        "max_yaw_pitch_delta_dps": r(rate[0], 1) if rate else None,
        "max_camera_rate_at": t(rate[1]) if rate else None,
    }


def projected_rotation(rows, next_row=None):
    # Mirror flip_check.py's 0.04 s projected pitch rate. New post-animation
    # fields are same-row; legacy bones shift one row only within a case.
    n = len(rows)
    same_frame = bool(rows) and all(f(x, "fw_body_pitch_deg") is not None for x in rows)
    source = "same_frame_post_animation" if same_frame else "legacy_case_bounded_shift"
    if n < 3 or (not same_frame and any(f(x, "body_pitch_deg") is None for x in rows)):
        return {"available": False, "reason": "no rendered pitch series"}
    ts = [f(x, "t") for x in rows]
    if None in ts or ts[-1] <= ts[0]:
        return {"available": False, "reason": "invalid timestamps"}
    same_case_next = bool(next_row and next_row.get("case", "") == rows[-1].get("case", ""))
    measured_n = n if same_frame or same_case_next else n - 1
    if measured_n < 2:
        return {"available": False, "reason": "no same-case shifted pose windows"}
    bp = ([f(row, "fw_body_pitch_deg") for row in rows]
          if same_frame else [f(rows[i + 1] if i + 1 < n else next_row, "body_pitch_deg")
                              for i in range(measured_n)])
    un = [bp[0]]
    for i in range(1, measured_n):
        un.append(un[-1] + (bp[i] - bp[i - 1] + 180) % 360 - 180)
    step = max(1, int(round(0.04 / max(1e-3, (ts[-1] - ts[0]) / (n - 1)))))
    rates = [(abs(un[i + step] - un[i]) / (ts[i + step] - ts[i]), i)
             for i in range(measured_n - step) if ts[i + step] > ts[i]]
    if not rates:
        return {"available": False, "reason": "no valid rate windows"}
    peak, at = max(rates)
    # Unlike the broad F4 checker, exclude Kickout/Reach waiting time.
    open_shapes = {"Pencil", "Throne", "Swan", "Straddle", "Layout"}
    holds, start, previous = [], None, None
    for rate, i in rates:
        shape = rows[i].get("flip_shape")
        if shape in open_shapes and rate <= 150:
            if start is None or rows[start].get("flip_shape") != shape:
                if start is not None:
                    holds.append({"shape": rows[start].get("flip_shape"), "first": t(rows[start]),
                                  "last": t(rows[previous]), "seconds": r(ts[previous] - ts[start] + 0.04, 4)})
                start = i
        elif start is not None:
            holds.append({"shape": rows[start].get("flip_shape"), "first": t(rows[start]),
                          "last": t(rows[previous]), "seconds": r(ts[previous] - ts[start] + 0.04, 4)})
            start = None
        previous = i
    if start is not None:
        holds.append({"shape": rows[start].get("flip_shape"), "first": t(rows[start]),
                      "last": t(rows[previous]), "seconds": r(ts[previous] - ts[start] + 0.04, 4)})
    holds.sort(key=lambda h: h["seconds"], reverse=True)
    return {"available": True, "rendered_axis_source": source, "window_frames": step,
            "projected_f3_peak_dps": r(peak, 1), "f3_le_800": peak <= 800,
            "peak_at": t(rows[at]), "peak_shape": rows[at].get("flip_shape"),
            "case_boundary_pose_excluded": bool(not same_frame and next_row and not same_case_next),
            "unmeasured_tail_frames": n - measured_n,
            "last_rate_window_ends_at": t(rows[rates[-1][1] + step]),
            "program_rate_at_peak_dps": r(f(rows[at], "flip_rate_dps"), 1),
            "primary_open_hold_longest": holds[0] if holds else None,
            "primary_open_hold_ge_0_30s": bool(holds and holds[0]["seconds"] >= 0.30),
            "primary_open_hold_intervals": holds[:5]}


def world_axis(rows):
    if not rows:
        return {"available": False, "reason": "empty trick"}
    direct = ("fw_body_axis_x", "fw_body_axis_y", "fw_body_axis_z")
    names = ("head_x", "head_y", "head_z", "hips_x", "hips_y", "hips_z")
    if all(all(f(row, key) is not None for key in direct) for row in rows):
        source = "same_frame_post_animation_world_axis"
        samples = [(row, unit([f(row, key) for key in direct])) for row in rows]
    elif all(k in rows[0] for k in names):
        source = "world_head_hips_xyz"
        samples = []
        for row in rows:
            head, hips = v3(row, "head"), v3(row, "hips")
            if head and hips:
                samples.append((row, unit([a - b for a, b in zip(head, hips)])))
    else:
        return {"available": False, "reason": "no world body-axis xyz; body_pitch/axis/roll are moving-frame projections"}
    samples = [(row, axis) for row, axis in samples if axis is not None]
    if len(samples) < 3:
        return {"available": False, "reason": "insufficient valid world-axis samples"}
    dt_mean = (f(samples[-1][0], "t") - f(samples[0][0], "t")) / (len(samples) - 1)
    step = max(1, int(round(0.04 / max(1e-3, dt_mean))))
    rates = []
    for i in range(len(samples) - step):
        a, va = samples[i]
        b, vb = samples[i + step]
        dt = f(b, "t", 0) - f(a, "t", 0)
        if dt > 0:
            rates.append((angle(va, vb) / dt, a))
    peak = max(rates, key=lambda x: x[0]) if rates else None
    return {"available": peak is not None, "source": source,
            "window_frames": step, "peak_3d_axis_dps": r(peak[0], 1) if peak else None,
            "peak_at": t(peak[1]) if peak else None}


def pose(row):
    try:
        values = [float(x) for x in row.get("pose_sig", "").split()]
        return [r(x) for x in values] if len(values) == 10 else None
    except ValueError:
        return None


def catch(rows, end):
    last = rows[end]
    caught = None
    for x in rows[end + 1:]:
        if f(x, "t", 0) - f(last, "t", 0) > 0.50 or x.get("mode") in {"land", "ground", "perch", "wall"}:
            break
        if x.get("mode") == "swing":
            caught = x
            break
    return {"end_at": t(last), "end_shape": last.get("flip_shape"),
            "end_pose_camera_plane": pose(last), "catch_at": t(caught) if caught else None,
            "catch_pose_camera_plane": pose(caught) if caught else None,
            "catch_gap_s": r(f(caught, "t") - f(last, "t"), 4) if caught else None,
            "visible_pose_classes": None}


def arm_direction(row, side):
    hand, shoulder = v3(row, "fw_h" + side), v3(row, "fw_sh" + side)
    return unit([a - b for a, b in zip(hand, shoulder)]) if hand and shoulder else None


def aim_error(row, side, strand):
    shoulder = v3(row, "fw_sh" + side)
    anchor = [f(row, f"fw_s{strand}_a{axis}") for axis in "xyz"]
    if shoulder is None or any(v is None for v in anchor):
        return None
    target = unit([a - b for a, b in zip(anchor, shoulder)])
    return angle(arm_direction(row, side), target)


def launches(rows):
    result = []
    for strand in (0, 1):
        key = f"fw_s{strand}_on"
        if not rows or key not in rows[0]:
            continue
        for i in range(1, len(rows)):
            if f(rows[i - 1], key, 0) >= 0.5 or f(rows[i], key, 0) < 0.5:
                continue
            side = "r" if f(rows[i], f"fw_s{strand}_hand", 1) > 0.5 else "l"
            samples = []
            for j in range(max(1, i - 1), min(len(rows), i + 4)):
                dt = f(rows[j], "t", 0) - f(rows[j - 1], "t", 0)
                turn = angle(arm_direction(rows[j - 1], side), arm_direction(rows[j], side))
                if dt > 0 and turn is not None:
                    samples.append((turn, turn / dt, rows[j]))
            peak = max(samples, key=lambda x: x[0]) if samples else None
            shoot = f(rows[i], f"fw_s{strand}_shoot")
            arrival = None
            if shoot is not None:
                for j in range(i, len(rows)):
                    if f(rows[j], key, 0) < 0.5:
                        break
                    if f(rows[j], f"fw_s{strand}_age", -1) >= shoot:
                        arrival = j
                        break
            pose_at_shot = rows[min(i + 1, len(rows) - 1)]
            pose_at_arrival = rows[min(arrival + 1, len(rows) - 1)] if arrival is not None else None
            result.append({"strand": strand, "hand": "right" if side == "r" else "left",
                           "shot_on": t(rows[i]), "shoot_time_s": shoot,
                           "first_pose_angle_deg": r(angle(arm_direction(rows[i - 1], side), arm_direction(rows[i], side)), 1),
                           "peak_near_launch_angle_deg": r(peak[0], 1) if peak else None,
                           "peak_near_launch_rate_dps": r(peak[1], 1) if peak else None,
                           "peak_at": t(peak[2]) if peak else None,
                           "aim_error_at_shot_deg": r(aim_error(pose_at_shot, side, strand), 1),
                           "tip_arrival_at": t(rows[arrival]) if arrival is not None else None,
                           "aim_error_at_tip_arrival_deg": r(aim_error(pose_at_arrival, side, strand), 1) if pose_at_arrival else None})
    return sorted(result, key=lambda x: x["shot_on"] or -1)


def inspect(path):
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    global_index = {id(row): i for i, row in enumerate(rows)}
    report = {"csv": path.name, "frames": len(rows), "cases": {}}
    for name, group in cases(rows).items():
        windows = []
        for a, b, program in flips(group):
            end_time = f(group[b], "t", 0)
            tail = [x for x in group[a:] if f(x, "t", 0) <= end_time + 0.50]
            next_index = global_index[id(group[b])] + 1
            # flip_check.py takes its one-row pose shift from the complete CSV,
            # even when a trick ends at a scripted case boundary.
            next_pose = rows[next_index] if next_index < len(rows) else None
            windows.append({"program": program, "start": t(group[a]), "end": t(group[b]),
                            "camera_through_catch": camera(tail),
                            "rotation": projected_rotation(group[a:b + 1], next_pose),
                            "world_3d_axis_rate": world_axis(group[a:b + 1]),
                            "catch": catch(group, b)})
        report["cases"][name] = {"flip_windows": windows, "launches": launches(group)}
    return report


def directory(path):
    return {p.stem.removesuffix("_telemetry"): inspect(p)
            for p in sorted(path.glob("*_telemetry.csv"))}


def compare(before, after):
    out = {}
    for clip in sorted(set(before) | set(after)):
        a, b = before.get(clip), after.get(clip)
        if not a or not b:
            out[clip] = {"status": "clip missing on one side"}
            continue
        out[clip] = {}
        for case in sorted(set(a["cases"]) | set(b["cases"])):
            x, y = a["cases"].get(case), b["cases"].get(case)
            if not x or not y:
                out[clip][case] = {"status": "case missing on one side"}
                continue
            pairs = []
            for old, new in zip(x["flip_windows"], y["flip_windows"]):
                if old["program"] != new["program"]:
                    pairs.append({"status": "program mismatch; inspect route"})
                    continue
                oc, nc = old["camera_through_catch"], new["camera_through_catch"]
                orot, nrot = old["rotation"], new["rotation"]
                pairs.append({"program": old["program"],
                              "absent_frames": [sum(z["frames"] for z in oc["absent"]), sum(z["frames"] for z in nc["absent"])],
                              "out_of_frame_frames": [sum(z["frames"] for z in oc["out_of_frame"]), sum(z["frames"] for z in nc["out_of_frame"])],
                              "max_projected_size_h": [oc["max_projected_size_h"], nc["max_projected_size_h"]],
                              "projected_f3_peak_dps": [orot.get("projected_f3_peak_dps"), nrot.get("projected_f3_peak_dps")],
                              "primary_open_hold_s": [(orot.get("primary_open_hold_longest") or {}).get("seconds"),
                                                      (nrot.get("primary_open_hold_longest") or {}).get("seconds")],
                              "catch_pose_signatures": [old["catch"]["catch_pose_camera_plane"], new["catch"]["catch_pose_camera_plane"]]})
            if len(x["flip_windows"]) != len(y["flip_windows"]):
                pairs.append({"status": "flip count mismatch; inspect route"})
            out[clip][case] = {"flips": pairs,
                               "launch_peak_angle_deg": [[z["peak_near_launch_angle_deg"] for z in x["launches"]],
                                                         [z["peak_near_launch_angle_deg"] for z in y["launches"]]],
                               "launch_aim_error_at_arrival_deg": [[z["aim_error_at_tip_arrival_deg"] for z in x["launches"]],
                                                                   [z["aim_error_at_tip_arrival_deg"] for z in y["launches"]]]}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.before.is_dir() or (args.after and not args.after.is_dir()):
        parser.error("input directories must exist")
    before = directory(args.before)
    after = directory(args.after) if args.after else None
    if not before or (args.after and not after):
        parser.error("no *_telemetry.csv files found")
    report = {"tool": "fourfix_check.py", "source": "existing CSV telemetry; no video inference",
              "thresholds_unchanged": {"TC_C_size_top_h": 0.36, "F3_projected_peak_top_dps": 800,
                                       "primary_open_hold_rate_top_dps": 150, "primary_open_hold_min_s": 0.30},
              "measurement_limits": ["Pose signatures are camera-plane joint offsets, not visible pose classes.",
                                     "Launch arm direction includes body motion and a one-row rendered-pose delay.",
                                     "The standard telemetry lacks raw world head and hip xyz; true 3D body-axis rate is unavailable.",
                                     "At a scripted case boundary the final shifted pose sample is unavailable; preceding full rate windows remain measured."],
              "before": before, "after": after,
              "comparison": compare(before, after) if after is not None else None}
    output = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
