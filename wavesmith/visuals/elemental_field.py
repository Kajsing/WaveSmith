"""Elemental CPU visual fields."""

import math

from PIL import Image, ImageDraw, ImageFilter

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float


def draw_elemental_field(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw fire, water, plasma, or ice inspired audio-reactive fields."""
    module_config = module.model_extra or {} if module else {}
    element = str(module_config.get("element", "plasma"))
    opacity = _clamp(float(module_config.get("opacity", 0.55)), 0.0, 1.0)
    density = max(8, min(int(module_config.get("density", 42)), 100))
    bands = max(1, min(int(module_config.get("bands", 5)), 10))
    blur = max(0.0, min(float(module_config.get("blur", 5)), 20.0))
    intensity = feature_float(ctx.features, str(module_config.get("intensity_feature", "rms")))
    bass = feature_float(ctx.features, str(module_config.get("bass_feature", "bass_energy")))
    treble = feature_float(ctx.features, str(module_config.get("motion_feature", "treble_energy")))
    beat = 1.0 if ctx.features.get(str(module_config.get("beat_feature", "beat"))) else 0.0

    overlay = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    palette = _element_palette(ctx, element)
    if element == "fire":
        _draw_fire(ctx, draw, palette, bands, density, opacity, intensity, bass, treble, beat)
    elif element == "water":
        _draw_water(ctx, draw, palette, bands, density, opacity, intensity, bass, treble, beat)
    elif element == "ice":
        _draw_ice(ctx, draw, palette, bands, density, opacity, intensity, bass, treble, beat)
    elif element == "lightning":
        _draw_lightning(ctx, draw, palette, bands, density, opacity, intensity, bass, treble, beat)
    else:
        _draw_plasma(ctx, draw, palette, bands, density, opacity, intensity, bass, treble, beat)

    if blur:
        soft = overlay.filter(ImageFilter.GaussianBlur(radius=blur * (0.55 + intensity * 0.45)))
        overlay = Image.alpha_composite(soft, overlay)

    composited = Image.alpha_composite(ctx.image.convert("RGBA"), overlay)
    ctx.image.paste(composited.convert("RGB"))


def _draw_fire(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    bands: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    floor = ctx.height * (0.93 - beat * 0.05)
    flame_height = ctx.height * (0.34 + bass * 0.22 + beat * 0.16)
    for band in range(bands):
        points: list[tuple[float, float]] = []
        phase = ctx.time_seconds * (1.4 + treble * 1.8) + band * 0.9
        for index in range(density + 1):
            amount = index / density
            x = amount * ctx.width
            lick = math.sin(amount * math.tau * (2.0 + band * 0.35) + phase)
            lick += math.sin(amount * math.tau * (6.0 + treble * 3.0) - phase * 1.3) * 0.36
            y = floor - flame_height * (0.28 + band / bands * 0.72) * (0.72 + lick * 0.22)
            points.append((x, y))
        color = _rgba(_blend3(palette, band / max(1, bands - 1)), opacity, intensity, beat, band)
        draw.line(points, fill=color, width=max(3, ctx.height // 55), joint="curve")


def _draw_water(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    bands: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    base_y = ctx.height * (0.55 + math.sin(ctx.time_seconds * 0.23) * 0.04)
    amplitude = ctx.height * (0.09 + bass * 0.17 + beat * 0.04)
    for band in range(bands):
        points: list[tuple[float, float]] = []
        phase = ctx.time_seconds * (0.55 + band * 0.13 + treble * 0.35) + band
        for index in range(density + 1):
            amount = index / density
            x = amount * ctx.width
            wave = math.sin(amount * math.tau * (1.0 + band * 0.28) + phase)
            ripple = math.sin(amount * math.tau * (4.0 + treble * 2.0) - phase)
            y = base_y + (band - bands / 2) * ctx.height * 0.035
            y += wave * amplitude + ripple * amplitude * 0.23
            points.append((x, y))
        color = _rgba(_blend3(palette, band / max(1, bands - 1)), opacity, intensity, beat, band)
        draw.line(points, fill=color, width=max(2, ctx.height // 70), joint="curve")


def _draw_ice(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    bands: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    center_x = ctx.width / 2
    center_y = ctx.height / 2
    radius = min(ctx.width, ctx.height) * (0.24 + bass * 0.11 + beat * 0.06)
    count = max(24, density)
    for index in range(count):
        angle = index / count * math.tau + ctx.time_seconds * (0.05 + treble * 0.12)
        shard = radius * (0.55 + (index % max(2, bands)) / max(1, bands) * 0.7)
        wobble = math.sin(index * 1.7 + ctx.time_seconds * 1.3) * radius * 0.08
        length = radius * (0.24 + intensity * 0.24 + (index % 3) * 0.04)
        start = (
            center_x + math.cos(angle) * (shard + wobble),
            center_y + math.sin(angle) * (shard + wobble),
        )
        end = (
            center_x + math.cos(angle) * (shard + length + wobble),
            center_y + math.sin(angle) * (shard + length + wobble),
        )
        color = _rgba(
            _blend3(palette, (index % bands) / max(1, bands - 1)),
            opacity,
            intensity,
            beat,
            index,
        )
        draw.line((*start, *end), fill=color, width=max(1, ctx.height // 110))


def _draw_plasma(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    bands: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    center_x = ctx.width / 2
    center_y = ctx.height / 2
    spread = min(ctx.width, ctx.height) * (0.24 + bass * 0.18 + beat * 0.08)
    count = max(18, density)
    for index in range(count):
        orbit = index / count
        angle = orbit * math.tau * 3.0 + ctx.time_seconds * (0.65 + treble)
        radius = spread * (0.35 + orbit * 0.9)
        x = center_x + math.cos(angle + math.sin(index)) * radius
        y = center_y + math.sin(angle * 0.8) * radius * 0.72
        size = min(ctx.width, ctx.height) * (0.012 + intensity * 0.025 + (index % 4) * 0.004)
        color = _rgba(
            _blend3(palette, (index % bands) / max(1, bands - 1)),
            opacity,
            intensity,
            beat,
            index,
        )
        draw.ellipse((x - size, y - size, x + size, y + size), fill=color)


def _draw_lightning(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    bands: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    count = max(3, min(bands + int(treble * 5) + int(beat * 4), 12))
    segments = max(5, min(density // 4, 18))
    reach = ctx.width * (0.38 + bass * 0.22 + beat * 0.18)
    for bolt in range(count):
        start_side = -1 if bolt % 2 == 0 else 1
        start_x = ctx.width * (0.5 + start_side * (0.18 + bolt * 0.017))
        start_y = ctx.height * (0.18 + ((bolt * 0.137 + ctx.progress) % 0.64))
        angle = math.pi * (0.08 + bolt * 0.035) + start_side * math.pi
        points: list[tuple[float, float]] = []
        for segment in range(segments + 1):
            amount = segment / segments
            jitter = math.sin(segment * 2.31 + ctx.time_seconds * (4.0 + treble * 4.0) + bolt)
            fork = math.sin(segment * 5.7 + bolt * 1.9) * ctx.height * 0.025
            x = start_x + math.cos(angle) * reach * amount + jitter * ctx.width * 0.018
            y = start_y + math.sin(angle) * reach * amount + fork
            points.append((x, y))
        color = _rgba(_blend3(palette, bolt / max(1, count - 1)), opacity, intensity, beat, bolt)
        draw.line(points, fill=color, width=max(1, ctx.height // 90), joint="curve")


def _element_palette(
    ctx: FrameContext,
    element: str,
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    if element == "fire":
        return (ctx.palette_accent, (255, 110, 30), ctx.palette_beat)
    if element == "water":
        return ((20, 150, 255), ctx.palette_base, (190, 245, 255))
    if element == "ice":
        return ((150, 235, 255), ctx.palette_beat, ctx.palette_accent)
    if element == "lightning":
        return (ctx.palette_beat, (120, 235, 255), ctx.palette_accent)
    return (ctx.palette_base, ctx.palette_accent, ctx.palette_beat)


def _blend3(
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    amount: float,
) -> tuple[int, int, int]:
    amount = _clamp(amount, 0.0, 1.0)
    if amount < 0.5:
        return blend_color(palette[0], palette[1], amount * 2)
    return blend_color(palette[1], palette[2], (amount - 0.5) * 2)


def _rgba(
    color: tuple[int, int, int],
    opacity: float,
    intensity: float,
    beat: float,
    index: int,
) -> tuple[int, int, int, int]:
    alpha = int(255 * opacity * (0.16 + intensity * 0.32 + beat * 0.18) / (1 + index % 3) ** 0.2)
    return (*color, max(0, min(255, alpha)))


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
