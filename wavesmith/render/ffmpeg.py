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
