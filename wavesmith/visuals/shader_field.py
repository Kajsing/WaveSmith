"""CPU shader-style field visual module."""

import math

from PIL import Image, ImageDraw, ImageFilter

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float


def draw_shader_field(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw layered audio-reactive light fields inspired by fragment shaders."""
    module_config = module.model_extra or {} if module else {}
    style = str(module_config.get("style", "aurora"))
    opacity = _clamp(float(module_config.get("opacity", 0.52)), 0.0, 1.0)
    layers = max(1, min(int(module_config.get("layers", 4)), 8))
    density = max(8, min(int(module_config.get("density", 34)), 96))
    blur = max(0.0, min(float(module_config.get("blur", 8)), 28.0))
    intensity = feature_float(ctx.features, str(module_config.get("intensity_feature", "rms")))
    bass = feature_float(ctx.features, str(module_config.get("bass_feature", "bass_energy")))
    treble = feature_float(
        ctx.features,
        str(module_config.get("distortion_feature", "treble_energy")),
    )
    beat = 1.0 if ctx.features.get(str(module_config.get("beat_feature", "beat"))) else 0.0

    overlay = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    if style == "vortex":
        _draw_vortex(ctx, overlay_draw, layers, density, opacity, intensity, bass, treble, beat)
    else:
        _draw_aurora(ctx, overlay_draw, layers, density, opacity, intensity, bass, treble, beat)

    if blur:
        soft_overlay = overlay.filter(
            ImageFilter.GaussianBlur(radius=blur * (0.45 + intensity * 0.55))
        )
        overlay = Image.alpha_composite(soft_overlay, overlay)

    composited = Image.alpha_composite(ctx.image.convert("RGBA"), overlay)
    ctx.image.paste(composited.convert("RGB"))


def _draw_aurora(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    layers: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    center_y = ctx.height * (0.45 + math.sin(ctx.time_seconds * 0.31) * 0.04)
    amplitude = ctx.height * (0.12 + bass * 0.18 + beat * 0.08)
    time = ctx.time_seconds
    for layer in range(layers):
        phase = time * (0.55 + layer * 0.17 + treble * 0.55) + layer * 1.7
        vertical_offset = (layer - (layers - 1) / 2) * ctx.height * 0.055
        width = max(2, int(ctx.height * (0.012 + intensity * 0.018 + layer * 0.002)))
        alpha = int(255 * opacity * (0.18 + intensity * 0.28 + beat * 0.14) / (layer + 1) ** 0.35)
        color = _field_color(ctx, layer / max(1, layers - 1), treble, alpha)
        points: list[tuple[float, float]] = []
        for index in range(density + 1):
            x = index / density * ctx.width
            normalized = index / density
            y = center_y + vertical_offset
            y += math.sin(normalized * math.tau * (1.2 + layer * 0.35) + phase) * amplitude
            fine_wave = math.sin(normalized * math.tau * (3.0 + treble * 2.5) - phase * 1.4)
            y += fine_wave * amplitude * 0.22
            points.append((x, y))
        draw.line(points, fill=color, width=width, joint="curve")


def _draw_vortex(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    layers: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    center_x = ctx.width / 2
    center_y = ctx.height / 2
    base_radius = min(ctx.width, ctx.height) * (0.12 + bass * 0.18 + beat * 0.08)
    max_radius = min(ctx.width, ctx.height) * (0.42 + intensity * 0.14)
    time = ctx.time_seconds * (0.42 + treble * 0.75)
    for layer in range(layers):
        points: list[tuple[float, float]] = []
        turns = 1.1 + layer * 0.28 + treble * 0.9
        phase = layer * math.tau / max(1, layers) + time
        for index in range(density + 1):
            amount = index / density
            angle = amount * math.tau * turns + phase
            wobble = math.sin(amount * math.tau * 4 + time * 1.7 + layer) * max_radius * 0.045
            radius = base_radius + amount * (max_radius - base_radius) + wobble
            points.append(
                (
                    center_x + math.cos(angle) * radius,
                    center_y + math.sin(angle) * radius,
                )
            )
        alpha = int(255 * opacity * (0.2 + intensity * 0.34 + beat * 0.16) / (layer + 1) ** 0.25)
        color = _field_color(ctx, layer / max(1, layers - 1), bass, alpha)
        draw.line(points, fill=color, width=max(2, int(ctx.height * 0.012)), joint="curve")


def _field_color(
    ctx: FrameContext,
    amount: float,
    feature: float,
    alpha: int,
) -> tuple[int, int, int, int]:
    color = blend_color(ctx.palette_base, ctx.palette_accent, amount)
    color = blend_color(color, ctx.palette_beat, feature * 0.35)
    return (*color, max(0, min(255, alpha)))


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
