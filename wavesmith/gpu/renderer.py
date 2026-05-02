"""ModernGL fullscreen shader renderer."""

import math
from collections.abc import Iterator
from importlib.resources import files
from typing import Any

from PIL import Image, ImageDraw

from wavesmith.gpu.capabilities import GPU_INSTALL_HINT, create_standalone_context
from wavesmith.lyrics import LyricCue, active_lyric_text
from wavesmith.presets.schema import PresetConfig, PresetModule
from wavesmith.render.options import RenderOptions
from wavesmith.timeline.model import Timeline
from wavesmith.visuals.base import FrameContext, feature_float, feature_vector
from wavesmith.visuals.text import draw_lyrics, draw_watermark

VERTEX_SHADER = """
#version 330
in vec2 in_pos;
out vec2 v_uv;

void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""


def generate_gpu_frames(
    *,
    options: RenderOptions,
    duration_seconds: float,
    timeline: Timeline,
    preset: PresetConfig,
    lyrics: list[LyricCue],
    watermark_text: str | None,
) -> Iterator[bytes]:
    """Yield RGB frame bytes from the experimental ModernGL shader path."""
    module = _gpu_shader_module(preset)
    shader_name = str(module.model_extra.get("shader", "bloom_field"))
    fragment_shader = _load_shader_source(shader_name)
    frame_count = max(1, math.ceil(duration_seconds * options.fps))

    try:
        ctx = create_standalone_context()
        program = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=fragment_shader)
        import struct

        import moderngl

        vertices = ctx.buffer(
            struct.pack(
                "8f",
                -1.0,
                -1.0,
                1.0,
                -1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
            )
        )
        vao = ctx.vertex_array(program, [(vertices, "2f", "in_pos")])
        texture = ctx.texture((options.width, options.height), components=3)
        framebuffer = ctx.framebuffer(color_attachments=[texture])
    except Exception as exc:
        raise RuntimeError(f"GPU shader setup failed: {exc}. {GPU_INSTALL_HINT}") from exc

    try:
        for frame_index in range(frame_count):
            progress = frame_index / max(1, frame_count - 1)
            time_seconds = frame_index / options.fps
            features = timeline.at(time_seconds)
            _set_uniforms(program, options, preset, features, time_seconds, progress)
            framebuffer.use()
            ctx.clear(0.0, 0.0, 0.0, 1.0)
            vao.render(mode=moderngl.TRIANGLE_STRIP, vertices=4)
            raw = framebuffer.read(components=3, alignment=1)
            image = Image.frombytes("RGB", (options.width, options.height), raw)
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            _draw_cpu_overlays(
                image,
                options,
                preset,
                features,
                time_seconds,
                progress,
                lyrics,
                watermark_text,
            )
            yield image.tobytes()
    finally:
        framebuffer.release()
        texture.release()
        vao.release()
        vertices.release()
        program.release()
        ctx.release()


def _gpu_shader_module(preset: PresetConfig) -> PresetModule:
    for module in preset.modules:
        if module.type == "shader_field" and module.model_extra.get("style") == "gpu_bloom":
            return module
    raise RuntimeError(
        f"Preset '{preset.name}' does not declare a shader_field module with style gpu_bloom."
    )


def _load_shader_source(shader_name: str) -> str:
    if shader_name != "bloom_field":
        raise RuntimeError(f"Unsupported GPU shader: {shader_name}")
    return (files("wavesmith.gpu.shaders") / "bloom_field.glsl").read_text(encoding="utf-8")


def _set_uniforms(
    program: Any,
    options: RenderOptions,
    preset: PresetConfig,
    features: dict[str, Any],
    time_seconds: float,
    progress: float,
) -> None:
    spectrum = feature_vector(features, "spectrum")[:32]
    spectrum = [*spectrum, *([0.0] * (32 - len(spectrum)))]
    uniforms: dict[str, Any] = {
        "u_resolution": (float(options.width), float(options.height)),
        "u_time": float(time_seconds),
        "u_progress": float(progress),
        "u_rms": feature_float(features, "rms"),
        "u_bass": feature_float(features, "bass_energy"),
        "u_mid": feature_float(features, "mid_energy"),
        "u_treble": feature_float(features, "treble_energy"),
        "u_beat": 1.0 if features.get("beat") else 0.0,
        "u_beat_decay": feature_float(features, "beat_decay"),
        "u_slow_pulse": feature_float(features, "slow_pulse"),
        "u_palette_base": _rgb01(preset.palette.base),
        "u_palette_accent": _rgb01(preset.palette.accent),
        "u_palette_beat": _rgb01(preset.palette.beat),
        "u_spectrum": spectrum,
    }
    for name, value in uniforms.items():
        if name in program:
            program[name].value = value


def _draw_cpu_overlays(
    image: Image.Image,
    options: RenderOptions,
    preset: PresetConfig,
    features: dict[str, Any],
    time_seconds: float,
    progress: float,
    lyrics: list[LyricCue],
    watermark_text: str | None,
) -> None:
    draw = ImageDraw.Draw(image)
    ctx = FrameContext(
        image=image,
        draw=draw,
        width=options.width,
        height=options.height,
        time_seconds=time_seconds,
        progress=progress,
        features=features,
        preset_name=preset.name,
        palette_base=preset.palette.base,
        palette_accent=preset.palette.accent,
        palette_beat=preset.palette.beat,
    )
    draw_lyrics(ctx, active_lyric_text(lyrics, time_seconds, options.lyrics_offset))
    draw_watermark(ctx, watermark_text)


def _rgb01(color: tuple[int, int, int]) -> tuple[float, float, float]:
    return tuple(channel / 255.0 for channel in color)
