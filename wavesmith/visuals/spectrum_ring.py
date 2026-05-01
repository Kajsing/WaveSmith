"""Spectrum ring visual module."""

import math

from wavesmith.visuals.base import FrameContext, blend_color, feature_float, feature_vector


def draw_spectrum_ring(ctx: FrameContext) -> None:
    """Draw a circular spectrum visualizer."""
    spectrum = feature_vector(ctx.features, "spectrum")
    if not spectrum:
        return

    rms = feature_float(ctx.features, "rms")
    treble = feature_float(ctx.features, "treble_energy")
    center_x = ctx.width / 2
    center_y = ctx.height / 2
    base_radius = min(ctx.width, ctx.height) * (0.24 + rms * 0.04)
    max_bar = min(ctx.width, ctx.height) * (0.12 + treble * 0.08)
    width = max(1, min(ctx.width, ctx.height) // 260)

    for index, value in enumerate(spectrum):
        angle = (index / len(spectrum)) * math.tau - math.pi / 2
        mirrored_value = (value + spectrum[-index - 1]) / 2
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
        color = blend_color((75, 220, 255), (255, 85, 210), mirrored_value)
        ctx.draw.line((*start, *end), fill=color, width=width)
