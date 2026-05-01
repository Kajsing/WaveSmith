"""Waveform ribbon visual module."""

import math

from wavesmith.visuals.base import FrameContext, blend_color, feature_float, feature_vector


def draw_waveform_ribbon(ctx: FrameContext) -> None:
    """Draw a lower waveform ribbon from preview samples."""
    waveform = feature_vector(ctx.features, "waveform_preview")
    if len(waveform) < 2:
        return

    rms = feature_float(ctx.features, "rms")
    bass = feature_float(ctx.features, "bass_energy")
    baseline = int(ctx.height * 0.78)
    amplitude = max(12, int(ctx.height * (0.06 + rms * 0.08)))
    phase = ctx.time_seconds * math.tau * (0.18 + bass * 0.25)
    color = blend_color((255, 235, 170), (80, 220, 255), rms)
    shadow = blend_color((55, 25, 80), (35, 100, 130), bass)

    points: list[tuple[int, int]] = []
    for index, value in enumerate(waveform):
        x = round(index / max(1, len(waveform) - 1) * ctx.width)
        centered = (value - 0.5) * 2.0
        sway = math.sin(index * 0.55 + phase) * amplitude * 0.28
        y = round(baseline + centered * amplitude + sway)
        points.append((x, y))

    ctx.draw.line(points, fill=shadow, width=max(5, ctx.height // 80))
    ctx.draw.line(points, fill=color, width=max(2, ctx.height // 150))
