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
    cache_status: str | None,
    cache_path: Path | None,
    ffmpeg_command: list[str] | None,
    thumbnail_path: Path | None = None,
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
        f"analysis_cache_status={cache_status}",
        f"analysis_cache_path={cache_path}",
        f"thumbnail_path={thumbnail_path}",
    ]
    if ffmpeg_command:
        lines.append(f"ffmpeg_command={shlex.join(ffmpeg_command)}")
    if error:
        lines.append(f"error_type={type(error).__name__}")
        lines.append(f"error={error}")
        lines.append("traceback:")
        lines.extend(traceback.format_exception(type(error), error, error.__traceback__))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
