"""ffmpeg integration."""

import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path


class FfmpegMissingError(RuntimeError):
    """Raised when ffmpeg or ffprobe is unavailable."""


class FfmpegRenderError(RuntimeError):
    """Raised when ffmpeg fails during rendering."""


def require_binary(name: str) -> str:
    """Return the path to a required binary."""
    binary = shutil.which(name)
    if binary is None:
        raise FfmpegMissingError(f"Required binary was not found on PATH: {name}")
    return binary


def probe_duration_seconds(input_audio: Path) -> float:
    """Read audio duration with ffprobe."""
    ffprobe = require_binary("ffprobe")
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_audio),
    ]
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise FfmpegRenderError(result.stderr.strip() or "ffprobe could not read audio duration.")

    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise FfmpegRenderError("ffprobe returned an invalid duration.") from exc

    if duration <= 0:
        raise FfmpegRenderError("Input audio duration must be greater than zero.")
    return duration


def verify_media_streams(output_video: Path) -> tuple[bool, bool]:
    """Return whether a media file contains at least one video and one audio stream."""
    ffprobe = require_binary("ffprobe")
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "csv=p=0",
        str(output_video),
    ]
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise FfmpegRenderError(result.stderr.strip() or "ffprobe could not read media streams.")

    stream_types = {line.strip() for line in result.stdout.splitlines()}
    return "video" in stream_types, "audio" in stream_types


def build_rawvideo_command(
    *,
    input_audio: Path,
    output_video: Path,
    width: int,
    height: int,
    fps: int,
    duration_seconds: float,
    crf: int,
    ffmpeg_preset: str,
) -> list[str]:
    """Build the ffmpeg command used for raw RGB frame streaming."""
    ffmpeg = require_binary("ffmpeg")
    return [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-i",
        str(input_audio),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-t",
        f"{duration_seconds:.3f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        str(crf),
        "-preset",
        ffmpeg_preset,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(output_video),
    ]


def parse_thumbnail_time(value: str, duration_seconds: float) -> float:
    """Parse thumbnail time as seconds, percent, or a named position."""
    normalized = value.strip().lower()
    named_positions = {
        "start": 0.0,
        "intro": 0.12,
        "middle": 0.5,
        "center": 0.5,
        "end": 0.88,
        "outro": 0.88,
    }
    if normalized in named_positions:
        return max(0.0, min(duration_seconds, duration_seconds * named_positions[normalized]))

    if normalized.endswith("%"):
        try:
            percent = float(normalized[:-1])
        except ValueError as exc:
            raise FfmpegRenderError("Thumbnail percent must be numeric.") from exc
        if percent < 0 or percent > 100:
            raise FfmpegRenderError("Thumbnail percent must be between 0 and 100.")
        return max(0.0, min(duration_seconds, duration_seconds * percent / 100))

    if normalized.endswith("s"):
        normalized = normalized[:-1]
    try:
        seconds = float(normalized)
    except ValueError as exc:
        raise FfmpegRenderError(
            "Thumbnail time must be seconds, a percent like 50%, or start/intro/middle/end."
        ) from exc
    if seconds < 0:
        raise FfmpegRenderError("Thumbnail time must be greater than or equal to 0.")
    return max(0.0, min(duration_seconds, seconds))


def extract_thumbnail(
    *,
    input_video: Path,
    output_image: Path,
    at: str,
    duration_seconds: float,
) -> None:
    """Extract a local JPG thumbnail from a rendered video."""
    ffmpeg = require_binary("ffmpeg")
    output_image.parent.mkdir(parents=True, exist_ok=True)
    timestamp = parse_thumbnail_time(at, duration_seconds)
    command = [
        ffmpeg,
        "-y",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        str(input_video),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_image),
    ]
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise FfmpegRenderError(result.stderr.strip() or "ffmpeg could not extract thumbnail.")


def encode_raw_frames(
    *,
    command: list[str],
    frames: Iterable[bytes],
) -> None:
    """Stream raw RGB frames to ffmpeg."""
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None

    try:
        for frame in frames:
            process.stdin.write(frame)
    except BrokenPipeError as exc:
        _, stderr = process.communicate()
        raise FfmpegRenderError(stderr.decode("utf-8", errors="replace").strip()) from exc
    except Exception:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise
    finally:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()

    stdout = process.stdout.read() if process.stdout else b""
    stderr = process.stderr.read() if process.stderr else b""
    return_code = process.wait()

    if return_code != 0:
        details = stderr.decode("utf-8", errors="replace").strip()
        if not details:
            details = stdout.decode("utf-8", errors="replace").strip()
        raise FfmpegRenderError(details or f"ffmpeg failed with exit code {return_code}.")
