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
        _draw_solar_surface(ctx, overlay, palette, opacity, intensity, bass, beat)
        _draw_solar_prominences(ctx, overlay, draw, palette, opacity, intensity, bass, treble)
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
        plume_noise = _fbm(
            xx * (7.0 + treble * 1.2) + warp_x * 1.25 + time * 0.07,
            yy * 1.6 - rise * 0.26 + warp_y * 0.9,
            octaves=4,
        )
        plume_gate = _smoothstep(0.47, 0.86, plume_noise + source_noise * 0.12)
        tongue_ceiling = flame_limit * (0.58 + source_noise * 0.42)
        tongue_fade = 1.0 - _smoothstep(tongue_ceiling, tongue_ceiling + 0.18, height_from_bottom)
        vertical_pull = _smoothstep(0.05, 0.26, height_from_bottom)
        density = tongues * source * vertical_fade * (0.45 + base_feed * 0.22)
        density += plume_gate * source * tongue_fade * vertical_pull * (0.16 + flare * 0.1)
        density += core * 0.62 + base_feed * source * (0.2 + bass * 0.1 + beat * 0.04)
        density *= 1.18 + intensity * 0.34 + beat * 0.14
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


def _draw_solar_surface(
    ctx: FrameContext,
    overlay: Image.Image,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    intensity: float,
    bass: float,
    beat: float,
) -> None:
    surface_width = max(160, min(360, ctx.width // 2))
    surface_height = max(90, min(220, ctx.height // 2))
    x = np.linspace(0.0, 1.0, surface_width, dtype=np.float32)
    y = np.linspace(0.0, 1.0, surface_height, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    time = np.float32(ctx.time_seconds)
    cx, cy, rx, ry = _solar_ellipse(surface_width, surface_height)
    ellipse = ((xx * surface_width - cx) / rx) ** 2 + ((yy * surface_height - cy) / ry) ** 2
    mask = ellipse <= 1.0
    limb = np.clip(1.0 - np.abs(ellipse - 1.0) * 18.0, 0.0, 1.0)
    texture = _fbm(xx * 5.2 + time * 0.035, yy * 4.4 - time * 0.018, octaves=5)
    granules = _fbm(xx * 18.0 - time * 0.06, yy * 13.0 + time * 0.02, octaves=3)
    heat = np.clip(texture * 0.7 + granules * 0.38 + limb * 0.42 + bass * 0.18 + beat * 0.08, 0, 1)
    dark = np.array([92, 18, 2], dtype=np.float32)
    orange = np.array(palette[1], dtype=np.float32)
    yellow = np.array([255, 192, 40], dtype=np.float32)
    color = _mix_rgb(dark, orange, _smoothstep(0.18, 0.72, heat))
    color = _mix_rgb(color, yellow, _smoothstep(0.68, 1.0, heat))
    alpha = np.where(mask, 255 * opacity * (0.62 + intensity * 0.18), 0.0)
    alpha += limb * 255 * opacity * (0.16 + bass * 0.12)
    rgba = np.dstack((color, np.clip(alpha, 0, 255))).astype(np.uint8)
    image = Image.fromarray(rgba, mode="RGBA").resize(
        (ctx.width, ctx.height),
        Image.Resampling.BICUBIC,
    )
    glow = image.filter(ImageFilter.GaussianBlur(radius=max(4, ctx.height // 34)))
    overlay.alpha_composite(glow)
    overlay.alpha_composite(image)


def _solar_ellipse(width: int, height: int) -> tuple[float, float, float, float]:
    return width * 0.5, height * 1.52, width * 0.72, height * 0.78


def _solar_limb_y(ctx: FrameContext, x: float) -> float:
    cx, cy, rx, ry = _solar_ellipse(ctx.width, ctx.height)
    amount = _clamp((x - cx) / rx, -0.98, 0.98)
    return cy - ry * math.sqrt(max(0.0, 1.0 - amount * amount))


def _draw_solar_prominences(
    ctx: FrameContext,
    overlay: Image.Image,
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    intensity: float,
    bass: float,
    treble: float,
) -> None:
    del draw
    glow = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    sharp = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    sharp_draw = ImageDraw.Draw(sharp)
    anchors = (0.12, 0.28, 0.44, 0.62, 0.78, 0.92)
    for index, anchor in enumerate(anchors):
        seed = float(index) + 1.0
        activation = _music_region_envelope(ctx, index)
        if activation < 0.02:
            continue
        width = ctx.width * (0.13 + _hash_scalar(seed, 4.0) * 0.2)
        height = ctx.height * (0.08 + bass * 0.14 + intensity * 0.18)
        height *= 0.72 + _hash_scalar(seed, 7.0) * 0.9
        height *= 0.5 + activation * 1.05
        phase = ctx.time_seconds * (0.11 + _hash_scalar(seed, 3.0) * 0.08) + seed
        sway = math.sin(phase) * ctx.width * (0.012 + treble * 0.01)
        amount = index / max(1, len(anchors) - 1)
        outer = blend_color((255, 68, 18), palette[1], min(1.0, 0.35 + amount * 0.25))
        middle = blend_color((255, 168, 38), palette[2], 0.28)
        inner = blend_color((255, 238, 126), palette[2], 0.55)
        alpha = int(
            255
            * opacity
            * (0.1 + intensity * 0.22 + bass * 0.18)
            * (0.28 + activation * 1.0)
        )
        for strand in range(8):
            strand_seed = seed + strand * 0.37
            strand_activation = activation * (0.58 + _hash_scalar(strand_seed, 16.0) * 0.42)
            if strand_activation < 0.055:
                continue
            direction = -1.0 if _hash_scalar(strand_seed, 8.0) < 0.38 else 1.0
            offset = (_hash_scalar(strand_seed, 5.0) - 0.5) * width * 0.48
            x0 = anchor * ctx.width + sway + offset
            x3 = x0 + direction * width * (0.25 + _hash_scalar(strand_seed, 9.0) * 0.55)
            y0 = _solar_limb_y(ctx, x0) - ctx.height * (
                0.004 + _hash_scalar(strand_seed, 6.0) * 0.01
            )
            y3 = _solar_limb_y(ctx, x3) - ctx.height * (
                0.006 + _hash_scalar(strand_seed, 10.0) * 0.012
            )
            strand_height = height * (0.35 + _hash_scalar(strand_seed, 7.0) * 0.92)
            strand_height *= 0.68 + strand_activation * 0.62
            twist = math.sin(phase * (1.1 + strand * 0.09)) * ctx.width * 0.034
            c1 = (
                x0 + direction * width * (0.06 + _hash_scalar(strand_seed, 11.0) * 0.18) + twist,
                y0 - strand_height * (0.9 + _hash_scalar(strand_seed, 12.0) * 0.72),
            )
            c2 = (
                x3 - direction * width * (0.08 + _hash_scalar(strand_seed, 13.0) * 0.16),
                y3 - strand_height * (0.45 + _hash_scalar(strand_seed, 14.0) * 0.55),
            )
            points = _cubic_points((x0, y0), c1, c2, (x3, y3), samples=46)
            width_outer = max(4, int(ctx.height * (0.009 + intensity * 0.01)))
            width_inner = max(1, width_outer // 4)
            glow_draw.line(
                points,
                fill=(*outer, max(0, min(120, int((alpha - 24) * strand_activation)))),
                width=width_outer * 4,
                joint="curve",
            )
            sharp_alpha = max(0, min(180, int((alpha + 4 - strand * 3) * strand_activation)))
            sharp_draw.line(
                points,
                fill=(*middle, sharp_alpha),
                width=max(2, width_outer // 2),
                joint="curve",
            )
            if strand in {1, 4}:
                segment = points[6:-10]
                sharp_draw.line(
                    segment,
                    fill=(*inner, max(0, min(190, alpha + 28))),
                    width=width_inner,
                    joint="curve",
                )
            if strand in {0, 3} and activation > 0.32:
                _draw_solar_hotspot(
                    glow_draw,
                    palette,
                    opacity,
                    intensity,
                    bass,
                    x0,
                    y0,
                    activation,
                )
    overlay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=max(5, ctx.height // 40))))
    overlay.alpha_composite(sharp)


def _music_region_envelope(ctx: FrameContext, index: int) -> float:
    tempo = float(ctx.features.get("tempo_bpm", 0.0) or 0.0)
    beat_seconds = 60.0 / tempo if tempo > 1.0 else 0.75
    cycle = beat_seconds * 8.0
    start_offset = index * beat_seconds * 1.5
    phase = ((ctx.time_seconds - start_offset) % cycle) / cycle
    attack = _scalar_smoothstep(0.0, 0.18, phase)
    release = 1.0 - _scalar_smoothstep(0.26, 1.0, phase)
    gate = attack * release
    slow_pulse = feature_float(ctx.features, "slow_pulse")
    beat_decay = feature_float(ctx.features, "beat_decay")
    return _clamp(gate * (0.38 + slow_pulse * 0.72) + beat_decay * 0.24, 0.0, 1.0)


def _draw_solar_hotspot(
    draw: ImageDraw.ImageDraw,
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    opacity: float,
    intensity: float,
    bass: float,
    x: float,
    y: float,
    activation: float,
) -> None:
    radius = (3 + intensity * 8 + bass * 7) * (0.45 + activation * 0.75)
    color = blend_color((255, 192, 36), palette[2], 0.45)
    alpha = int(255 * opacity * (0.14 + intensity * 0.17 + bass * 0.14) * activation)
    draw.ellipse(
        (x - radius, y - radius * 0.7, x + radius, y + radius * 0.7),
        fill=(*color, max(0, min(230, alpha))),
    )


def _cubic_points(
    start: tuple[float, float],
    control_a: tuple[float, float],
    control_b: tuple[float, float],
    end: tuple[float, float],
    samples: int,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(samples):
        t = index / max(1, samples - 1)
        inv = 1.0 - t
        x = (
            inv**3 * start[0]
            + 3.0 * inv * inv * t * control_a[0]
            + 3.0 * inv * t * t * control_b[0]
            + t**3 * end[0]
        )
        y = (
            inv**3 * start[1]
            + 3.0 * inv * inv * t * control_a[1]
            + 3.0 * inv * t * t * control_b[1]
            + t**3 * end[1]
        )
        points.append((x, y))
    return points


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


def _hash_scalar(x: float, y: float) -> float:
    value = math.sin(x * 127.1 + y * 311.7) * 43758.5453
    return value - math.floor(value)


def _smoothstep(
    edge0: float | np.ndarray,
    edge1: float | np.ndarray,
    value: np.ndarray,
) -> np.ndarray:
    denominator = np.maximum(0.0001, np.asarray(edge1) - np.asarray(edge0))
    t = np.clip((value - edge0) / denominator, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _scalar_smoothstep(edge0: float, edge1: float, value: float) -> float:
    denominator = max(0.0001, edge1 - edge0)
    t = _clamp((value - edge0) / denominator, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _mix_rgb(a: np.ndarray, b: np.ndarray, amount: np.ndarray) -> np.ndarray:
    return a * (1.0 - amount[..., None]) + b * amount[..., None]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
