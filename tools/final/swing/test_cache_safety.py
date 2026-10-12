"""Offline safety checks for run_clip's optional cache cleanup."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cache_safety import cache_work, scratch_root, validate_and_cleanup


class ScratchSafetyTest(unittest.TestCase):
    def test_rejects_shared_cache_source_and_relative_roots(self):
        project = Path(__file__).resolve().parents[3]
        with self.assertRaises(ValueError):
            scratch_root("relative-cache", project)
        with self.assertRaises(ValueError):
            scratch_root(Path.home() / "sm2-n1/_scratch/final/swing/new", project)
        with self.assertRaises(ValueError):
            scratch_root(project / "Saved/cache", project)
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "old-cache"
            link.symlink_to(Path.home() / "sm2-n1/_scratch")
            with self.assertRaises(ValueError):
                scratch_root(link, project)

    def test_cleanup_only_after_complete_artifacts(self):
        project = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch_root(Path(tmp) / "capture", project)
            work = cache_work(root, "round-13-closeout", "s2_press_variety")
            cases = ["c1", "c2"]
            for name in cases:
                frames = work / name / "frames_done"
                frames.mkdir(parents=True)
                (frames / "MovieFrame00000.png").write_bytes(b"frame")
            mp4 = Path(tmp) / "clip.mp4"
            csv_path = Path(tmp) / "clip.csv"
            metadata = Path(tmp) / "render.json"
            with csv_path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["clip_frame", "case"])
                writer.writeheader()
                writer.writerows([{"clip_frame": "0", "case": "c1"}, {"clip_frame": "1", "case": "c2"}])
            metadata.write_text(json.dumps({"frames": 2, "cases": [
                {"case": name, "rows": 1, "frames_rendered": 1} for name in cases]}))
            with self.assertRaises(ValueError):
                validate_and_cleanup(root, work, mp4, csv_path, metadata, 2, cases)
            self.assertTrue((work / "c1/frames_done/MovieFrame00000.png").exists())
            mp4.write_bytes(b"encoded")
            with patch("cache_safety.subprocess.run", side_effect=RuntimeError("ffprobe failed")):
                with self.assertRaises(RuntimeError):
                    validate_and_cleanup(root, work, mp4, csv_path, metadata, 2, cases)
            self.assertTrue((work / "c2/frames_done/MovieFrame00000.png").exists())
            short_probe = type("Probe", (), {"stdout": json.dumps({"streams": [{
                "codec_name": "h264", "width": 1920, "height": 1080, "nb_read_frames": "1"}]})})()
            with patch("cache_safety.subprocess.run", return_value=short_probe):
                with self.assertRaises(ValueError):
                    validate_and_cleanup(root, work, mp4, csv_path, metadata, 2, cases)
            self.assertTrue((work / "c1/frames_done/MovieFrame00000.png").exists())
            probe = type("Probe", (), {"stdout": json.dumps({"streams": [{
                "codec_name": "h264", "width": 1920, "height": 1080, "nb_read_frames": "2"}]})})()
            with patch("cache_safety.subprocess.run", return_value=probe):
                validate_and_cleanup(root, work, mp4, csv_path, metadata, 2, cases)
            self.assertFalse((work / "c1/frames_done").exists())
            self.assertFalse((work / "c2/frames_done").exists())
            self.assertTrue(mp4.exists())
            self.assertTrue(csv_path.exists())
            self.assertTrue(metadata.exists())


if __name__ == "__main__":
    unittest.main()
