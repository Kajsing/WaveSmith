"""Local poster thumbnail rendering."""

import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from wavesmith.audio.features import AudioAnalysis, TimeSeries
from wavesmith.presets.schema import PresetConfig
from wavesmith.render.ffmpeg import parse_thumbnail_time
from wavesmith.visuals.base import blend_color, feature_float

BEST_THUMBNAIL_TIMES = {"auto", "best", "peak"}


def write_poster_thumbnail(
    *,
    output_image: Path,
    preset: PresetConfig,
    features: dict[str, Any],
    title: str,
    width: int = 1280,
    height: int = 720,
) -> None:
    """Write a designed local poster thumbnail."""
    output_image.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (width, height), (3, 5, 12))
    draw = ImageDraw.Draw(image)
    rms = feature_float(features, "rms")
    bass = feature_float(features, "bass_energy")
    treble = feature_float(features, "treble_energy")

    _draw_gradient(draw, width, height, preset, rms, treble)
    _draw_glow(image, preset, bass, rms)
    _draw_poster_ring(draw, width, height, preset, features, bass, treble)
    _draw_title(draw, width, height, preset, title)
    image.save(output_image, quality=92, optimize=True)


def resolve_thumbnail_time(
    value: str,
    duration_seconds: float,
    analysis: AudioAnalysis,
) -> float:
    """Resolve explicit or audio-reactive thumbnail timing."""
    if value.strip().lower() in BEST_THUMBNAIL_TIMES:
        return choose_reactive_thumbnail_time(analysis, duration_seconds)
    return parse_thumbnail_time(value, duration_seconds)


def choose_reactive_thumbnail_time(
    analysis: AudioAnalysis,
    duration_seconds: float,
) -> float:
    """Pick a musically strong thumbnail time from normalized analysis features."""
    candidate_times = _candidate_times(analysis, duration_seconds)
    if not candidate_times:
        return round(duration_seconds * 0.5, 3)

    if duration_seconds <= 4.0:
        window_start = 0.0
        window_end = duration_seconds
    else:
        margin = min(12.0, duration_seconds * 0.08)
        window_start = margin
        window_end = max(window_start, duration_seconds - margin)

    midpoint = duration_seconds * 0.5
    best_time = min(candidate_times, key=lambda time_seconds: abs(time_seconds - midpoint))
    best_score = -1.0
    for time_seconds in candidate_times:
        if time_seconds < window_start or time_seconds > window_end:
            continue
        score = _thumbnail_score(analysis, time_seconds, duration_seconds)
        if score > best_score:
            best_score = score
            best_time = time_seconds
    return round(max(0.0, min(duration_seconds, best_time)), 3)


def _candidate_times(analysis: AudioAnalysis, duration_seconds: float) -> list[float]:
    for series in (
        analysis.rms,
        analysis.bass_energy,
        analysis.mid_energy,
        analysis.treble_energy,
    ):
        times = [time for time in series.times if 0.0 <= time <= duration_seconds]
        if times:
            return times
    return []


def _thumbnail_score(
    analysis: AudioAnalysis,
    time_seconds: float,
    duration_seconds: float,
) -> float:
    rms = _series_value_at(analysis.rms, time_seconds)
    bass = _series_value_at(analysis.bass_energy, time_seconds)
    mid = _series_value_at(analysis.mid_energy, time_seconds)
    treble = _series_value_at(analysis.treble_energy, time_seconds)
    beat_bonus = _near_event_bonus(time_seconds, analysis.beats, 0.1, 0.1)
    onset_bonus = _near_event_bonus(time_seconds, analysis.onsets, 0.08, 0.05)
    center_position = time_seconds / max(0.001, duration_seconds)
    center_bias = 1.0 - min(0.18, abs(center_position - 0.5) * 0.18)
    score = rms * 0.34 + bass * 0.26 + mid * 0.14 + treble * 0.18
    return (score + beat_bonus + onset_bonus) * center_bias


