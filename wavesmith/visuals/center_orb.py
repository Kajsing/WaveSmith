"""Center orb visual module."""

import math

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float


def draw_center_orb(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw a bass-reactive center orb with beat shock rings."""
    radius_config = (module.model_extra or {}).get("radius", {}) if module else {}
    radius_feature = radius_config.get("feature", "bass_energy")
    bass = feature_float(ctx.features, radius_feature)
    rms = feature_float(ctx.features, "rms")
    treble = feature_float(ctx.features, "treble_energy")
    beat = bool(ctx.features.get("beat"))
    center_x = ctx.width // 2
    center_y = ctx.height // 2
    configured_base = float(radius_config.get("base", 90))
    configured_scale = float(radius_config.get("scale", 120))
    design_scale = min(ctx.width, ctx.height) / 720
    base_radius = configured_base * design_scale
    radius = int(base_radius + configured_scale * design_scale * bass + rms * base_radius * 0.25)
    wobble = int(math.sin(ctx.time_seconds * math.tau * 1.3) * (4 + treble * 12))

    accent = blend_color(ctx.palette_accent, ctx.palette_beat, bass * 0.35)
    core = blend_color(ctx.palette_base, ctx.palette_accent, rms)

    for index in range(5, 0, -1):
        ring_radius = radius + index * int(7 + rms * 10)
        color = blend_color((25, 65, 95), accent, index / 5)
        ctx.draw.ellipse(
            (
                center_x - ring_radius,
                center_y - ring_radius,
                center_x + ring_radius,
                center_y + ring_radius,
            ),
            outline=color,
            width=max(1, index // 2),
        )

    if beat:
        shock_radius = radius + int(min(ctx.width, ctx.height) * 0.14)
        ctx.draw.ellipse(
            (
                center_x - shock_radius,
                center_y - shock_radius,
                center_x + shock_radius,
                center_y + shock_radius,
            ),
            outline=ctx.palette_beat,
            width=max(2, min(ctx.width, ctx.height) // 180),
        )

    horizontal_radius = max(2, radius + abs(wobble))
    vertical_radius = max(2, radius)
    ctx.draw.ellipse(
        (
            center_x - horizontal_radius,
            center_y - vertical_radius,
            center_x + horizontal_radius,
            center_y + vertical_radius,
        ),
        fill=core,
        outline=ctx.palette_beat,
        width=max(2, min(ctx.width, ctx.height) // 220),
    )
    highlight_radius = max(2, int(radius * 0.34))
    ctx.draw.ellipse(
        (
            center_x - highlight_radius,
            center_y - highlight_radius,
            center_x + highlight_radius,
            center_y + highlight_radius,
        ),
        fill=blend_color(core, ctx.palette_beat, 0.35),
    )
