"""Regression for case-aligned rendered-axis sampling; no engine required."""

import contextlib
import csv
import importlib.util
import io
import math
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


flip = load("flip_check", ROOT / "docs/night1/traversal/flip_check.py")
fourfix = load("fourfix_check", ROOT / "tools/final/swing/fourfix_check.py")


FIELDS = ("t clip_t case mode flip_prog flip_t body_pitch_deg body_axis_deg "
          "flip_rate_dps flip_shape flip_shape_legs flip_twist_deg flip_pitch_deg "
          "pcm_roll cam_z z_m px_bottom px_top fw_body_pitch_deg fw_body_axis_deg "
          "fw_body_axis_x fw_body_axis_y fw_body_axis_z").split()


def sample(index, case, program, pitch, shape="Tuck"):
    return {"t": f"{index / 60:.4f}", "clip_t": f"{index / 60:.4f}",
            "case": case, "mode": "air", "flip_prog": program,
            "flip_t": f"{index / 60:.4f}" if program else "-1",
            "body_pitch_deg": str(pitch), "body_axis_deg": "40",
            "flip_rate_dps": "600" if program else "0",
            "flip_shape": shape if program else "", "flip_shape_legs": shape if program else "",
            "flip_twist_deg": "0", "flip_pitch_deg": str(pitch),
            "pcm_roll": "0", "cam_z": "4", "z_m": "3",
            "px_bottom": "500", "px_top": "200"}


def run_checker(rows):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "synthetic.csv"
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            flip.main(str(path), "synthetic")
        return output.getvalue()


class CaseAlignment(unittest.TestCase):
    def test_new_case_spawn_does_not_create_f3_peak(self):
        rows = [sample(i, "c1", "wallFront", 10 * i) for i in range(6)]
        rows.append(sample(6, "c2", "", 170))
        report = run_checker(rows)
        peak = float(re.search(r"F3 peak (\d+) deg/s", report).group(1))
        self.assertLessEqual(peak, 800)
        self.assertIn("rendered axis limit: final", report)
        focused = fourfix.projected_rotation(rows[:6], rows[6])
        self.assertTrue(focused["case_boundary_pose_excluded"])
        self.assertEqual(focused["unmeasured_tail_frames"], 1)
        self.assertLessEqual(focused["projected_f3_peak_dps"], 800)

    def test_genuine_same_case_peak_still_fails_f3(self):
        rows = [sample(i, "c1", "frontSingle", 17 * i) for i in range(8)]
        rows.append(sample(8, "c1", "", 136))
        report = run_checker(rows)
        peak = float(re.search(r"F3 peak (\d+) deg/s FAIL", report).group(1))
        self.assertGreater(peak, 800)
        self.assertNotIn("rendered axis limit", report)
        focused = fourfix.projected_rotation(rows[:8], rows[8])
        self.assertFalse(focused["case_boundary_pose_excluded"])
        self.assertGreater(focused["projected_f3_peak_dps"], 800)

    def test_complete_same_frame_columns_take_priority_and_enable_3d_rate(self):
        rows = [sample(i, "c1", "frontSingle", 20 * i) for i in range(8)]
        rows.append(sample(8, "c1", "", 160))
        for i, row in enumerate(rows):
            degrees = 5 * i
            rad = math.radians(degrees)
            row.update({"fw_body_pitch_deg": str(degrees),
                        "fw_body_axis_deg": str(degrees),
                        "fw_body_axis_x": str(math.sin(rad)),
                        "fw_body_axis_y": "0",
                        "fw_body_axis_z": str(math.cos(rad))})
        report = run_checker(rows)
        self.assertIn("rendered-axis phase: same-frame post-animation", report)
        self.assertRegex(report, r"F3 peak 300 deg/s FAIL")  # below the unchanged 450 floor
        focused = fourfix.projected_rotation(rows[:8], rows[8])
        self.assertEqual(focused["rendered_axis_source"], "same_frame_post_animation")
        self.assertAlmostEqual(focused["projected_f3_peak_dps"], 300, delta=1)
        true_3d = fourfix.world_axis(rows[:8])
        self.assertTrue(true_3d["available"])
        self.assertEqual(true_3d["source"], "same_frame_post_animation_world_axis")
        self.assertAlmostEqual(true_3d["peak_3d_axis_dps"], 300, delta=1)

    def test_five_baseline_primary_failures_persist(self):
        path = ROOT / "docs/night1/final/swing/round-13-closeout/s3b_flip_cases_telemetry.csv"
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        grouped = fourfix.cases(rows)
        expected = {"s3_c1_fwd": ("frontSingle", 810.8),
                    "s3_c2_back": ("backSingle", 811.4),
                    "s3_c4_left": ("barani", 819.8),
                    "s3_c6_fwd_right": ("rudi", 871.3),
                    "s3_c7_back_left": ("fullTwist", 867.9)}
        for case, (name, old_peak) in expected.items():
            with self.subTest(case=case):
                group = grouped[case]
                a, b, program = next(run for run in fourfix.flips(group) if run[2] == name)
                peak = fourfix.projected_rotation(group[a:b + 1], group[b + 1])["projected_f3_peak_dps"]
                self.assertEqual(program, name)
                self.assertAlmostEqual(peak, old_peak, delta=0.1)
                self.assertGreater(peak, 800)


if __name__ == "__main__":
    unittest.main()
