"""Cinematic horizontal waveform and vertical spectrum spires."""

import math

from PIL import Image, ImageDraw, ImageFilter

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float, feature_vector


def draw_spectrum_wall(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw spectrum bars and a central waveform beam inspired by poster visualizers."""
    module_config = module.model_extra or {} if module else {}
    spectrum = feature_vector(ctx.features, module_config.get("spectrum_feature", "spectrum"))
    waveform = feature_vector(
        ctx.features,
        module_config.get("waveform_feature", "waveform_preview"),
    )
    if not spectrum:
        return

    opacity = max(0.0, min(float(module_config.get("opacity", 0.78)), 1.0))
    bars = max(24, min(int(module_config.get("bars", 120)), 260))
    baseline = ctx.height * float(module_config.get("baseline", 0.52))
    max_height = ctx.height * float(module_config.get("height", 0.34))
    side_bias = str(module_config.get("layout", "full"))
    rms = feature_float(ctx.features, "rms")
    bass = feature_float(ctx.features, "bass_energy")
    treble = feature_float(ctx.features, "treble_energy")

    overlay = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    _draw_bars(draw, ctx, spectrum, bars, baseline, max_height, opacity, rms, treble, side_bias)
    if waveform:
        _draw_waveform_beam(draw, ctx, waveform, baseline, opacity, rms, bass)

    glow = overlay.filter(ImageFilter.GaussianBlur(radius=max(2, ctx.height // 100)))
    composited = Image.alpha_composite(ctx.image.convert("RGBA"), glow)
    composited = Image.alpha_composite(composited, overlay)
    ctx.image.paste(composited.convert("RGB"))


def _draw_bars(
    draw: ImageDraw.ImageDraw,
    ctx: FrameContext,
    spectrum: list[float],
    bars: int,
    baseline: float,
    max_height: float,
    opacity: float,
    rms: float,
    treble: float,
    layout: str,
) -> None:
    gap = max(1, int(ctx.width / bars * 0.22))
    bar_width = max(1, int(ctx.width / bars - gap))
    for index in range(bars):
        source_index = round(index / max(1, bars - 1) * (len(spectrum) - 1))
        value = spectrum[source_index]
        if layout == "sides":
            center_weight = abs(index / max(1, bars - 1) - 0.5) * 2
            value *= 0.18 + center_weight * 1.15
        shimmer = 0.72 + math.sin(index * 0.37 + ctx.time_seconds * (0.8 + treble)) * 0.18
        height = max_height * (0.05 + value * (0.95 + rms * 0.42)) * shimmer
        x0 = index / bars * ctx.width + gap / 2
        x1 = x0 + bar_width
        color = blend_color(ctx.palette_base, ctx.palette_accent, index / max(1, bars - 1))
        color = blend_color(color, ctx.palette_beat, min(1.0, value * 0.6 + treble * 0.25))
        alpha = int(255 * opacity * (0.22 + value * 0.5 + rms * 0.18))
        draw.rounded_rectangle(
            (x0, baseline - height, x1, baseline + height * 0.36),
            radius=max(1, bar_width // 2),
            fill=(*color, max(0, min(255, alpha))),
        )
        if value > 0.68:
            draw.line(
                (x0, baseline - height, x1, baseline - height),
                fill=(*ctx.palette_beat, alpha),
            )


def _draw_waveform_beam(
    draw: ImageDraw.ImageDraw,
    ctx: FrameContext,
    waveform: list[float],
    baseline: float,
    opacity: float,
    rms: float,
    bass: float,
) -> None:
    amplitude = ctx.height * (0.07 + rms * 0.12 + bass * 0.04)
    points: list[tuple[float, float]] = []
    for index, value in enumerate(waveform):
        x = index / max(1, len(waveform) - 1) * ctx.width
        centered = (value - 0.5) * 2
        needle = math.sin(index * 0.9 + ctx.time_seconds * 1.7) * amplitude * 0.2
        y = baseline + centered * amplitude + needle
        points.append((x, y))
    for width, alpha_scale in [(9, 0.2), (5, 0.35), (2, 0.92)]:
        draw.line(
            points,
            fill=(*ctx.palette_beat, int(255 * opacity * alpha_scale)),
            width=max(1, width),
            joint="curve",
        )
    draw.line(
        (0, baseline, ctx.width, baseline),
        fill=(*ctx.palette_beat, int(255 * opacity * 0.5)),
    )
