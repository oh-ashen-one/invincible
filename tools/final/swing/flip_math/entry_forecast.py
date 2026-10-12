#!/usr/bin/env python3
"""Forecast c7 entry rates from paired actual final-axis captures; actual replay remains decisive."""
import argparse
import csv
import math
from pathlib import Path
import re


def unit(vector):
    length = math.sqrt(sum(x * x for x in vector))
    return [x / length for x in vector]


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def extrapolate_axis(a, b, fraction):
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    angle = math.acos(dot)
    if angle < 1e-6:
        return a
    divisor = math.sin(angle)
    return unit([(math.sin((1.0 - fraction) * angle) * x + math.sin(fraction * angle) * y) / divisor
                 for x, y in zip(a, b)])


def forecast(rows, entry_seconds):
    samples = []
    for row in rows:
        time = float(row["flip_t"])
        # The fixture records actual variants sampled at 60Hz; use precise case time
        # rather than the legacy flip_t column's three-decimal rounding for weights.
        time = float(row["t"]) - 0.4
        old_a, old_b = smooth(time / 0.15), smooth(time / 0.25)
        candidate = smooth(time / entry_seconds)
        axis_a = unit([float(row["axis_a_" + component]) for component in "xyz"])
        axis_b = unit([float(row["axis_b_" + component]) for component in "xyz"])
        if abs(old_b - old_a) < 1e-6:
            axis = axis_a
        else:
            axis = extrapolate_axis(axis_a, axis_b, (candidate - old_a) / (old_b - old_a))
        # In this airborne case traversal facing follows horizontal velocity.
        forward = unit([float(row["vx"]), float(row["vy"]), 0.0])
        pitch = math.degrees(math.atan2(sum(x * y for x, y in zip(axis, forward)), axis[2]))
        samples.append((float(row["t"]), pitch, axis))
    windows = []
    for index in range(len(samples) - 2):
        start, end = samples[index], samples[index + 2]
        dt = end[0] - start[0]
        pitch_delta = (end[1] - start[1] + 180.0) % 360.0 - 180.0
        dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(start[2], end[2]))))
        windows.append((abs(pitch_delta) / dt, math.degrees(math.acos(dot)) / dt, start[0]))
    return max(windows), max(windows, key=lambda sample: sample[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    fixture = Path(__file__).resolve().parent
    with (fixture / "c7_entry_pairs.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    header = (args.source_root / "unreal/WebHomage/Source/WebHomage/Traversal/WebTravFlips.h").read_text()
    current = float(re.search(r"PoseEntryS\s*=\s*([0-9.]+)f", header).group(1))
    for anchor, measured in [(0.15, 804.38), (0.25, 812.41)]:
        projected, spatial = forecast(rows, anchor)
        assert abs(projected[0] - measured) < 0.1, (anchor, projected)
        print(f"Recorded entry {anchor:.2f}s: projected={projected[0]:.2f}deg/s, 3D={spatial[1]:.2f}deg/s")
    projected, spatial = forecast(rows, current)
    print(f"CURRENT entry {current:.2f}s forecast: projected={projected[0]:.2f}deg/s@{projected[2]:.4f}s, "
          f"3D={spatial[1]:.2f}deg/s@{spatial[2]:.4f}s; approximate, requires rendered replay")
    assert projected[0] <= 800.0 and spatial[1] <= 800.0, (current, projected, spatial)


if __name__ == "__main__":
    main()
