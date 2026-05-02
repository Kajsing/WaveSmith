"""Render backend selection and CPU frame generation."""

import math
from collections.abc import Iterator
from typing import Protocol

from PIL import Image, ImageDraw

from wavesmith.lyrics import LyricCue, active_lyric_text
from wavesmith.presets.schema import PresetConfig, PresetModule
from wavesmith.render.options import RenderOptions
from wavesmith.timeline.model import Timeline
from wavesmith.visuals.background import draw_reactive_background
from wavesmith.visuals.base import FrameContext
from wavesmith.visuals.center_orb import draw_center_orb
from wavesmith.visuals.cinematic_backdrop import draw_cinematic_backdrop
from wavesmith.visuals.elemental_field import draw_elemental_field
from wavesmith.visuals.image_backdrop import draw_image_backdrop
from wavesmith.visuals.particles import draw_particles
from wavesmith.visuals.portal_ring import draw_portal_ring
from wavesmith.visuals.shader_field import draw_shader_field
from wavesmith.visuals.spectrum_ring import draw_spectrum_ring
from wavesmith.visuals.spectrum_wall import draw_spectrum_wall
from wavesmith.visuals.text import draw_lyrics, draw_watermark
from wavesmith.visuals.waveform_ribbon import draw_waveform_ribbon


class RenderBackendError(RuntimeError):
    """Raised when a selected render backend cannot render."""


class RenderBackend(Protocol):
    """Frame generator backend contract."""

    name: str

    def generate_frames(
        self,
        *,
        options: RenderOptions,
        duration_seconds: float,
        timeline: Timeline,
        preset: PresetConfig,
        lyrics: list[LyricCue],
        watermark_text: str | None,
    ) -> Iterator[bytes]:
        """Yield RGB frame bytes."""


class CpuRenderBackend:
    """Reference Pillow-based renderer."""

    name = "cpu"

    def generate_frames(
        self,
        *,
        options: RenderOptions,
        duration_seconds: float,
        timeline: Timeline,
        preset: PresetConfig,
        lyrics: list[LyricCue],
        watermark_text: str | None,
    ) -> Iterator[bytes]:
        """Yield RGB frames driven by timeline features."""
        frame_count = max(1, math.ceil(duration_seconds * options.fps))
        width = options.width
        height = options.height

        for frame_index in range(frame_count):
            progress = frame_index / max(1, frame_count - 1)
            time_seconds = frame_index / options.fps
            features = timeline.at(time_seconds)
            image = Image.new("RGB", (width, height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            ctx = FrameContext(
                image=image,
                draw=draw,
                width=width,
                height=height,
                time_seconds=time_seconds,
                progress=progress,
                features=features,
                preset_name=preset.name,
                palette_base=preset.palette.base,
                palette_accent=preset.palette.accent,
                palette_beat=preset.palette.beat,
            )

            draw_reactive_background(ctx)
            for module in preset.modules:
                _draw_module(ctx, module)
            draw_lyrics(ctx, active_lyric_text(lyrics, time_seconds, options.lyrics_offset))
            draw_watermark(ctx, watermark_text)

            yield image.tobytes()


class GpuRenderBackend:
    """Placeholder for the future local GPU renderer."""

    name = "gpu"

    def generate_frames(
        self,
        *,
        options: RenderOptions,
        duration_seconds: float,
        timeline: Timeline,
        preset: PresetConfig,
        lyrics: list[LyricCue],
        watermark_text: str | None,
    ) -> Iterator[bytes]:
        """Yield frames from the experimental ModernGL backend."""
        try:
            from wavesmith.gpu.renderer import generate_gpu_frames

            yield from generate_gpu_frames(
                options=options,
                duration_seconds=duration_seconds,
                timeline=timeline,
                preset=preset,
                lyrics=lyrics,
                watermark_text=watermark_text,
            )
        except Exception as exc:
            raise RenderBackendError(str(exc)) from exc


def get_render_backend(name: str) -> RenderBackend:
    """Return a render backend by name."""
    if name == "cpu":
        return CpuRenderBackend()
    if name == "gpu":
        return GpuRenderBackend()
    raise RenderBackendError(f"Unknown render backend: {name}")


def _draw_module(ctx: FrameContext, module: PresetModule) -> None:
    if module.type == "center_orb":
        draw_center_orb(ctx, module)
    elif module.type == "spectrum_ring":
        draw_spectrum_ring(ctx, module)
    elif module.type == "waveform_ribbon":
        draw_waveform_ribbon(ctx, module)
    elif module.type == "particles":
        draw_particles(ctx, module)
    elif module.type == "shader_field":
        draw_shader_field(ctx, module)
    elif module.type == "elemental_field":
        draw_elemental_field(ctx, module)
    elif module.type == "portal_ring":
        draw_portal_ring(ctx, module)
    elif module.type == "spectrum_wall":
        draw_spectrum_wall(ctx, module)
    elif module.type == "cinematic_backdrop":
        draw_cinematic_backdrop(ctx, module)
    elif module.type == "image_backdrop":
        draw_image_backdrop(ctx, module)
