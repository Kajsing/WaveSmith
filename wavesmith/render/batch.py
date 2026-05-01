"""Batch rendering helpers."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from wavesmith.render.options import RenderOptions
from wavesmith.render.pipeline import render_video

SUPPORTED_BATCH_EXTENSIONS = {".mp3", ".wav"}


@dataclass(frozen=True)
class BatchItemResult:
    """Result for one batch item."""

    input_audio: str
    output_video: str
    status: str
    thumbnail: str | None = None
    cache_status: str | None = None
    log_path: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class BatchSummary:
    """Batch render summary."""

    total: int
    succeeded: int
    failed: int
    results: list[BatchItemResult]
    summary_path: str


def discover_audio_files(input_dir: Path) -> list[Path]:
    """Find supported audio files in deterministic order."""
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_BATCH_EXTENSIONS
    )


def run_batch(
    *,
    input_dir: Path,
    output_dir: Path,
    preset: str,
    width: int,
    height: int,
    fps: int,
    max_seconds: float | None,
    watermark: str | None,
    crf: int,
    ffmpeg_preset: str,
    backend: str,
    force_analysis: bool,
    thumbnails: bool,
    thumbnail_at: str,
    thumbnail_style: str,
    stop_on_error: bool,
) -> BatchSummary:
    """Render all supported audio files in a directory."""
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    if backend not in {"cpu", "gpu"}:
        raise ValueError("Render backend must be cpu or gpu.")
    if thumbnail_style not in {"frame", "poster"}:
        raise ValueError("Thumbnail style must be frame or poster.")

    output_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_dir = output_dir / "thumbnails"
    audio_files = discover_audio_files(input_dir)
    results: list[BatchItemResult] = []

    for input_audio in audio_files:
        output_video = output_dir / f"{input_audio.stem}.mp4"
        thumbnail_path = thumbnail_dir / f"{input_audio.stem}.jpg" if thumbnails else None
        options = RenderOptions(
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
            backend=backend,
            force_analysis=force_analysis,
            thumbnail=thumbnails,
            thumbnail_at=thumbnail_at,
            thumbnail_style=thumbnail_style,
            thumbnail_path=thumbnail_path,
        )
        try:
            render_result = render_video(options)
        except Exception as exc:
            results.append(
                BatchItemResult(
                    input_audio=str(input_audio),
                    output_video=str(output_video),
                    status="failed",
                    thumbnail=str(thumbnail_path) if thumbnail_path else None,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            if stop_on_error:
                break
        else:
            results.append(
                BatchItemResult(
                    input_audio=str(input_audio),
                    output_video=str(output_video),
                    status="success",
                    thumbnail=str(render_result.thumbnail_path)
                    if render_result.thumbnail_path
                    else None,
                    cache_status=render_result.cache_status,
                    log_path=str(render_result.log_path),
                )
            )

    summary_path = output_dir / "batch-summary.json"
    summary = BatchSummary(
        total=len(results),
        succeeded=sum(1 for result in results if result.status == "success"),
        failed=sum(1 for result in results if result.status == "failed"),
        results=results,
        summary_path=str(summary_path),
    )
    summary_path.write_text(json.dumps(asdict(summary), indent=2) + "\n", encoding="utf-8")
    return summary
