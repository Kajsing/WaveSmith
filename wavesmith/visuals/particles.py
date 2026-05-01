"""Particle visual module."""

import math

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float


def draw_particles(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw deterministic feature-reactive particles."""
    module_config = module.model_extra or {} if module else {}
    count = int(module_config.get("count", 180))
    count = max(0, min(count, 600))
    velocity_feature = module_config.get("velocity_feature", "treble_energy")
    velocity = feature_float(ctx.features, velocity_feature)
    beat_boost = 1.0 if ctx.features.get(module_config.get("burst_on", "beat")) else 0.0
    center_x = ctx.width / 2
    center_y = ctx.height / 2
    spread = min(ctx.width, ctx.height) * (0.28 + velocity * 0.18 + beat_boost * 0.08)
    color = blend_color(ctx.palette_base, ctx.palette_accent, 0.55 + velocity * 0.35)

    for index in range(count):
        angle = ((index * 137.508) % 360) * math.pi / 180
        orbit = ((index % 37) / 37) * spread
        drift = ctx.time_seconds * (0.18 + velocity * 0.8)
        radius = orbit + math.sin(index * 0.73 + drift) * spread * 0.08
        x = center_x + math.cos(angle + drift) * radius
        y = center_y + math.sin(angle + drift * 0.7) * radius
        size = 1 + int((index % 3 == 0) or beat_boost)
        ctx.draw.ellipse((x - size, y - size, x + size, y + size), fill=color)
