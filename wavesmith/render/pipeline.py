"""Render pipeline orchestration."""

import math
from collections.abc import Iterator

from PIL import Image, ImageDraw

from wavesmith.audio.analyzer import analyze_audio
from wavesmith.presets.loader import load_preset
from wavesmith.render.ffmpeg import (
    build_rawvideo_command,
    encode_raw_frames,
    probe_duration_seconds,
)
from wavesmith.render.options import RenderOptions
from wavesmith.timeline.model import Timeline
from wavesmith.visuals.background import draw_reactive_background
from wavesmith.visuals.base import FrameContext
from wavesmith.visuals.center_orb import draw_center_orb
from wavesmith.visuals.spectrum_ring import draw_spectrum_ring
from wavesmith.visuals.text import draw_watermark
from wavesmith.visuals.waveform_ribbon import draw_waveform_ribbon


def render_video(options: RenderOptions) -> float:
    """Render audio-reactive frames and mux them with the source audio."""
    load_preset(options.preset)
    source_duration = probe_duration_seconds(options.input_audio)
    duration_seconds = min(source_duration, options.max_seconds or source_duration)
    analysis = analyze_audio(options.input_audio, feature_fps=max(options.fps, 20))
    timeline = Timeline(analysis)

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
        frames=generate_reactive_frames(options, duration_seconds, timeline),
    )
    return duration_seconds


def generate_reactive_frames(
    options: RenderOptions,
    duration_seconds: float,
    timeline: Timeline,
) -> Iterator[bytes]:
    """Yield RGB frames driven by timeline features."""
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
            draw=draw,
            width=width,
            height=height,
            time_seconds=time_seconds,
            progress=progress,
            features=features,
            preset_name=options.preset,
        )

        draw_reactive_background(ctx)
        draw_spectrum_ring(ctx)
        draw_center_orb(ctx)
        draw_waveform_ribbon(ctx)
        draw_watermark(ctx, options.watermark)

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
