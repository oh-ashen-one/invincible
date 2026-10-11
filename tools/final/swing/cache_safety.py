"""Guard the optional, task-owned frame cache cleanup for run_clip.py."""

import csv
import json
import re
import shutil
import subprocess
from pathlib import Path


def _inside(path, parent):
    return path == parent or parent in path.parents


def scratch_root(value, project):
    """Require an absolute cache path separate from source and the old shared cache."""
    raw = Path(value).expanduser()
    if not raw.is_absolute():
        raise ValueError("--scratch-root must be an absolute path")
    root = raw.resolve()
    protected = (Path(project).resolve(),
                 (Path.home() / "spider-man-2").resolve(),
                 (Path.home() / "sm2-n1/_scratch").resolve())
    if any(_inside(root, p) or _inside(p, root) for p in protected):
        raise ValueError("--scratch-root must be separate from project source and ~/sm2-n1/_scratch")
    return root


def cache_work(root, round_name, clip):
    for part in (round_name, clip):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", part):
            raise ValueError("round and clip must be simple names without path separators")
    work = root / round_name / clip
    if not _inside(work.resolve(), root.resolve()):
        raise ValueError("cache work path resolves outside --scratch-root")
    return work


def validate_and_cleanup(root, work, mp4, telemetry, metadata, expected_rows, cases):
    """Remove only frames_done dirs after all final artifacts prove complete."""
    meta = json.loads(metadata.read_text())
    if meta.get("frames") != expected_rows or [c.get("case") for c in meta.get("cases", [])] != cases:
        raise ValueError("render metadata does not match the completed cases and frame count")
    if sum(c.get("rows", -1) for c in meta["cases"]) != expected_rows:
        raise ValueError("render metadata case rows do not match the final frame count")
    with telemetry.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != expected_rows or [r.get("clip_frame") for r in rows] != [str(i) for i in range(expected_rows)]:
        raise ValueError("telemetry rows are incomplete or out of order")
    if not mp4.is_file() or mp4.stat().st_size == 0:
        raise ValueError("final MP4 is missing or empty")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                            "-show_entries", "stream=codec_name,width,height,nb_read_frames", "-of", "json", str(mp4)],
                           check=True, capture_output=True, text=True)
    streams = json.loads(probe.stdout).get("streams", [])
    if len(streams) != 1 or streams[0].get("codec_name") != "h264" or streams[0].get("width") != 1920 or streams[0].get("height") != 1080 or int(streams[0].get("nb_read_frames", -1)) != expected_rows:
        raise ValueError("final MP4 stream does not match the expected capture")
    root = root.resolve()
    if not _inside(work.resolve(), root):
        raise ValueError("cache work path resolves outside --scratch-root")
    dirs = []
    for name, case_meta in zip(cases, meta["cases"]):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError("unsafe case name")
        frames = work / name / "frames_done"
        if frames.is_symlink() or not frames.is_dir() or not _inside(frames.resolve(), root):
            raise ValueError("unsafe or missing per-case frame cache: " + str(frames))
        if len(list(frames.glob("MovieFrame*.png"))) != case_meta["frames_rendered"]:
            raise ValueError("per-case frame cache is incomplete: " + str(frames))
        dirs.append(frames)
    for frames in dirs:
        shutil.rmtree(frames)
