"""Render pipeline orchestration."""

import math
from collections.abc import Iterator

from PIL import Image, ImageDraw, ImageFont

from wavesmith.presets.loader import load_preset
from wavesmith.render.ffmpeg import (
    build_rawvideo_command,
    encode_raw_frames,
    probe_duration_seconds,
)
from wavesmith.render.options import RenderOptions


def render_video(options: RenderOptions) -> float:
    """Render deterministic placeholder frames and mux them with the source audio."""
    load_preset(options.preset)
    source_duration = probe_duration_seconds(options.input_audio)
    duration_seconds = min(source_duration, options.max_seconds or source_duration)

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
        frames=generate_placeholder_frames(options, duration_seconds),
    )
    return duration_seconds


def generate_placeholder_frames(
    options: RenderOptions,
    duration_seconds: float,
) -> Iterator[bytes]:
    """Yield RGB frames for the M1 smoke renderer."""
    frame_count = max(1, math.ceil(duration_seconds * options.fps))
    width = options.width
    height = options.height
    font = ImageFont.load_default()

    for frame_index in range(frame_count):
        progress = frame_index / max(1, frame_count - 1)
        time_seconds = frame_index / options.fps
        image = Image.new("RGB", (width, height), _background_color(options.preset, progress))
        draw = ImageDraw.Draw(image)

        _draw_grid(draw, width, height, progress)
        _draw_orb(draw, width, height, progress, time_seconds, options.preset)
        _draw_ribbon(draw, width, height, progress, time_seconds)

        if options.watermark != "":
            watermark = options.watermark or "WaveSmith"
            draw.text(
                (width - 12, height - 18),
                watermark,
                fill=(230, 235, 240),
                font=font,
                anchor="rd",
            )

        yield image.tobytes()


def _background_color(preset: str, progress: float) -> tuple[int, int, int]:
    palette = {
        "neon_orb": (8, 5, 18),
        "spectrum_ring": (3, 8, 14),
        "waveform_ribbon": (14, 7, 9),
    }
    base = palette.get(preset, (6, 6, 10))
    pulse = int(12 * (0.5 + 0.5 * math.sin(progress * math.tau)))
    return (min(255, base[0] + pulse), min(255, base[1] + pulse // 2), min(255, base[2] + pulse))


def _draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int, progress: float) -> None:
    spacing = max(32, min(width, height) // 12)
    offset = int(progress * spacing)
    color = (18, 30, 44)
    for x in range(-spacing + offset, width, spacing):
        draw.line((x, 0, x, height), fill=color)
    for y in range(-spacing + offset, height, spacing):
        draw.line((0, y, width, y), fill=color)


def _draw_orb(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    progress: float,
    time_seconds: float,
    preset: str,
) -> None:
    center_x = width // 2
    center_y = height // 2
    base_radius = min(width, height) * 0.13
    pulse = 1.0 + 0.18 * math.sin(time_seconds * math.tau * 1.5)
    radius = int(base_radius * pulse)
    accent = {
        "neon_orb": (95, 220, 255),
        "spectrum_ring": (255, 80, 180),
        "waveform_ribbon": (255, 165, 95),
    }.get(preset, (150, 210, 255))

    for ring in range(4, 0, -1):
        ring_radius = radius + ring * 18
        alpha = 45 + ring * 12
        color = tuple(min(255, channel + alpha) for channel in accent)
        draw.ellipse(
            (
                center_x - ring_radius,
                center_y - ring_radius,
                center_x + ring_radius,
                center_y + ring_radius,
            ),
            outline=color,
            width=max(1, ring),
        )

    wobble = int(12 * math.sin(progress * math.tau * 3))
    draw.ellipse(
        (
            center_x - radius - wobble,
            center_y - radius,
            center_x + radius + wobble,
            center_y + radius,
        ),
        fill=accent,
        outline=(245, 248, 255),
        width=2,
    )


def _draw_ribbon(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    progress: float,
    time_seconds: float,
) -> None:
    points: list[tuple[int, int]] = []
    baseline = int(height * 0.78)
    amplitude = max(12, int(height * 0.07))
    step = max(4, width // 160)
    for x in range(0, width + step, step):
        phase = (x / width) * math.tau * 4 + time_seconds * math.tau * 0.8
        y = baseline + int(math.sin(phase) * amplitude * (0.55 + 0.45 * progress))
        points.append((x, y))

    if len(points) > 1:
        draw.line(points, fill=(255, 245, 210), width=max(2, height // 160))
