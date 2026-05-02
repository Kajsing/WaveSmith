from pathlib import Path
from types import SimpleNamespace

import pytest

from wavesmith.audio.features import AudioAnalysis, TimeSeries
from wavesmith.presets.loader import load_preset
from wavesmith.render.backends import (
    CpuRenderBackend,
    GpuRenderBackend,
    RenderBackendError,
    get_render_backend,
)
from wavesmith.render.options import RenderOptions
from wavesmith.timeline.model import Timeline


def test_get_render_backend_returns_cpu() -> None:
    backend = get_render_backend("cpu")

    assert isinstance(backend, CpuRenderBackend)
    assert backend.name == "cpu"


def test_get_render_backend_returns_gpu() -> None:
    backend = get_render_backend("gpu")

    assert isinstance(backend, GpuRenderBackend)
    assert backend.name == "gpu"


def test_gpu_backend_reports_missing_dependency(monkeypatch) -> None:
    def fake_generate_gpu_frames(**kwargs):
        raise RuntimeError(
            "ModernGL is not installed. Install GPU support with: pip install -e .[gpu]"
        )

    monkeypatch.setattr(
        "wavesmith.gpu.renderer.generate_gpu_frames",
        fake_generate_gpu_frames,
    )
    backend = get_render_backend("gpu")

    with pytest.raises(RenderBackendError, match=r"pip install -e .\[gpu\]"):
        next(
            backend.generate_frames(
                options=None,  # type: ignore[arg-type]
                duration_seconds=1.0,
                timeline=None,  # type: ignore[arg-type]
                preset=None,  # type: ignore[arg-type]
                lyrics=[],
                watermark_text=None,
            )
        )


def test_gpu_uniforms_prepare_audio_features() -> None:
    from wavesmith.gpu.renderer import _set_uniforms

    program = {
        "u_resolution": SimpleNamespace(value=None),
        "u_time": SimpleNamespace(value=None),
        "u_rms": SimpleNamespace(value=None),
        "u_bass": SimpleNamespace(value=None),
        "u_spectrum": SimpleNamespace(value=None),
        "u_palette_base": SimpleNamespace(value=None),
    }
    options = RenderOptions(
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        preset="gpu_shader_bloom",
        width=64,
        height=48,
        fps=2,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
    )
    features = {
        "rms": 0.4,
        "bass_energy": 0.6,
        "spectrum": [0.1, 0.2, 0.3],
    }

    _set_uniforms(program, options, load_preset("gpu_shader_bloom"), features, 1.25, 0.5)

    assert program["u_resolution"].value == (64.0, 48.0)
    assert program["u_time"].value == 1.25
    assert program["u_rms"].value == 0.4
    assert program["u_bass"].value == 0.6
    assert len(program["u_spectrum"].value) == 32
    assert program["u_palette_base"].value == (46 / 255, 1.0, 172 / 255)


def test_gpu_backend_smoke_renders_tiny_frames() -> None:
    pytest.importorskip("moderngl")
    options = RenderOptions(
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        preset="gpu_shader_bloom",
        width=32,
        height=24,
        fps=2,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
    )
    scalar = TimeSeries(times=[0.0, 1.0], values=[0.2, 0.9])
    vector = TimeSeries(
        times=[0.0, 1.0],
        values=[[0.1] * 32, [0.8] * 32],
    )
    analysis = AudioAnalysis(
        duration_seconds=1.0,
        sample_rate=22_050,
        tempo_bpm=120.0,
        beats=[0.0],
        onsets=[],
        rms=scalar,
        bass_energy=scalar,
        mid_energy=scalar,
        treble_energy=scalar,
        spectrum=vector,
        waveform_preview=vector,
    )

    try:
        frame = next(
            get_render_backend("gpu").generate_frames(
                options=options,
                duration_seconds=0.5,
                timeline=Timeline(analysis),
                preset=load_preset("gpu_shader_bloom"),
                lyrics=[],
                watermark_text=None,
            )
        )
    except RenderBackendError as exc:
        pytest.skip(f"ModernGL context unavailable: {exc}")

    assert len(frame) == 32 * 24 * 3
    assert any(byte != 0 for byte in frame)
