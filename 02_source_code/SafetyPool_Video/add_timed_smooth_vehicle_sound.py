#!/usr/bin/env python3
"""Add a smooth everyday-vehicle hum only during active video intervals."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--volume", type=float, default=0.38)
    parser.add_argument(
        "--active",
        action="append",
        default=[],
        metavar="START:END",
        help="Audible interval in seconds; supply once for every active tile.",
    )
    return parser.parse_args()


def duration_of(path: Path) -> float:
    reader = imageio.get_reader(path)
    try:
        metadata = reader.get_meta_data()
        duration = float(metadata.get("duration", 0.0))
        if duration > 0:
            return duration
        return reader.count_frames() / float(metadata["fps"])
    finally:
        reader.close()


def parse_intervals(values: list[str], duration: float) -> list[tuple[float, float]]:
    intervals = []
    for value in values:
        try:
            start_text, end_text = value.split(":", 1)
            start, end = float(start_text), float(end_text)
        except ValueError as exc:
            raise ValueError(f"Invalid --active {value!r}; expected START:END") from exc
        start = max(0.0, start)
        end = min(duration, end)
        if end <= start:
            raise ValueError(f"Invalid active interval: {value}")
        intervals.append((start, end))
    return intervals


def engine_segment(seconds: float, sample_rate: int, volume: float) -> np.ndarray:
    count = max(1, round(seconds * sample_rate))
    time = np.arange(count, dtype=np.float64) / sample_rate
    progress = np.clip(time / max(seconds, 0.001), 0.0, 1.0)
    # Smooth everyday driving: steady low hum with a small speed increase.
    rpm = 72.0 + 34.0 * (0.5 - 0.5 * np.cos(np.pi * progress))
    rpm *= 1.0 + 0.006 * np.sin(2.0 * np.pi * 3.5 * time)
    phase = 2.0 * np.pi * np.cumsum(rpm) / sample_rate
    signal = (
        0.63 * np.sin(phase)
        + 0.23 * np.sin(2.0 * phase)
        + 0.08 * np.sin(3.0 * phase)
        + 0.06 * np.sin(0.5 * phase)
    )
    peak = float(np.max(np.abs(signal)))
    if peak:
        signal /= peak
    fade_count = min(round(0.10 * sample_rate), count // 2)
    if fade_count:
        fade = np.linspace(0.0, 1.0, fade_count)
        signal[:fade_count] *= fade
        signal[-fade_count:] *= fade[::-1]
    return signal * max(0.0, min(volume, 1.0))


def write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype(np.int16)
    stereo = np.column_stack((pcm, pcm)).ravel()
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(stereo.tobytes())


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    duration = duration_of(args.input)
    intervals = parse_intervals(args.active, duration)
    if not intervals:
        raise ValueError("At least one --active START:END interval is required")

    sample_rate = 48_000
    track = np.zeros(round(duration * sample_rate), dtype=np.float64)
    for start, end in intervals:
        first = round(start * sample_rate)
        segment = engine_segment(end - start, sample_rate, args.volume)
        last = min(len(track), first + len(segment))
        track[first:last] += segment[: last - first]
    track = np.clip(track, -1.0, 1.0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix="safetypool_timed_audio_") as directory:
        wav_path = Path(directory) / "timed_engine.wav"
        write_wav(wav_path, track, sample_rate)
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(args.input),
                "-i",
                str(wav_path),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(args.output),
            ],
            check=True,
        )
    print(f"Timed-audio video: {args.output.resolve()}")


if __name__ == "__main__":
    main()
