"""Preset comparison rendering helpers."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from wavesmith.render.options import RenderOptions
from wavesmith.render.pipeline import render_video


@dataclass(frozen=True)
class CompareItemResult:
    """Result for one preset comparison render."""

    preset: str
    output_video: str
    status: str
    thumbnail: str | None = None
    cache_status: str | None = None
    log_path: str | None = None
    backend: str | None = None
    encode_elapsed_seconds: float | None = None
    effective_fps: float | None = None
    output_size_bytes: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class CompareSummary:
    """Summary for a preset comparison run."""

    input_audio: str
    output_dir: str
    total: int
    succeeded: int
    failed: int
    results: list[CompareItemResult]
    summary_path: str


def run_compare(
    *,
    input_audio: Path,
    output_dir: Path,
    presets: list[str],
    width: int,
    height: int,
    fps: int,
    seconds: float,
    watermark: str | None,
    crf: int,
    ffmpeg_preset: str,
    backend: str,
    force_analysis: bool,
    thumbnails: bool,
    thumbnail_at: str,
    thumbnail_style: str,
    stop_on_error: bool,
) -> CompareSummary:
    """Render the same audio through multiple presets and write a JSON summary."""
    if not input_audio.exists():
        raise ValueError(f"Input audio file does not exist: {input_audio}")
    if input_audio.suffix.lower() not in {".mp3", ".wav"}:
        raise ValueError("Input audio must be an MP3 or WAV file.")
    if not presets:
        raise ValueError("At least one preset is required.")
    if backend not in {"cpu", "gpu"}:
        raise ValueError("Render backend must be cpu or gpu.")
    if thumbnail_style not in {"frame", "poster"}:
        raise ValueError("Thumbnail style must be frame or poster.")

    output_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_dir = output_dir / "thumbnails"
    results: list[CompareItemResult] = []

    for preset in presets:
        output_video = output_dir / f"{input_audio.stem}-{_safe_slug(preset)}.mp4"
        thumbnail_path = thumbnail_dir / f"{input_audio.stem}-{_safe_slug(preset)}.jpg"
        options = RenderOptions(
            input_audio=input_audio,
            output_video=output_video,
            preset=preset,
            width=width,
            height=height,
            fps=fps,
            max_seconds=seconds,
            watermark=watermark,
            crf=crf,
            ffmpeg_preset=ffmpeg_preset,
            backend=backend,
            force_analysis=force_analysis,
            thumbnail=thumbnails,
            thumbnail_at=thumbnail_at,
            thumbnail_style=thumbnail_style,
            thumbnail_path=thumbnail_path if thumbnails else None,
        )
        try:
            render_result = render_video(options)
        except Exception as exc:
            results.append(
                CompareItemResult(
                    preset=preset,
                    output_video=str(output_video),
                    status="failed",
                    thumbnail=str(thumbnail_path) if thumbnails else None,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            if stop_on_error:
                break
        else:
            results.append(
                CompareItemResult(
                    preset=preset,
                    output_video=str(output_video),
                    status="success",
                    thumbnail=str(render_result.thumbnail_path)
                    if render_result.thumbnail_path
                    else None,
                    cache_status=render_result.cache_status,
                    log_path=str(render_result.log_path),
                    backend=render_result.backend,
                    encode_elapsed_seconds=render_result.encode_elapsed_seconds,
                    effective_fps=render_result.effective_fps,
                    output_size_bytes=render_result.output_size_bytes,
                )
            )

    summary_path = output_dir / "compare-summary.json"
    summary = CompareSummary(
        input_audio=str(input_audio),
        output_dir=str(output_dir),
        total=len(results),
        succeeded=sum(1 for result in results if result.status == "success"),
        failed=sum(1 for result in results if result.status == "failed"),
        results=results,
        summary_path=str(summary_path),
    )
    summary_path.write_text(json.dumps(asdict(summary), indent=2) + "\n", encoding="utf-8")
    return summary


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    return slug.strip("-") or "preset"
