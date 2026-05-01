"""Spectrum ring visual module."""

import math

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float, feature_vector


def draw_spectrum_ring(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw a circular spectrum visualizer."""
    module_config = module.model_extra or {} if module else {}
    bars_config = module_config.get("bars", {})
    spectrum = feature_vector(ctx.features, bars_config.get("height_feature", "spectrum"))
    if not spectrum:
        return

    rms = feature_float(ctx.features, "rms")
    treble = feature_float(ctx.features, "treble_energy")
    center_x = ctx.width / 2
    center_y = ctx.height / 2
    radius_config = module_config.get("radius", {})
    configured_base = float(radius_config.get("base", 220))
    configured_scale = float(radius_config.get("scale", 40))
    bar_scale = float(bars_config.get("scale", 180))
    bar_count = max(4, min(int(bars_config.get("count", len(spectrum))), 360))
    rotation_speed = float(module_config.get("rotation_speed", 0.0))
    design_scale = min(ctx.width, ctx.height) / 720
    base_radius = (configured_base + configured_scale * rms) * design_scale
    max_bar = bar_scale * design_scale * (0.62 + treble * 0.38)
    width = max(1, min(ctx.width, ctx.height) // 260)
    rotation = ctx.time_seconds * rotation_speed

    for index in range(bar_count):
        source_index = round(index / max(1, bar_count - 1) * (len(spectrum) - 1))
        value = spectrum[source_index]
        mirrored_value = (value + spectrum[-source_index - 1]) / 2
        angle = (index / bar_count) * math.tau - math.pi / 2 + rotation
        bar_length = 4 + mirrored_value * max_bar
        start_radius = base_radius
        end_radius = base_radius + bar_length
        start = (
            center_x + math.cos(angle) * start_radius,
            center_y + math.sin(angle) * start_radius,
        )
        end = (
            center_x + math.cos(angle) * end_radius,
            center_y + math.sin(angle) * end_radius,
        )
        color = blend_color(ctx.palette_accent, ctx.palette_beat, mirrored_value * 0.55)
        ctx.draw.line((*start, *end), fill=color, width=width)
