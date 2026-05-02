"""Render pipeline orchestration."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from wavesmith.audio.cache import CachedAnalysis, load_or_analyze_audio
from wavesmith.lyrics import LyricCue, load_lyrics
from wavesmith.presets.loader import load_preset
from wavesmith.presets.schema import PresetConfig
from wavesmith.render.backends import CpuRenderBackend, get_render_backend
from wavesmith.render.ffmpeg import (
    build_rawvideo_command,
    encode_raw_frames,
    extract_thumbnail,
    probe_duration_seconds,
)
from wavesmith.render.options import RenderOptions
from wavesmith.render.thumbnail import resolve_thumbnail_time, write_poster_thumbnail
from wavesmith.timeline.model import Timeline
from wavesmith.utils.logging import render_log_path, write_render_log


@dataclass(frozen=True)
class RenderResult:
    """Summary of a completed render."""

    duration_seconds: float
    cache_status: str
    cache_path: Path
    log_path: Path
    thumbnail_path: Path | None = None
    thumbnail_time_seconds: float | None = None


def render_video(options: RenderOptions) -> RenderResult:
    """Render audio-reactive frames and mux them with the source audio."""
    preset = load_preset(options.preset)
    log_path = render_log_path(options.input_audio)
    duration_seconds: float | None = None
    thumbnail_time: float | None = None
    cached: CachedAnalysis | None = None
    command: list[str] | None = None
    try:
        source_duration = probe_duration_seconds(options.input_audio)
        duration_seconds = min(source_duration, options.max_seconds or source_duration)
        cached = load_or_analyze_audio(
            options.input_audio,
            force=options.force_analysis,
            feature_fps=max(options.fps, 20),
        )
        timeline = Timeline(cached.analysis)
        lyrics = load_lyrics(options.lyrics_path) if options.lyrics_path else []

        options.output_video.parent.mkdir(parents=True, exist_ok=True)
        command = build_rawvideo_command(
            input_audio=options.input_audio,
            output_video=options.output_video,
            width=options.width,
            height=options.height,
            fps=options.fps,
            duration_seconds=duration_seconds,
            crf=options.crf,
            ffmpeg_preset=options.ffmpeg_preset,
        )
        backend = get_render_backend(options.backend)
        encode_raw_frames(
            command=command,
            frames=backend.generate_frames(
                options=options,
                duration_seconds=duration_seconds,
                timeline=timeline,
                preset=preset,
                lyrics=lyrics,
                watermark_text=_watermark_text(options, preset),
            ),
        )
        thumbnail_path = _thumbnail_path(options)
        if thumbnail_path:
            thumbnail_time = resolve_thumbnail_time(
                options.thumbnail_at,
                duration_seconds,
                cached.analysis,
            )
            if options.thumbnail_style == "poster":
                write_poster_thumbnail(
                    output_image=thumbnail_path,
                    preset=preset,
                    features=timeline.at(thumbnail_time),
                    title=options.input_audio.stem,
                )
            else:
                extract_thumbnail(
                    input_video=options.output_video,
                    output_image=thumbnail_path,
                    at=f"{thumbnail_time:.3f}s",
                    duration_seconds=duration_seconds,
                )
    except Exception as exc:
        write_render_log(
            path=log_path,
            status="failed",
            input_audio=options.input_audio,
            output_video=options.output_video,
            preset=preset.name,
            duration_seconds=duration_seconds,
            resolution=f"{options.width}x{options.height}",
            fps=options.fps,
            cache_status=cached.cache_status if cached else None,
            cache_path=cached.cache_path if cached else None,
            ffmpeg_command=command,
            thumbnail_path=_thumbnail_path(options),
            thumbnail_time_seconds=thumbnail_time,
            error=exc,
        )
        raise

    write_render_log(
        path=log_path,
        status="success",
        input_audio=options.input_audio,
        output_video=options.output_video,
        preset=preset.name,
        duration_seconds=duration_seconds,
        resolution=f"{options.width}x{options.height}",
        fps=options.fps,
        cache_status=cached.cache_status,
        cache_path=cached.cache_path,
        ffmpeg_command=command,
        thumbnail_path=_thumbnail_path(options),
        thumbnail_time_seconds=thumbnail_time,
    )
    return RenderResult(
        duration_seconds=duration_seconds,
        cache_status=cached.cache_status,
        cache_path=cached.cache_path,
        log_path=log_path,
        thumbnail_path=_thumbnail_path(options),
        thumbnail_time_seconds=thumbnail_time,
    )


def generate_reactive_frames(
    options: RenderOptions,
    duration_seconds: float,
    timeline: Timeline,
    preset: PresetConfig | None = None,
    lyrics: list[LyricCue] | None = None,
) -> Iterator[bytes]:
    """Yield RGB frames driven by timeline features."""
    preset = preset or load_preset(options.preset)
    lyrics = lyrics or []
    yield from CpuRenderBackend().generate_frames(
        options=options,
        duration_seconds=duration_seconds,
        timeline=timeline,
        preset=preset,
        lyrics=lyrics,
        watermark_text=_watermark_text(options, preset),
    )


def generate_placeholder_frames(
    options: RenderOptions,
    duration_seconds: float,
) -> Iterator[bytes]:
    """Yield deterministic frames for older tests and fallback diagnostics."""
    from wavesmith.audio.features import AudioAnalysis, TimeSeries

    scalar = TimeSeries(times=[0.0, duration_seconds], values=[0.25, 0.75])
    vector = TimeSeries(
        times=[0.0, duration_seconds],
        values=[[0.1, 0.3, 0.5, 0.7], [0.7, 0.5, 0.3, 0.1]],
    )
    analysis = AudioAnalysis(
        duration_seconds=duration_seconds,
        sample_rate=22_050,
        tempo_bpm=0.0,
        beats=[],
        onsets=[],
        rms=scalar,
        bass_energy=scalar,
        mid_energy=scalar,
        treble_energy=scalar,
        spectrum=vector,
        waveform_preview=vector,
    )
    yield from generate_reactive_frames(options, duration_seconds, Timeline(analysis))


def _watermark_text(options: RenderOptions, preset: PresetConfig) -> str | None:
    if options.watermark is not None:
        return options.watermark
    if preset.watermark and preset.watermark.enabled:
        return preset.watermark.text
    return ""


def _thumbnail_path(options: RenderOptions) -> Path | None:
    if not options.thumbnail:
        return None
    if options.thumbnail_path:
        return options.thumbnail_path
    return Path(".renders/thumbnails") / f"{options.output_video.stem}.jpg"
