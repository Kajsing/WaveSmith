import math
import wave
from pathlib import Path


def write_test_tone(path: Path, *, seconds: float = 1.0, sample_rate: int = 22_050) -> None:
    """Write a small mono WAV with two tones and a gentle pulse."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(seconds * sample_rate)
    amplitude = 0.4 * 32767

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for index in range(frame_count):
            time_seconds = index / sample_rate
            pulse = 0.65 + 0.35 * math.sin(math.tau * 2 * time_seconds)
            value = (
                math.sin(math.tau * 110 * time_seconds)
                + 0.45 * math.sin(math.tau * 880 * time_seconds)
            )
            sample = int(amplitude * pulse * value / 1.45)
            wav.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))
