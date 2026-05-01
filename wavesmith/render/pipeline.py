"""Render pipeline orchestration."""

import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from wavesmith.audio.cache import CachedAnalysis, load_or_analyze_audio
from wavesmith.lyrics import LyricCue, active_lyric_text, load_lyrics
from wavesmith.presets.loader import load_preset
from wavesmith.presets.schema import PresetConfig, PresetModule
from wavesmith.render.ffmpeg import (
    build_rawvideo_command,
    encode_raw_frames,
    extract_thumbnail,
    probe_duration_seconds,
)
from wavesmith.render.options import RenderOptions
from wavesmith.timeline.model import Timeline
from wavesmith.utils.logging import render_log_path, write_render_log
from wavesmith.visuals.background import draw_reactive_background
from wavesmith.visuals.base import FrameContext
from wavesmith.visuals.center_orb import draw_center_orb
from wavesmith.visuals.particles import draw_particles
from wavesmith.visuals.shader_field import draw_shader_field
from wavesmith.visuals.spectrum_ring import draw_spectrum_ring
from wavesmith.visuals.text import draw_lyrics, draw_watermark
from wavesmith.visuals.waveform_ribbon import draw_waveform_ribbon


@dataclass(frozen=True)
class RenderResult:
    """Summary of a completed render."""

    duration_seconds: float
    cache_status: str
    cache_path: Path
    log_path: Path
    thumbnail_path: Path | None = None


def render_video(options: RenderOptions) -> RenderResult:
    """Render audio-reactive frames and mux them with the source audio."""
    preset = load_preset(options.preset)
    log_path = render_log_path(options.input_audio)
    duration_seconds: float | None = None
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
        encode_raw_frames(
            command=command,
            frames=generate_reactive_frames(
                options,
                duration_seconds,
                timeline,
                preset,
                lyrics=lyrics,
            ),
        )
        thumbnail_path = _thumbnail_path(options)
        if thumbnail_path:
            extract_thumbnail(
                input_video=options.output_video,
                output_image=thumbnail_path,
                at=options.thumbnail_at,
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
    )
    return RenderResult(
        duration_seconds=duration_seconds,
        cache_status=cached.cache_status,
        cache_path=cached.cache_path,
        log_path=log_path,
        thumbnail_path=_thumbnail_path(options),
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
    frame_count = max(1, math.ceil(duration_seconds * options.fps))
    width = options.width
    height = options.height

    for frame_index in range(frame_count):
        progress = frame_index / max(1, frame_count - 1)
        time_seconds = frame_index / options.fps
        features = timeline.at(time_seconds)
        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        ctx = FrameContext(
            image=image,
            draw=draw,
            width=width,
            height=height,
            time_seconds=time_seconds,
            progress=progress,
            features=features,
            preset_name=preset.name,
            palette_base=preset.palette.base,
            palette_accent=preset.palette.accent,
            palette_beat=preset.palette.beat,
        )

        draw_reactive_background(ctx)
        for module in preset.modules:
            _draw_module(ctx, module)
        draw_lyrics(ctx, active_lyric_text(lyrics, time_seconds, options.lyrics_offset))
        draw_watermark(ctx, _watermark_text(options, preset))

        yield image.tobytes()


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


def _draw_module(ctx: FrameContext, module: PresetModule) -> None:
    if module.type == "center_orb":
        draw_center_orb(ctx, module)
    elif module.type == "spectrum_ring":
        draw_spectrum_ring(ctx, module)
    elif module.type == "waveform_ribbon":
        draw_waveform_ribbon(ctx, module)
    elif module.type == "particles":
        draw_particles(ctx, module)
    elif module.type == "shader_field":
        draw_shader_field(ctx, module)


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
