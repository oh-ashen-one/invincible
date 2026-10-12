#!/usr/bin/env python3
"""Prepare the owner-supplied track for a continuous UE loop; requires ffmpeg only.

From the repo root: python3 -B tools/audio/prepare_background_music.py
The original MP3 stays untouched. Generated WAV/metadata live under Unreal's ignored Saved/ directory.
Trim quiet ends only, then overlap the tail and head with a 0.4 s raised-cosine crossfade.
Rotating the loop starts it after the overlapped head and makes its file boundary adjacent source samples.
"""
from array import array
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[2]
RATE = 48000
CHANNELS = 2


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(source, output, crossfade_seconds=0.4, quiet_db=-48.0, pad_seconds=0.04):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to decode the MP3 and write PCM16 WAV")
    if not source.is_file():
        raise FileNotFoundError(source)
    if output.resolve() == source.resolve():
        raise ValueError("Output must differ from the original track")
    decoded = subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-i", str(source), "-map", "0:a:0", "-vn",
         "-ac", str(CHANNELS), "-ar", str(RATE), "-f", "f32le", "pipe:1"],
        capture_output=True, check=True,
    )
    samples = array("f")
    samples.frombytes(decoded.stdout)
    del decoded
    if sys.byteorder != "little":
        samples.byteswap()
    frames = len(samples) // CHANNELS
    if frames < RATE:
        raise ValueError("Expected a music track longer than one second")
    threshold = 10 ** (quiet_db / 20.0)
    block = RATE // 100  # 10 ms peak windows; trim silence at the ends, never internal musical pauses.
    start, end = 0, frames

    def quiet(first, last):
        return max((abs(v) for v in samples[first * CHANNELS:last * CHANNELS]), default=0.0) < threshold

    while start < end and quiet(start, min(start + block, end)):
        start += block
    while end > start and quiet(max(start, end - block), end):
        end -= block
    if start >= end:
        raise ValueError("The decoded track is entirely quiet at the chosen threshold")
    pad = round(pad_seconds * RATE)
    start, end = max(0, start - pad), min(frames, end + pad)
    trimmed = samples[start * CHANNELS:end * CHANNELS]
    del samples
    overlap = round(crossfade_seconds * RATE)
    if overlap < 2 or overlap * 4 >= end - start:
        raise ValueError("Crossfade must be at least two samples and shorter than one quarter of the track")
    join = array("f", [0.0]) * (overlap * CHANNELS)
    tail = len(trimmed) - overlap * CHANNELS
    for frame in range(overlap):
        head_weight = 0.5 - 0.5 * math.cos(math.pi * frame / (overlap - 1))
        for channel in range(CHANNELS):
            i = frame * CHANNELS + channel
            join[i] = trimmed[tail + i] * (1.0 - head_weight) + trimmed[i] * head_weight
    loop = trimmed[overlap * CHANNELS:tail]
    loop.extend(join)
    del trimmed, join
    peak = max(abs(v) for v in loop)
    gain = min(1.0, 0.999 / max(peak, 1e-12))  # A convex crossfade adds no gain; protect MP3 overshoots only.
    boundary_step = max(abs(loop[-CHANNELS + c] - loop[c]) for c in range(CHANNELS)) * gain
    if sys.byteorder != "little":
        loop.byteswap()
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(RATE),
         "-ac", str(CHANNELS), "-i", "pipe:0", "-af", f"volume={gain:.12g}",
         "-c:a", "pcm_s16le", "-map_metadata", "-1", str(output)],
        input=loop.tobytes(), check=True,
    )
    with wave.open(str(output), "rb") as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (RATE, CHANNELS, 2):
            raise RuntimeError("Prepared audio is not 48 kHz stereo PCM16")
        output_frames = wav.getnframes()
    metadata = {
        "source": str(source.resolve()), "source_sha256": sha256(source),
        "output": str(output.resolve()), "output_sha256": sha256(output),
        "sample_rate": RATE, "channels": CHANNELS, "sample_width_bytes": 2,
        "source_decoded_seconds": frames / RATE, "trim_start_seconds": start / RATE,
        "trim_end_seconds": end / RATE, "quiet_threshold_db": quiet_db,
        "quiet_padding_seconds": pad_seconds, "crossfade_seconds": overlap / RATE,
        "crossfade_curve": "raised cosine, complementary weights",
        "loop_rotation_seconds": overlap / RATE, "loop_frames": output_frames,
        "loop_seconds": output_frames / RATE, "peak_before_gain": peak,
        "gain_applied": gain, "loop_boundary_step_peak": boundary_step,
    }
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "assets/audio/Curious Groove.mp3")
    parser.add_argument("--output", type=Path, default=ROOT / "unreal/WebHomage/Saved/AudioImport/CuriousGroove_Loop.wav")
    parser.add_argument("--crossfade-seconds", type=float, default=0.4)
    args = parser.parse_args()
    metadata = prepare(args.source, args.output, args.crossfade_seconds)
    print("WH_BACKGROUND_MUSIC_PREPARED " + json.dumps(metadata, sort_keys=True))


if __name__ == "__main__":
    main()
