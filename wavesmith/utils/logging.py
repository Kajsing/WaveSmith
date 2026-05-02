"""Logging utilities."""

import shlex
import traceback
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_RENDER_LOG_DIR = Path(".renders/logs")


def render_log_path(input_audio: Path, *, log_dir: Path = DEFAULT_RENDER_LOG_DIR) -> Path:
    """Create a deterministic-ish per-render log path."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return log_dir / f"{timestamp}-{input_audio.stem}.log"


def write_render_log(
    *,
    path: Path,
    status: str,
    input_audio: Path,
    output_video: Path,
    preset: str,
    duration_seconds: float | None,
    resolution: str,
    fps: int,
    backend: str | None = None,
    crf: int | None = None,
    ffmpeg_preset: str | None = None,
    frame_count: int | None = None,
    total_elapsed_seconds: float | None = None,
    encode_elapsed_seconds: float | None = None,
    effective_fps: float | None = None,
    output_size_bytes: int | None = None,
    cache_status: str | None = None,
    cache_path: Path | None = None,
    ffmpeg_command: list[str] | None = None,
    thumbnail_path: Path | None = None,
    thumbnail_time_seconds: float | None = None,
    error: BaseException | None = None,
) -> None:
    """Write a plain-text render log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"status={status}",
        f"input_audio={input_audio}",
        f"output_video={output_video}",
        f"preset={preset}",
        f"duration_seconds={duration_seconds}",
        f"resolution={resolution}",
        f"fps={fps}",
        f"backend={backend}",
        f"crf={crf}",
        f"ffmpeg_preset={ffmpeg_preset}",
        f"frame_count={frame_count}",
        f"total_elapsed_seconds={total_elapsed_seconds}",
        f"encode_elapsed_seconds={encode_elapsed_seconds}",
        f"effective_fps={effective_fps}",
        f"output_size_bytes={output_size_bytes}",
        f"analysis_cache_status={cache_status}",
        f"analysis_cache_path={cache_path}",
        f"thumbnail_path={thumbnail_path}",
        f"thumbnail_time_seconds={thumbnail_time_seconds}",
    ]
    if ffmpeg_command:
        lines.append(f"ffmpeg_command={shlex.join(ffmpeg_command)}")
    if error:
        lines.append(f"error_type={type(error).__name__}")
        lines.append(f"error={error}")
        lines.append("traceback:")
        lines.extend(traceback.format_exception(type(error), error, error.__traceback__))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