def _series_value_at(series: TimeSeries, time_seconds: float) -> float:
    if not series.times or not series.values:
        return 0.0
    index = min(
        range(len(series.times)),
        key=lambda candidate: abs(series.times[candidate] - time_seconds),
    )
    value = series.values[index]
    if isinstance(value, list):
        numeric_values = [float(item) for item in value if isinstance(item, int | float)]
        if not numeric_values:
            return 0.0
        return max(0.0, min(1.0, sum(numeric_values) / len(numeric_values)))
    return max(0.0, min(1.0, float(value)))


def _near_event_bonus(
    time_seconds: float,
    events: list[float],
    window_seconds: float,
    amount: float,
) -> float:
    if any(abs(time_seconds - event) <= window_seconds for event in events):
        return amount
    return 0.0


def _draw_gradient(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    preset: PresetConfig,
    rms: float,
    treble: float,
) -> None:
    top = blend_color((4, 6, 18), preset.palette.base, 0.22 + rms * 0.2)
    bottom = blend_color((8, 2, 12), preset.palette.accent, 0.2 + treble * 0.28)
    for y in range(height):
        draw.line((0, y, width, y), fill=blend_color(top, bottom, y / max(1, height - 1)))


def _draw_glow(
    image: Image.Image,
    preset: PresetConfig,
    bass: float,
    rms: float,
) -> None:
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    center = (width * 0.5, height * 0.46)
    for index in range(5, 0, -1):
        radius = int(min(width, height) * (0.18 + index * 0.075 + bass * 0.06))
        amount = index / 5
        color = blend_color(preset.palette.base, preset.palette.accent, 1.0 - amount)
        alpha = int(36 + rms * 54)
        draw.ellipse(
            (
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ),
            fill=(*color, alpha),
        )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=34))
    image.paste(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))


def _draw_poster_ring(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    preset: PresetConfig,
    features: dict[str, Any],
    bass: float,
    treble: float,
) -> None:
    spectrum = features.get("spectrum", [])
    if not isinstance(spectrum, list) or not spectrum:
        spectrum = [0.4] * 96
    spectrum = [float(value) for value in spectrum if isinstance(value, int | float)]
    center_x = width / 2
    center_y = height * 0.46
    base_radius = min(width, height) * (0.22 + bass * 0.08)
    max_bar = min(width, height) * (0.16 + treble * 0.1)
    for index in range(180):
        source_index = round(index / 179 * (len(spectrum) - 1))
        value = max(0.0, min(1.0, spectrum[source_index]))
        angle = index / 180 * math.tau - math.pi / 2
        start_radius = base_radius
        end_radius = base_radius + 12 + value * max_bar
        color = blend_color(preset.palette.accent, preset.palette.beat, value * 0.65)
        draw.line(
            (
                center_x + math.cos(angle) * start_radius,
                center_y + math.sin(angle) * start_radius,
                center_x + math.cos(angle) * end_radius,
                center_y + math.sin(angle) * end_radius,
            ),
            fill=color,
            width=3,
        )


def _draw_title(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    preset: PresetConfig,
    title: str,
) -> None:
    title_font = _font(max(34, width // 24))
    label_font = _font(max(18, width // 58))
    safe_title = title.replace("_", " ").replace("-", " ").strip() or "WaveSmith"
    max_width = int(width * 0.82)
    while _text_width(safe_title, title_font) > max_width and len(safe_title) > 8:
        safe_title = safe_title[:-1].rstrip()
    draw.text(
        (width / 2, height * 0.78),
        safe_title,
        font=title_font,
        fill=preset.palette.beat,
        anchor="mm",
    )
    draw.text(
        (width / 2, height * 0.86),
        f"WaveSmith // {preset.name}",
        font=label_font,
        fill=blend_color(preset.palette.beat, preset.palette.accent, 0.45),
        anchor="mm",
    )


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _text_width(text: str, font: ImageFont.ImageFont) -> int:
    left, _, right, _ = font.getbbox(text)
    return right - left
