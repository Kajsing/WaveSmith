"""Local poster thumbnail rendering."""

import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from wavesmith.presets.schema import PresetConfig
from wavesmith.visuals.base import blend_color, feature_float


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
