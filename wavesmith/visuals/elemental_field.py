"""Elemental CPU visual fields."""

import math

import numpy as np
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
    behavior = str(module_config.get("behavior", module_config.get("fire_behavior", "dream")))
    intensity = feature_float(ctx.features, str(module_config.get("intensity_feature", "rms")))
    bass = feature_float(ctx.features, str(module_config.get("bass_feature", "bass_energy")))
    treble = feature_float(ctx.features, str(module_config.get("motion_feature", "treble_energy")))
    beat = 1.0 if ctx.features.get(str(module_config.get("beat_feature", "beat"))) else 0.0

    overlay = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    palette = _element_palette(ctx, element)
    if element == "fire":
        _draw_fire(
            ctx,
            overlay,
            draw,
            palette,
            bands,
            density,
            opacity,
            intensity,
            bass,
            treble,
            beat,
            behavior.lower(),
        )
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
    overlay: Image.Image,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    bands: int,
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
    behavior: str,
) -> None:
    _draw_fire_density_field(
        ctx, overlay, palette, opacity, intensity, bass, treble, beat, behavior
    )
    floor = ctx.height * (0.93 - beat * 0.05)
    if behavior in {"natural", "realistic", "normal"}:
        _draw_fire_base_glow(ctx, draw, palette, opacity, intensity, bass, beat, floor)
    else:
        flame_height = ctx.height * (0.42 + bass * 0.28 + beat * 0.18)
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
            color = _rgba(
                _blend3(palette, band / max(1, bands - 1)),
                opacity,
                intensity,
                beat,
                band,
            )
            draw.line(points, fill=color, width=max(3, ctx.height // 55), joint="curve")
    _draw_fire_embers(
        ctx, draw, palette, density, opacity, intensity, treble, beat, floor, behavior
    )


def _draw_fire_density_field(
    ctx: FrameContext,
    overlay: Image.Image,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
    behavior: str,
) -> None:
    field_width = max(96, min(240, ctx.width // 3))
    field_height = max(54, min(140, ctx.height // 3))
    x = np.linspace(0.0, 1.0, field_width, dtype=np.float32)
    y = np.linspace(0.0, 1.0, field_height, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    height_from_bottom = 1.0 - yy
    time = np.float32(ctx.time_seconds)
    natural = behavior in {"natural", "realistic", "normal"}
    scale = 2.45 + treble * 0.5 if natural else 3.2 + treble * 1.4
    rise = time * (0.72 + bass * 0.34 + beat * 0.12) if natural else time * (
        0.52 + bass * 0.35 + beat * 0.25
    )

    warp_x = _fbm(xx * 2.2 + time * 0.11, yy * 2.6 - rise * 0.22, octaves=3)
    warp_y = _fbm(xx * 2.8 - time * 0.08, yy * 2.1 - rise * 0.3, octaves=3)
    warp_amount_x = 0.28 + treble * 0.1 if natural else 0.55 + treble * 0.25
    warp_amount_y = 0.24 + bass * 0.16 if natural else 0.35 + bass * 0.3
    warped_x = xx * scale + (warp_x - 0.5) * warp_amount_x
    warped_y = yy * (scale * (1.52 if natural else 1.25)) - rise + (warp_y - 0.5) * warp_amount_y
    turbulence = _fbm(warped_x, warped_y, octaves=5)
    source_noise = _fbm(
        xx * (11.0 if natural else 9.0) + time * 0.13,
        yy * 4.0 - rise * 0.4,
        octaves=3,
    )

    if natural:
        flare = max(bass, intensity * 0.82)
        flame_limit = 0.48 + flare * 0.3 + beat * 0.1
        base_width = 0.82 - height_from_bottom * (0.48 - bass * 0.08)
        source = np.exp(-((xx - 0.5) ** 2) / np.maximum(0.045, base_width**2))
        side_fade = np.exp(-((np.abs(xx - 0.5) / 0.64) ** 4))
        source *= side_fade * (0.64 + source_noise * 0.52)
        base_feed = 1.0 - _smoothstep(0.0, 0.15, height_from_bottom)
        vertical_fade = 1.0 - _smoothstep(flame_limit, flame_limit + 0.23, height_from_bottom)
        threshold = 0.21 + height_from_bottom * (0.56 - bass * 0.18)
        threshold += (1.0 - source_noise) * 0.12
        tongues = _smoothstep(threshold, 0.88, turbulence + source_noise * 0.08)
        core_falloff = 1.0 - _smoothstep(0.0, flame_limit * 0.78, height_from_bottom)
        core = source * core_falloff * (0.22 + flare * 0.12)
        ridges = 1.0 - np.abs(
            np.sin((xx * (5.4 + treble * 1.4) + (warp_x - 0.5) * 0.42) * math.tau)
        )
        ridges = _smoothstep(0.54, 0.96, ridges + source_noise * 0.18)
        tongue_ceiling = flame_limit * (0.58 + source_noise * 0.42)
        tongue_fade = 1.0 - _smoothstep(tongue_ceiling, tongue_ceiling + 0.18, height_from_bottom)
        vertical_pull = _smoothstep(0.05, 0.26, height_from_bottom)
        density = tongues * source * vertical_fade * (0.78 + base_feed * 0.32)
        density += ridges * source * tongue_fade * vertical_pull * (0.5 + flare * 0.25)
        density += core + base_feed * source * (0.26 + bass * 0.14 + beat * 0.06)
        density *= 1.24 + intensity * 0.44 + beat * 0.18
    else:
        base_width = 0.78 - height_from_bottom * (0.54 - bass * 0.08)
        source = np.exp(-((xx - 0.5) ** 2) / np.maximum(0.04, base_width**2))
        source *= 0.45 + source_noise * 0.65
        base_feed = 1.0 - _smoothstep(0.0, 0.14, height_from_bottom)
        vertical_fade = 1.0 - _smoothstep(0.58 + bass * 0.1, 1.0, height_from_bottom)
        threshold = 0.36 + height_from_bottom * (0.5 - bass * 0.12)
        threshold += (1.0 - source_noise) * 0.14
        tongues = _smoothstep(threshold, 1.0, turbulence)
        density = tongues * source * vertical_fade
        density += base_feed * (0.22 + bass * 0.18 + beat * 0.08)
        density *= 1.25 + intensity * 0.55 + beat * 0.22
    density = np.clip(density, 0.0, 1.0)

    rgba = _fire_rgba(density, palette, opacity)
    image = Image.fromarray(rgba, mode="RGBA")
    image = image.resize((ctx.width, ctx.height), Image.Resampling.BICUBIC)
    overlay.alpha_composite(image)


def _draw_fire_base_glow(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    intensity: float,
    bass: float,
    beat: float,
    floor: float,
) -> None:
    glow_height = ctx.height * (0.045 + bass * 0.028 + beat * 0.018)
    glow_color = _blend3(palette, 0.75)
    alpha = int(255 * opacity * (0.09 + intensity * 0.1 + bass * 0.1 + beat * 0.05))
    draw.ellipse(
        (
            ctx.width * -0.04,
            floor - glow_height,
            ctx.width * 1.04,
            floor + glow_height * 0.6,
        ),
        fill=(*glow_color, max(0, min(135, alpha))),
    )


def _draw_fire_lashes(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    density: int,
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
    beat: float,
    floor: float,
) -> None:
    lash_count = max(24, min(density, 90))
    for index in range(lash_count):
        amount = index / max(1, lash_count - 1)
        x = amount * ctx.width
        phase = ctx.time_seconds * (1.6 + treble * 2.0) + index * 0.73
        base_width = ctx.width * (0.008 + (index % 5) * 0.0015)
        height = ctx.height * (0.18 + intensity * 0.1 + bass * 0.32 + beat * 0.14)
        height *= 0.55 + abs(math.sin(index * 1.91 + ctx.time_seconds * 0.9))
        curl = math.sin(phase) * ctx.width * (0.012 + treble * 0.018)
        tip_y = floor - height
        mid_y = floor - height * 0.48
        color_amount = min(1.0, 0.2 + height / max(1, ctx.height * 0.42))
        fill = _blend3(palette, color_amount)
        alpha = int(255 * opacity * (0.28 + intensity * 0.28 + bass * 0.32 + beat * 0.18))
        points = [
            (x - base_width * 1.7, floor),
            (x - base_width * 0.45 + curl * 0.35, mid_y),
            (x + curl, tip_y),
            (x + base_width * 0.5 + curl * 0.25, mid_y),
            (x + base_width * 1.7, floor),
        ]
        draw.polygon(points, fill=(*fill, max(0, min(220, alpha))))
        inner = _blend3(palette, 0.86)
        draw.line(
            [(x, floor), (x + curl * 0.42, mid_y), (x + curl, tip_y)],
            fill=(*inner, max(0, min(255, alpha + 32))),
            width=max(1, ctx.height // 95),
            joint="curve",
        )


def _draw_fire_embers(
    ctx: FrameContext,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    density: int,
    opacity: float,
    intensity: float,
    treble: float,
    beat: float,
    floor: float,
    behavior: str = "dream",
) -> None:
    natural = behavior in {"natural", "realistic", "normal"}
    ember_count = max(16, density // 3) if natural else max(28, density // 2)
    for index in range(ember_count):
        drift = ctx.time_seconds * (0.12 + treble * 0.28 if natural else 0.18 + treble * 0.5)
        x = ((index * 89.17 + drift * ctx.width) % (ctx.width * 1.08)) - ctx.width * 0.04
        rise = ((index * 0.137 + ctx.progress * (0.5 + treble)) % 1.0)
        y = floor - rise * ctx.height * ((0.34 + beat * 0.08) if natural else (0.55 + beat * 0.12))
        flicker = 0.55 + abs(math.sin(index * 2.1 + ctx.time_seconds * 4.0)) * 0.45
        size = max(1, int((1 + (index % 3)) * flicker))
        color = _blend3(palette, 0.62 + (index % 5) / 14)
        if natural:
            alpha = int(255 * opacity * (0.15 + intensity * 0.16 + treble * 0.14) * flicker)
        else:
            alpha = int(255 * opacity * (0.24 + intensity * 0.2 + treble * 0.26) * flicker)
        draw.ellipse(
            (x - size, y - size, x + size, y + size),
            fill=(*color, max(0, min(255, alpha))),
        )


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


def _fire_rgba(
    density: np.ndarray,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
) -> np.ndarray:
    dark_red = np.array([54, 5, 0], dtype=np.float32)
    orange = np.array(palette[1], dtype=np.float32)
    yellow = np.array([255, 188, 42], dtype=np.float32)
    hot = np.array(palette[2], dtype=np.float32)
    red_to_orange = _mix_rgb(dark_red, orange, _smoothstep(0.12, 0.62, density))
    orange_to_yellow = _mix_rgb(red_to_orange, yellow, _smoothstep(0.55, 0.88, density))
    color = _mix_rgb(orange_to_yellow, hot, _smoothstep(0.84, 1.0, density))
    alpha = np.clip((density**1.75) * 255 * opacity * 1.05, 0, 255)
    rgba = np.dstack((color, alpha)).astype(np.uint8)
    return rgba


def _fbm(x: np.ndarray, y: np.ndarray, octaves: int) -> np.ndarray:
    value = np.zeros_like(x, dtype=np.float32)
    amplitude = np.float32(0.5)
    frequency = np.float32(1.0)
    total = np.float32(0.0)
    for _ in range(octaves):
        value += _value_noise(x * frequency, y * frequency) * amplitude
        total += amplitude
        frequency *= np.float32(2.02)
        amplitude *= np.float32(0.52)
    return value / total


def _value_noise(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x0 = np.floor(x)
    y0 = np.floor(y)
    xf = x - x0
    yf = y - y0
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)
    n00 = _hash2(x0, y0)
    n10 = _hash2(x0 + 1.0, y0)
    n01 = _hash2(x0, y0 + 1.0)
    n11 = _hash2(x0 + 1.0, y0 + 1.0)
    nx0 = n00 * (1.0 - u) + n10 * u
    nx1 = n01 * (1.0 - u) + n11 * u
    return nx0 * (1.0 - v) + nx1 * v


def _hash2(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    value = np.sin(x * 127.1 + y * 311.7) * 43758.5453
    return value - np.floor(value)


def _smoothstep(
    edge0: float | np.ndarray,
    edge1: float | np.ndarray,
    value: np.ndarray,
) -> np.ndarray:
    denominator = np.maximum(0.0001, np.asarray(edge1) - np.asarray(edge0))
    t = np.clip((value - edge0) / denominator, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _mix_rgb(a: np.ndarray, b: np.ndarray, amount: np.ndarray) -> np.ndarray:
    return a * (1.0 - amount[..., None]) + b * amount[..., None]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
