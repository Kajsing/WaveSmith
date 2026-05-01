"""Background visual primitives."""

import math

from wavesmith.visuals.base import FrameContext, blend_color, feature_float


def draw_reactive_background(ctx: FrameContext) -> None:
    """Draw a dark reactive background with subtle scan-grid motion."""
    rms = feature_float(ctx.features, "rms")
    treble = feature_float(ctx.features, "treble_energy")
    beat = 1.0 if ctx.features.get("beat") else 0.0
    top = blend_color((5, 4, 16), (20, 8, 35), rms)
    bottom = blend_color((1, 10, 16), (5, 34, 48), treble)

    for y in range(ctx.height):
        amount = y / max(1, ctx.height - 1)
        color = blend_color(top, bottom, amount)
        if beat:
            color = blend_color(color, (55, 70, 90), 0.2)
        ctx.draw.line((0, y, ctx.width, y), fill=color)

    spacing = max(28, min(ctx.width, ctx.height) // 13)
    offset = int((ctx.progress * spacing * 2) % spacing)
    grid_color = blend_color((16, 22, 36), (35, 70, 90), treble)
    for x in range(-spacing + offset, ctx.width, spacing):
        ctx.draw.line((x, 0, x, ctx.height), fill=grid_color)
    wave_offset = int(math.sin(ctx.time_seconds * math.tau * 0.3) * spacing * 0.25)
    for y in range(-spacing + offset + wave_offset, ctx.height, spacing):
        ctx.draw.line((0, y, ctx.width, y), fill=grid_color)
