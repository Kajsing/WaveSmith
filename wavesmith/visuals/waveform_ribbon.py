"""Waveform ribbon visual module."""

import math

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float, feature_vector


def draw_waveform_ribbon(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw a lower waveform ribbon from preview samples."""
    module_config = module.model_extra or {} if module else {}
    waveform = feature_vector(ctx.features, module_config.get("feature", "waveform_preview"))
    if len(waveform) < 2:
        return

    rms = feature_float(ctx.features, "rms")
    bass = feature_float(ctx.features, "bass_energy")
    position = module_config.get("position", "bottom")
    baseline_ratio = {"upper": 0.34, "lower": 0.72, "bottom": 0.78}.get(position, 0.78)
    baseline = int(ctx.height * baseline_ratio)
    configured_height = float(module_config.get("height", 160))
    amplitude = max(10, int((configured_height / 720) * ctx.height * (0.5 + rms)))
    phase = ctx.time_seconds * math.tau * (0.18 + bass * 0.25)
    color = blend_color(ctx.palette_beat, ctx.palette_accent, rms)
    shadow = blend_color(ctx.palette_base, ctx.palette_accent, bass * 0.4)

    points: list[tuple[int, int]] = []
    for index, value in enumerate(waveform):
        x = round(index / max(1, len(waveform) - 1) * ctx.width)
        centered = (value - 0.5) * 2.0
        sway = math.sin(index * 0.55 + phase) * amplitude * 0.28
        y = round(baseline + centered * amplitude + sway)
        points.append((x, y))

    ctx.draw.line(points, fill=shadow, width=max(5, ctx.height // 80))
    ctx.draw.line(points, fill=color, width=max(2, ctx.height // 150))
