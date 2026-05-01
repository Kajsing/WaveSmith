"""Generate a small WAV test tone for render smoke tests."""

from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path


def generate_tone(path: Path, seconds: float, sample_rate: int, frequency: float) -> None:
    """Write a mono 16-bit PCM sine tone."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(seconds * sample_rate)
    amplitude = 0.35 * 32767

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for index in range(frame_count):
            fade_frames = sample_rate * 0.05
            envelope = min(1.0, index / fade_frames, (frame_count - index) / fade_frames)
            wave_value = math.sin(math.tau * frequency * index / sample_rate)
            sample = int(amplitude * envelope * wave_value)
            wav.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a WAV test tone.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--sample-rate", type=int, default=44100)
    parser.add_argument("--frequency", type=float, default=440.0)
    args = parser.parse_args()

    if args.seconds <= 0:
        raise SystemExit("--seconds must be greater than 0")
    generate_tone(args.output, args.seconds, args.sample_rate, args.frequency)


if __name__ == "__main__":
    main()
