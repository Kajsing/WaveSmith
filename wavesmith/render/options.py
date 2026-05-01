"""Render option models."""

from dataclasses import dataclass
from pathlib import Path


class RenderOptionsError(ValueError):
    """Raised when render options are invalid."""


@dataclass(frozen=True)
class RenderOptions:
    """Validated options for one render."""

    input_audio: Path
    output_video: Path
    preset: str
    width: int
    height: int
    fps: int
    max_seconds: float | None
    watermark: str | None
    crf: int
    ffmpeg_preset: str
    force_analysis: bool = False


def parse_resolution(value: str) -> tuple[int, int]:
    """Parse a resolution string like 1920x1080."""
    normalized = value.lower().strip()
    if "x" not in normalized:
        raise RenderOptionsError("Resolution must use WIDTHxHEIGHT format, for example 1920x1080.")

    width_text, height_text = normalized.split("x", 1)
    try:
        width = int(width_text)
        height = int(height_text)
    except ValueError as exc:
        raise RenderOptionsError("Resolution width and height must be integers.") from exc

    if width < 16 or height < 16:
        raise RenderOptionsError("Resolution must be at least 16x16.")
    if width % 2 != 0 or height % 2 != 0:
        raise RenderOptionsError("Resolution width and height must be even numbers for MP4 output.")

    return width, height


def build_render_options(
    *,
    input_audio: Path,
    output_video: Path,
    preset: str,
    resolution: str,
    fps: int,
    max_seconds: float | None,
    watermark: str | None,
    crf: int,
    ffmpeg_preset: str,
    force_analysis: bool,
) -> RenderOptions:
    """Validate CLI render values and return normalized options."""
    if not input_audio.exists():
        raise RenderOptionsError(f"Input audio file does not exist: {input_audio}")
    if input_audio.suffix.lower() not in {".mp3", ".wav"}:
        raise RenderOptionsError("Input audio must be an MP3 or WAV file.")
    if output_video.suffix.lower() != ".mp4":
        raise RenderOptionsError("Output video path must end with .mp4.")
    if fps < 1:
        raise RenderOptionsError("FPS must be at least 1.")
    if max_seconds is not None and max_seconds <= 0:
        raise RenderOptionsError("--max-seconds must be greater than 0.")

    width, height = parse_resolution(resolution)

    return RenderOptions(
        input_audio=input_audio,
        output_video=output_video,
        preset=preset,
        width=width,
        height=height,
        fps=fps,
        max_seconds=max_seconds,
        watermark=watermark,
        crf=crf,
        ffmpeg_preset=ffmpeg_preset,
        force_analysis=force_analysis,
    )
