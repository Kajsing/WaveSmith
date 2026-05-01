"""Cinematic portal ring visual module."""

import math

from PIL import Image, ImageDraw, ImageFilter

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float


def draw_portal_ring(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw a cinematic audio-reactive portal ring."""
    module_config = module.model_extra or {} if module else {}
    style = str(module_config.get("style", "inferno"))
    opacity = _clamp(float(module_config.get("opacity", 0.85)), 0.0, 1.0)
    shard_count = max(24, min(int(module_config.get("shards", 120)), 320))
    ring_width = max(4, int(min(ctx.width, ctx.height) * float(module_config.get("width", 0.035))))
    core_opacity = _clamp(float(module_config.get("core_opacity", 0.42)), 0.0, 1.0)
    design_scale = min(ctx.width, ctx.height) / 720
    radius = min(ctx.width, ctx.height) * float(module_config.get("radius", 0.29))
    radius += feature_float(ctx.features, "bass_energy") * min(ctx.width, ctx.height) * 0.035
    center_x = ctx.width / 2
    center_y = ctx.height * float(module_config.get("center_y", 0.48))
    rms = feature_float(ctx.features, "rms")
    bass = feature_float(ctx.features, "bass_energy")
    treble = feature_float(ctx.features, "treble_energy")
    beat = 1.0 if ctx.features.get("beat") else 0.0
    palette = _style_palette(ctx, style)

    overlay = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    _draw_void_core(draw, center_x, center_y, radius, ring_width, core_opacity, bass)
    _draw_ring_core(draw, center_x, center_y, radius, ring_width, palette, opacity, rms, beat)
    if style == "crystal":
        _draw_crystal_shards(
            draw, center_x, center_y, radius, shard_count, palette, opacity, rms, treble
        )
    elif style == "electric":
        _draw_electric_branches(
            draw, center_x, center_y, radius, shard_count, palette, opacity, bass, treble
        )
    else:
        _draw_flame_lashes(
            draw, center_x, center_y, radius, shard_count, palette, opacity, bass, treble, beat
        )
        _draw_flame_wisps(
            draw,
            center_x,
            center_y,
            radius,
            shard_count,
            palette,
            opacity,
            bass,
            treble,
            ctx.time_seconds,
        )
    _draw_sparks(
        draw, center_x, center_y, radius, shard_count, palette, opacity, ctx.time_seconds, treble
    )

    soft = overlay.filter(ImageFilter.GaussianBlur(radius=max(3, int(9 * design_scale))))
    composited = Image.alpha_composite(ctx.image.convert("RGBA"), soft)
    composited = Image.alpha_composite(composited, overlay)
    ctx.image.paste(composited.convert("RGB"))


def _draw_void_core(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius: float,
    ring_width: int,
    core_opacity: float,
    bass: float,
) -> None:
    core_radius = radius - ring_width * (0.85 + bass * 0.3)
    if core_radius <= 2:
        return
    draw.ellipse(
        (
            center_x - core_radius,
            center_y - core_radius,
            center_x + core_radius,
            center_y + core_radius,
        ),
        fill=(0, 0, 0, int(255 * core_opacity)),
    )


def _draw_ring_core(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius: float,
    ring_width: int,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    rms: float,
    beat: float,
) -> None:
    for index in range(5, 0, -1):
        amount = index / 5
        current_radius = radius + (index - 3) * ring_width * 0.55
        alpha = int(255 * opacity * (0.28 + rms * 0.34 + beat * 0.24) * amount)
        color = (*_blend3(palette, 1.0 - amount * 0.35), max(0, min(255, alpha)))
        draw.ellipse(
            (
                center_x - current_radius,
                center_y - current_radius,
                center_x + current_radius,
                center_y + current_radius,
            ),
            outline=color,
            width=max(1, ring_width // (6 - index)),
        )


def _draw_flame_lashes(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius: float,
    count: int,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    bass: float,
    treble: float,
    beat: float,
) -> None:
    for index in range(count):
        angle = index / count * math.tau
        favor_top = max(0.2, 1.0 - max(0.0, math.sin(angle)) * 0.45)
        lick = math.sin(index * 1.73 + bass * 4.0) * 0.35 + math.sin(index * 0.37) * 0.22
        length = radius * (0.16 + bass * 0.26 + treble * 0.12 + beat * 0.14) * favor_top
        length *= 0.55 + abs(lick)
        inner = radius - length * 0.16
        outer = radius + length
        points = [
            _polar(center_x, center_y, angle - 0.012, inner),
            _polar(center_x, center_y, angle, outer),
            _polar(center_x, center_y, angle + 0.012, inner),
        ]
        alpha = int(255 * opacity * (0.28 + bass * 0.42 + beat * 0.22))
        draw.polygon(points, fill=(*_blend3(palette, index / max(1, count - 1)), alpha))


def _draw_flame_wisps(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius: float,
    count: int,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    bass: float,
    treble: float,
    time_seconds: float,
) -> None:
    wisp_count = max(28, count // 5)
    for index in range(wisp_count):
        angle = -math.pi * (0.08 + (index / max(1, wisp_count - 1)) * 0.84)
        angle += math.sin(index * 1.19 + time_seconds * 0.7) * 0.12
        start_radius = radius * (0.92 + (index % 5) * 0.018)
        crown_boost = max(0.25, -math.sin(angle))
        length = radius * (0.26 + bass * 0.4 + treble * 0.18) * crown_boost
        points: list[tuple[float, float]] = []
        for segment in range(7):
            amount = segment / 6
            curl = math.sin(segment * 1.7 + index * 0.61 + time_seconds * (1.0 + treble)) * 0.16
            current_angle = angle + curl * amount
            current_radius = start_radius + length * amount
            x, y = _polar(center_x, center_y, current_angle, current_radius)
            y -= math.sin(amount * math.pi) * radius * (0.14 + bass * 0.18) * crown_boost
            points.append((x, y))
        alpha = int(255 * opacity * (0.28 + bass * 0.36 + treble * 0.18) * crown_boost)
        color = _blend3(palette, 0.45 + (index % 7) / 14)
        draw.line(
            points,
            fill=(*color, max(0, min(255, alpha))),
            width=max(1, int(radius // 42)),
            joint="curve",
        )


def _draw_crystal_shards(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius: float,
    count: int,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    rms: float,
    treble: float,
) -> None:
    for index in range(count // 2):
        angle = index / max(1, count // 2) * math.tau
        length = radius * (0.06 + rms * 0.08 + (index % 5) * 0.012)
        width = 0.012 + treble * 0.008
        points = [
            _polar(center_x, center_y, angle - width, radius * 0.98),
            _polar(center_x, center_y, angle, radius + length),
            _polar(center_x, center_y, angle + width, radius * 0.98),
            _polar(center_x, center_y, angle, radius + length * 0.22),
        ]
        alpha = int(255 * opacity * (0.22 + rms * 0.28))
        draw.polygon(points, fill=(*_blend3(palette, (index % 9) / 8), alpha))
        draw.line(points + [points[0]], fill=(*palette[2], min(255, alpha + 40)), width=1)


def _draw_electric_branches(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius: float,
    count: int,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    bass: float,
    treble: float,
) -> None:
    branch_count = max(10, count // 12)
    for branch in range(branch_count):
        angle = branch / branch_count * math.tau
        points = []
        for segment in range(5):
            amount = segment / 4
            jitter = math.sin(branch * 3.1 + segment * 2.4 + treble * 4.0) * radius * 0.035
            points.append(
                _polar(center_x, center_y, angle + jitter / radius, radius * (1.0 + amount * 0.42))
            )
        alpha = int(255 * opacity * (0.28 + treble * 0.38 + bass * 0.12))
        draw.line(
            points,
            fill=(*_blend3(palette, branch / max(1, branch_count - 1)), alpha),
            width=2,
        )


def _draw_sparks(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius: float,
    count: int,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    time_seconds: float,
    treble: float,
) -> None:
    for index in range(max(18, count // 3)):
        angle = ((index * 137.508) % 360) * math.pi / 180 + time_seconds * 0.08
        distance = radius * (0.78 + (index % 31) / 31 * (0.85 + treble * 0.45))
        x, y = _polar(center_x, center_y, angle, distance)
        size = 1 + int(index % 7 == 0)
        alpha = int(255 * opacity * (0.16 + treble * 0.34))
        draw.ellipse((x - size, y - size, x + size, y + size), fill=(*palette[index % 3], alpha))


def _style_palette(
    ctx: FrameContext,
    style: str,
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    if style == "crystal":
        return ((90, 220, 255), ctx.palette_accent, ctx.palette_beat)
    if style == "electric":
        return ((80, 160, 255), ctx.palette_beat, (150, 235, 255))
    return (ctx.palette_accent, (255, 135, 24), ctx.palette_beat)


def _blend3(
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    amount: float,
) -> tuple[int, int, int]:
    amount = _clamp(amount, 0.0, 1.0)
    if amount < 0.5:
        return blend_color(palette[0], palette[1], amount * 2)
    return blend_color(palette[1], palette[2], (amount - 0.5) * 2)


def _polar(center_x: float, center_y: float, angle: float, radius: float) -> tuple[float, float]:
    return center_x + math.cos(angle) * radius, center_y + math.sin(angle) * radius


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
